import pygame
import random
from typing import List

def mode_choice(mode : int) -> List[str]:
    with open('word lists/fiveletterwords.txt', 'r') as file:
        five_letter_words = file.read().splitlines()
    with open('word lists/sixletterwords.txt', 'r') as file:
        six_letter_words = file.read().splitlines()
    with open('word lists/sevenletterwords.txt', 'r') as file:
        seven_letter_words = file.read().splitlines()

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

def number_of_guesses() -> int:
    return 5

def is_word_valid(word: str, chosen_list : List[str]) -> bool:
    if word.upper() in chosen_list:
        return True
    else:
        return False

def random_word(chosen_list: List[str]) -> List[str]:
    random_word = chosen_list[random.randint(0, len(chosen_list)-1)]
    letters = list(random_word)
    return letters

def guessing(guess_letters: List[str], word : str, chosen_list: List[str]) -> None:
    guess = ''.join(guess_letters).upper()
    guess_letters = list(guess)
    letters = list(word.upper())

    if not is_word_valid(guess, chosen_list):
        # reset word typing and make a popup that no such word exists
        raise ValueError

    #logic
    if guess == random_word:
        print('You won!')
        return
    else:
        #make a list for alphabet - color corrects in green, guesses in yellow, wrongs in black
        to_be_guessed = list(letters)

        for index, letter in enumerate(letters):
            if letter == guess_letters[index]:
                to_be_guessed.remove(guess_letters[index])
                print('g', end='')
                    
            elif guess_letters[index] in to_be_guessed:
                to_be_guessed.remove(guess_letters[index])
                print('y', end='')
                    
            else:
                print('b', end='')
        print("\n")

pygame.init()

pygame.font.init() 
my_font = pygame.font.SysFont('Arial', 30)

screen = pygame.display.set_mode((640,640))
clock = pygame.time.Clock()
delta_time = 0.1

#this needs to be changed during runtime
amount_of_guesses = number_of_guesses()
chosen_list = mode_choice(5)
chosen_word = random_word(chosen_list)

#change list length depending on number of guesses
guess_list = [[],[],[],[],[],[]]
word_number = 0

running = True

pygame.display.set_caption('PVP Wordle')
while running:
    #closing the window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            #this is horrible, redo
            if event.key == pygame.K_BACKSPACE:
                guess_list[word_number] = guess_list[word_number][:-1]
            elif word_number <= amount_of_guesses and event.key == pygame.K_RETURN and len(guess_list[word_number]) == 5:
                try:
                    guessing(guess_list[word_number],''.join(chosen_word),chosen_list)
                    word_number+=1
                except ValueError:
                    guess_list[word_number] = []
            elif word_number <= amount_of_guesses and event.key != pygame.K_RETURN and len(guess_list[word_number])<5:
                guess_list[word_number].append(event.unicode)

    #white background
    screen.fill((255,255,255))

    text_surface = my_font.render("\n".join(" ".join(str(letter) for letter in word) for word in guess_list), False, (0, 0, 0))

    screen.blit(text_surface, (250,100))

    #display stuff on the window
    pygame.display.flip()

    #time handling for framerate
    delta_time = clock.tick(60) / 1000
    delta_time = max(0.001, min(0.1,delta_time))

pygame.quit()