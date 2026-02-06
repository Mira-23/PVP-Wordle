from pathlib import Path
import socket
import threading
import json
from typing import List
from protocols import Protocols

class Client:
    def __init__(self,host="127.0.0.1",port=55555):
        self.nickname = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((host,port))

        self.mode = 5

        self.closed = False
        self.started = False

        self.guesses = []
        self.current_round_index=0

        self.opponent_question_index=0
        self.opponent_name = None

        self.winner = None
        self.points = 0
        self.opponent_points = 0

        self.new_round = False
        self.opponent_left = False

    def start(self):
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    def send(self, request, message):
        data = {"type": request, "data": message}
        message_str = json.dumps(data) + "\n"   # <- add newline
        self.server.send(message_str.encode("ascii"))

    def receive(self):
        buffer = ""
        while not self.closed:
            try:
                buffer += self.server.recv(1024).decode("ascii")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip() == "":
                        continue
                    message = json.loads(line)
                    self.handle_response(message)
            except:
                break

    def close(self):
        self.closed = True
        self.server.close()

    def mode_choice(self) -> List[str]:
        BASE_DIR = Path(__file__).resolve().parent

        with open(BASE_DIR / "word lists" / "longerfiveletterwords.txt", 'r') as file:
            longer_fives = file.read().splitlines()
        with open(BASE_DIR / "word lists" / "longersixletterwords.txt", 'r') as file:
            longer_sixes = file.read().splitlines()
        with open(BASE_DIR / "word lists" / "longersevenletterwords.txt", 'r') as file:
            longer_sevens = file.read().splitlines()

        longer_list = []
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

    def is_word_valid(self,word: str) -> bool:
        if word.upper() in self.longer_list:
            return True
        else:
            return False

    def handle_response(self,response):
        r_type = response.get("type")
        data = response.get("data")

        if r_type == Protocols.Response.GUESSES:
            self.guesses = data
        elif r_type == Protocols.Response.SETTINGS:
            self.mode = data["mode"]
            self.max_guesses = data["max_guesses"]
            self.longer_list = self.mode_choice()
        elif r_type == Protocols.Response.OPPONENT:
            # Handle opponent data which now includes points
            if isinstance(data, dict):
                self.opponent_name = data.get("name")
                self.opponent_points = data.get("points", 0)
            else:
                # Backward compatibility - data is just name string
                self.opponent_name = data
                self.opponent_points = 0
        elif r_type == Protocols.Response.OPPONENT_ADVANCE:
            pass
        elif r_type == Protocols.Response.START:
            print("Received START from server")
            self.started = True
        elif r_type == Protocols.Response.WINNER:
            self.winner = data
        elif r_type == Protocols.Response.NEW_ROUND:
            self.current_round_index += 1
            self.new_round = True
        elif r_type == Protocols.Response.POINTS_UPDATE:  # Add this handler
            self.points = data.get("your_points", 0)
            self.opponent_points = data.get("opponent_points", 0)
        elif r_type == Protocols.Response.OPPONENT_LEFT:
            self.opponent_left = True