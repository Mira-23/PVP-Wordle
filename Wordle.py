#import pygame
import random
from typing import List

def startup() -> List[str]:
    with open('word lists/fiveletterwords.txt', 'r') as file:
        five_letter_words = file.read().splitlines()
    with open('word lists/sixletterwords.txt', 'r') as file:
        six_letter_words = file.read().splitlines()
    with open('word lists/sevenletterwords.txt', 'r') as file:
        seven_letter_words = file.read().splitlines()

    mode = 5 # int(input())

    chosen_list = []
    match mode:
        case 5:
            chosen_list = five_letter_words
        case 6:
            chosen_list = six_letter_words
        case 7:
            chosen_list = seven_letter_words
        case _:
            pass
    
    return chosen_list

def guessing(chosen_list: List[str]):
    mode = len(chosen_list[0])
    #number_of_guesses = manual choice (input) - (2,mode+1)
    random_word = "ABOTB" # chosen_list[random.randint(0, len(chosen_list)-1)]
    letters = list(random_word)
    count = 0

    def is_word_valid(word: str) -> bool:
        if word:
            return True
        else:
            return False


    while count!=mode+1:

        guess = (input()).upper()
        guess_letters = list(guess)
        if not is_word_valid(guess):
            print("not a word my guy")
            continue

        #logic
        if guess == random_word:
            print("You won!")
            return
        else:
            #make a list for alphabet - color corrects in green, guesses in yellow, wrongs in black
            to_be_guessed = list(letters)

            for index, letter in enumerate(letters):
                if letter == guess_letters[index]:
                    to_be_guessed.remove(guess_letters[index])
                    print("g", end="")
                    
                elif guess_letters[index] in to_be_guessed:
                    to_be_guessed.remove(guess_letters[index])
                    print("y", end="")
                    
                else:
                    print("b", end="")
            print("\n")
        count+=1
        pass

    print(f"damn, you lost! the word was {random_word}")

chosen_list = startup()

guessing(chosen_list)
# pygame.init()

# screen = pygame.display.set_mode((640,640))
# clock = pygame.time.Clock()
# delta_time = 0.1

# running = True
# while running:
#     #white background
#     screen.fill((255,255,255))

#     #closing the window
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False

#     #display stuff on the window
#     pygame.display.flip()

#     #time handling for framerate
#     delta_time = clock.tick(60) / 1000
#     delta_time = max(0.001, min(0.1,delta_time))

# pygame.quit()