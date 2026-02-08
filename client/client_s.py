import os
from pathlib import Path
import socket
import sys
import threading
import json
from typing import List, Dict, Any, Optional
from protocols import Protocols

class Client:
    def __init__(self, host: str | None = "localhost", port: int | None = 55555) -> None:
        # manual server overdrive for hosting with another service
        if host is None and port is None:
            host = input("Enter server IP address: ")
            port = int(input("Enter port: "))
        self.server: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.server.connect((host, port))

        self.nickname: str = ""

        self.mode: int = 5

        self.started: bool = False
        self.closed: bool = False

        self.guesses: List[List[str]] = []
        self.current_round_index: int = 0

        self.opponent_name: str = ""

        self.winner: Optional[Any] = None

        self.points: int = 0
        self.opponent_points: int = 0

        self.new_round: bool = False
        self.opponent_left: bool = False

        self.warning : str = ""

        self.max_guesses: int = 0
        self.longer_list: List[str] = []

        self.leaderboard_data: List[Dict[str, Any]] = []

    # starts thread on receive
    def start(self) -> None:
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    # send data
    def send(self, request: str, message: Any) -> None:
        data: Dict[str, Any] = {"type": request, "data": message}
        message_str: str = json.dumps(data) + "\n"
        self.server.send(message_str.encode("ascii"))

    # recieves data in json, watches out for newlines
    def receive(self) -> None:
        buffer: str = ""
        while not self.closed:
            try:
                buffer += self.server.recv(1024).decode("ascii")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip() == "":
                        continue
                    message: Dict[str, Any] = json.loads(line)
                    self.handle_response(message)
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                break

    # close self
    def close(self) -> None:
        self.closed = True
        self.server.close()

    # based on the chosen word length fetch the list for word verification
    def mode_choice(self) -> List[str]:
        if getattr(sys, 'frozen', False):
            # running as compiled executable
            base_dir_str: str = os.path.dirname(sys.executable)
            base_dir: Path = Path(base_dir_str)
        else:
            # running as script
            base_dir : Path = Path(__file__).resolve().parent
        
        word_lists_dir : Path = Path(base_dir) / "word lists"
        
        if not word_lists_dir.exists():
            word_lists_dir = Path(base_dir) / ".." / "word lists"

        base_dir: Path = Path(__file__).resolve().parent
        word_lists_dir: Path = base_dir / "word lists"

        with open(
            word_lists_dir / "longerfiveletterwords.txt", 'r'
            , encoding='utf-8'
        ) as file:
            longer_fives: List[str] = file.read().splitlines()
        with open(
            word_lists_dir / "longersixletterwords.txt", 'r'
            , encoding='utf-8'
        ) as file:
            longer_sixes: List[str] = file.read().splitlines()
        with open(
            word_lists_dir / "longersevenletterwords.txt", 'r'
            , encoding='utf-8'
        ) as file:
            longer_sevens: List[str] = file.read().splitlines()

        longer_list: List[str] = []
        match self.mode:
            case 5:
                longer_list = longer_fives
            case 6:
                longer_list = longer_sixes
            case 7:
                longer_list = longer_sevens
            case _:
                pass

        return longer_list

    # checks if submitted word is in fact a real word (zzzzz - isnt)
    def is_word_valid(self, word: str) -> bool:
        return word.upper() in self.longer_list

    # handles protocol responses
    def handle_response(self, response: Dict[str, Any]) -> None:
        r_type: Optional[str] = response.get("type")
        data: Any = response.get("data")

        if r_type == Protocols.Response.START:
            self.started = True
        # receive words to be guessed from server
        elif r_type == Protocols.Response.GUESSES:
            self.guesses = data
        # receive settings (word lenght and max attempts)
        elif r_type == Protocols.Response.SETTINGS:
            self.mode = data["mode"]
            self.max_guesses = data["max_guesses"]
            self.longer_list = self.mode_choice()
        # set new round variables
        elif r_type == Protocols.Response.NEW_ROUND:
            self.current_round_index += 1
            self.new_round = True
        # receive opponent data (name and points)
        elif r_type == Protocols.Response.OPPONENT:
            self.opponent_name = data.get("name")
            self.opponent_points = data.get("points", 0)
        # updates points for players
        elif r_type == Protocols.Response.POINTS_UPDATE:
            self.points = data.get("your_points", 0)
            self.opponent_points = data.get("opponent_points", 0)
        # recieves winner
        elif r_type == Protocols.Response.WINNER:
            self.winner = data
        # receives leaderboard data
        elif r_type == Protocols.Response.LEADERBOARD:
            self.leaderboard_data = data
        # warning from server
        elif r_type == Protocols.Response.INVALID_REQUEST:
            self.warning = data
        # opponent has left
        elif r_type == Protocols.Response.OPPONENT_LEFT:
            self.opponent_left = True
