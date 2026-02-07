from pathlib import Path
import random
from typing import List, Dict, Set, Any, Optional

class Room:
    def __init__(self, host: Any, settings: Dict[str, Any]) -> None:
        self.host: Any = host
        self.guest: Optional[Any] = None   # second player later

        self.mode: int = settings["mode"]
        self.rounds: int = settings["rounds"]
        self.is_infinite: bool = settings["infinite"]
        self.max_guesses: int = settings["max_guesses"]

        self.chosen_list: List[str] = self.mode_choice()
        self.guesses: List[List[str]] = self.generate_guesses(
            self.chosen_list
        )

        self.round_indexes: Dict[Any, int] = {host: 0}
        self.points: Dict[Any, int] = {host: 0}

        self.finished_players: Set[Any] = set()
        self.failed_players: Set[Any] = set()

    # adds player to room unless full
    def add_player(self, client: Any) -> bool:
        if self.guest is not None:
            return False

        self.guest = client
        self.round_indexes[client] = 0
        self.points[client] = 0
        return True

    # generates random words to be guessed based on the amount of rounds
    def generate_guesses(self, chosen_list: List[str]) -> List[List[str]]:
        return [
            list(chosen_list[random.randint(0, len(chosen_list) - 1)])
            for _ in range(self.rounds)
        ]

    # loads a set of words based on the chosen mode for the random word
    # generation
    def mode_choice(self) -> List[str]:
        base_dir: Path = Path(__file__).resolve().parent.parent
        word_lists_dir = base_dir / "client" / "word lists"

        with open(
            word_lists_dir / "fiveletterwords.txt", 'r', encoding='utf-8'
            ) as file:
            five_letter_words: List[str] = file.read().splitlines()
        with open(
            word_lists_dir / "sixletterwords.txt", 'r', encoding='utf-8'
            ) as file:
            six_letter_words: List[str] = file.read().splitlines()
        with open(
            word_lists_dir / "sevenletterwords.txt", 'r', encoding='utf-8'
            ) as file:
            seven_letter_words: List[str] = file.read().splitlines()

        chosen_list: List[str] = []
        match self.mode:
            case 5:
                chosen_list = five_letter_words
            case 6:
                chosen_list = six_letter_words
            case 7:
                chosen_list = seven_letter_words
            case _:
                pass

        return chosen_list

    # calculates points based on the amount of guesses and time taken
    # max guesses - player guesses)*10 + extra points (50 for 30 seconds,
    # 40 for 1 minute... etc)
    def calculate_points(self, guesses_used: int, seconds: float) -> int:
        guess_score: int = max(0, (self.max_guesses - guesses_used) * 10)

        bonus_steps: int = max(0, 5 - int(seconds // 30))
        time_bonus: int = bonus_steps * 10

        if guess_score == 0:
            time_bonus = 0

        return guess_score + time_bonus

    # handles a finished player based on whether the mode is infinite or not
    def client_finished(self, client: Any, data: Dict[str, Any]) -> None:
        guesses_used: int = data.get("guesses_used", self.max_guesses)
        seconds_taken: float = data.get("seconds", 999)
        success: bool = data.get("success", False)

        points: int = self.calculate_points(guesses_used, seconds_taken)
        self.points[client] += points

        if success:
            self.round_indexes[client] += 1
        else:
            self.failed_players.add(client)

        self.finished_players.add(client)
