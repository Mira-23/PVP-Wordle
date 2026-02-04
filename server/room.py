from pathlib import Path
import random
from typing import List
class Room:
    def __init__(self, client1, client2):
        self.mode = 5
        self.rounds = 2
        self.chosen_list, self.longer_list = self.mode_choice()
        self.guesses = self.generate_guesses(self.chosen_list)
        self.round_indexes = {client1:0,client2: 0}
        self.finished = False
        self.is_infinite = False
        self.word_lost = False
        self.points = {client1: 0, client2: 0}
        self.finished_players = set()
        self.all_finished_players = set()

    #change
    def generate_guesses(self, chosen_list: List[str]) -> List[str]:
        guesses = []
        for i in range(self.rounds):
            random_word = chosen_list[random.randint(0, len(chosen_list)-1)]
            letters = list(random_word)
            guesses.append(letters)
        return guesses
    
    def mode_choice(self) -> tuple[List[str],List[str]]:
        BASE_DIR = Path(__file__).resolve().parent.parent

        with open(BASE_DIR / "client" / "word lists" / "fiveletterwords.txt", 'r') as file:
            five_letter_words = file.read().splitlines()
        with open(BASE_DIR / "client" / "word lists" / "longerfiveletterwords.txt", 'r') as file:
            longer_fives = file.read().splitlines()
        with open(BASE_DIR / "client" / "word lists" / "sixletterwords.txt", 'r') as file:
            six_letter_words = file.read().splitlines()
        with open(BASE_DIR / "client" / "word lists" / "longersixletterwords.txt", 'r') as file:
            longer_sixes = file.read().splitlines()
        with open(BASE_DIR / "client" / "word lists" / "sevenletterwords.txt", 'r') as file:
            seven_letter_words = file.read().splitlines()
        with open(BASE_DIR / "client" / "word lists" / "longersevenletterwords.txt", 'r') as file:
            longer_sevens = file.read().splitlines()

        chosen_list = []
        longer_list = []
        match self.mode:
            case 5:
                chosen_list = five_letter_words
                longer_list = longer_fives
            case 6:
                chosen_list = six_letter_words
                longer_list = longer_sixes
            case 7:
                chosen_list = seven_letter_words
                longer_list = longer_sevens
            case _:
                pass
            
        return chosen_list, longer_list

    def calculate_points(self, guesses_used: int, seconds: float) -> int:
        max_guesses = 6  # Wordle rows

        # Guess score
        guess_score = max(0, (max_guesses - guesses_used) * 10)

        # Time bonus (steps of 30 seconds)
        bonus_steps = max(0, 5 - int(seconds // 30))
        time_bonus = bonus_steps * 10

        return guess_score + time_bonus

    #change
    def verify_answer(self, client, data):
        # if isinstance(data, dict):
        #     attempt = data['attempt']
        #     client_finished_round = data.get('is_final', False)
        # else: 
        #     attempt = data
        #     client_finished_round = False
        # print(data)
        # print(client_finished_round)  

        guesses_used = data.get("guesses_used", 6)
        seconds_taken = data.get("seconds", 999)

        points = self.calculate_points(guesses_used, seconds_taken)

        self.points[client] += points

        self.round_indexes[client] += 1
        self.finished_players.add(client)
    
    def round_finished(self):
        print(len(self.finished_players))
        if self.rounds == 0:
            self.finished = True
        else:
            self.rounds-=1
        return len(self.finished_players) == 2
        
    
    def start_new_round(self):
        self.finished_players.clear()

