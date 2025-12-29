from enum import Enum
import pygame
import random
from typing import List

def mode_choice(mode : int) -> tuple[List[str],List[str]]:
    with open('word lists/fiveletterwords.txt', 'r') as file:
        five_letter_words = file.read().splitlines()
    with open('word lists/longerfiveletterwords.txt', 'r') as file:
        longer_fives = file.read().splitlines()
    with open('word lists/sixletterwords.txt', 'r') as file:
        six_letter_words = file.read().splitlines()
    with open('word lists/longersixletterwords.txt', 'r') as file:
        longer_sixes = file.read().splitlines()
    with open('word lists/sevenletterwords.txt', 'r') as file:
        seven_letter_words = file.read().splitlines()
    with open('word lists/longersevenletterwords.txt', 'r') as file:
        longer_sevens = file.read().splitlines()

    chosen_list = []
    longer_list = []
    match mode:
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

def number_of_guesses() -> int:
    return 6

def is_word_valid(word: str, chosen_list : List[str]) -> bool:
    if word.upper() in chosen_list:
        return True
    else:
        return False

def random_word(chosen_list: List[str]) -> List[str]:
    random_word = chosen_list[random.randint(0, len(chosen_list)-1)]
    letters = list(random_word)
    return letters

#fix board type hint
def guessing(board, row: int,guess_letters: List[str], word : str) -> bool:
    guess = ''.join(guess_letters).upper()
    guess_letters = list(guess)
    letters = list(word.upper())

    #logic
    if guess == word:
        for cell in board[row]:
            cell.color = CellColors.GREEN
        return True
    else:
        #make a list for alphabet - color corrects in green, guesses in yellow, wrongs in black
        to_be_guessed = list(letters)

        for index, letter in enumerate(letters):
            if letter == guess_letters[index]:
                to_be_guessed.remove(guess_letters[index])
                board[row][index].color = CellColors.GREEN
                    
            elif guess_letters[index] in to_be_guessed:
                to_be_guessed.remove(guess_letters[index])
                board[row][index].color = CellColors.YELLOW
                    
            else:
                board[row][index].color = CellColors.BLACK
    return False

class CellColors(Enum):
    BLACK = (0, 0, 0)
    WHITE = (128, 128, 128)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)

class Cell:
    def __init__(self,letter='',color=CellColors.WHITE):
        self.letter = letter
        self.color = color

pygame.init()

pygame.font.init() 
my_font = pygame.font.SysFont('Arial', 30)

screen = pygame.display.set_mode((640,640))
clock = pygame.time.Clock()
delta_time = 0.1

#this needs to be changed during runtime
mode = 5 #5,6,7
amount_of_guesses = number_of_guesses()
chosen_list, longer_list = mode_choice(mode)
chosen_word = random_word(chosen_list)

#change list length depending on number of guesses
guess_list = [[],[],[],[],[],[]]
word_number = 0

valid_letter_inputs = [getattr(pygame, f"K_{chr(i)}") for i in range(ord('a'), ord('z') + 1)]

round_active = True

grid_size, grid_height, cell_size = mode, amount_of_guesses, 50
board = [[Cell() for _ in range(grid_size)] for _ in range(grid_height)]

running = True

pygame.display.set_caption('PVP Wordle')
while running:
    #closing the window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if round_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    #delete character
                    guess_list[word_number] = guess_list[word_number][:-1]
                elif event.key == pygame.K_RETURN and len(guess_list[word_number]) == 5:
                    if not is_word_valid(''.join(guess_list[word_number]),longer_list):
                        guess_list[word_number] = []
                        continue

                    if guessing(board,word_number,guess_list[word_number],''.join(chosen_word)):
                        round_active = False
                        print("You Won!")
                    else:
                        word_number+=1

                        if word_number == amount_of_guesses:
                            round_active = False
                            print("You Lost!")

                elif event.key in valid_letter_inputs and len(guess_list[word_number])<5:
                    guess_list[word_number].append(event.unicode)

    #white background
    screen.fill((255,255,255))


    for iy, rowOfCells in enumerate(board):
        for ix, cell in enumerate(rowOfCells):
            cell_rect = pygame.Rect(ix*cell_size+180, iy*cell_size+100, cell_size-5, cell_size-5)
            c_sur = my_font.render(cell.letter,False,(250,250,250))
            pygame.draw.rect(screen, cell.color.value, cell_rect)
 
    text_surface = my_font.render("\n".join(" ".join(str(letter) for letter in word) for word in guess_list), False, (250, 250, 250))

    screen.blit(text_surface, (250,100))

    #display stuff on the window
    pygame.display.flip()

    #time handling for framerate
    delta_time = clock.tick(60) / 1000
    delta_time = max(0.001, min(0.1,delta_time))

pygame.quit()