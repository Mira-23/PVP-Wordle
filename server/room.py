from pathlib import Path
import random
from typing import List
class Room:
    def __init__(self, client1, client2):
        self.mode = 5
        self.rounds = 5
        self.chosen_list, self.longer_list = self.mode_choice()
        self.guesses = self.generate_guesses(self.chosen_list)
        self.round_indexes = {client1:0,client2: 0}
        self.finished = False
        self.is_infinite = False
        self.word_lost = False

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

    #change
    def verify_answer(self,client,attempt):
        if self.finished:
            return False
        
        index = self.round_indexes[client]
        answer = self.guesses[index]
        correct = answer == attempt

        if correct:
            self.round_indexes[client]+=1

        return correct