from pathlib import Path
import random
from typing import List
class Room:
    def __init__(self, client1, client2):
        self.mode = 5
        self.rounds = 5
        self.max_guesses = self.mode + 1 # change

        self.chosen_list = self.mode_choice()
        self.guesses = self.generate_guesses(self.chosen_list)

        self.round_indexes = {client1:0,client2: 0}

        self.finished = False
        self.is_infinite = False

        self.points = {client1: 0, client2: 0}

        self.finished_players = set()
        self.all_finished_players = set()

    # generates random words to be guessed based on the amount of rounds
    def generate_guesses(self, chosen_list: List[str]) -> List[str]:
        guesses = []
        for i in range(self.rounds):
            random_word = chosen_list[random.randint(0, len(chosen_list)-1)]
            letters = list(random_word)
            guesses.append(letters)
        return guesses
    
    # loads a set of words based on the chosen mode for the random word generation
    def mode_choice(self) -> List[str]:
        BASE_DIR = Path(__file__).resolve().parent.parent

        with open(BASE_DIR / "client" / "word lists" / "fiveletterwords.txt", 'r') as file:
            five_letter_words = file.read().splitlines()
        with open(BASE_DIR / "client" / "word lists" / "sixletterwords.txt", 'r') as file:
            six_letter_words = file.read().splitlines()
        with open(BASE_DIR / "client" / "word lists" / "sevenletterwords.txt", 'r') as file:
            seven_letter_words = file.read().splitlines()

        chosen_list = []
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
    # max guesses - player guesses)*10 + extra points (50 for 30 seconds, 40 for 1 minute... etc)
    def calculate_points(self, guesses_used: int, seconds: float) -> int:
        guess_score = max(0, (self.max_guesses - guesses_used) * 10)

        bonus_steps = max(0, 5 - int(seconds // 30))
        time_bonus = bonus_steps * 10

        return guess_score + time_bonus

    # triggered when a player finishes a round, calculates points and prepares for new round
    def client_finished(self, client, data):
        guesses_used = data.get("guesses_used", self.max_guesses)
        seconds_taken = data.get("seconds", 999)

        points = self.calculate_points(guesses_used, seconds_taken)

        self.points[client] += points

        self.round_indexes[client] += 1
        self.finished_players.add(client)
    
    # checks if room is finished, decreases rounds left if it isnt
    def round_finished(self):
        if self.rounds == 0:
            self.finished = True
        else:
            self.rounds-=1
        return len(self.finished_players) == 2
    
    #clears finished players from list
    def start_new_round(self):
        self.finished_players.clear()