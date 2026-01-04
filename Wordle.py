import pygame
import random
from enum import Enum
from typing import List
from typing import Optional

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

def choose_random_word(chosen_list: List[str]) -> List[str]:
    random_word = chosen_list[random.randint(0, len(chosen_list)-1)]
    letters = list(random_word)
    return letters

# fix board type hint
def guessing(board, row: int,guess_letters: List[str], word : str) -> bool:
    guess = ''.join(guess_letters).upper()
    guess_letters = list(guess)
    letters = list(word.upper())

    # logic
    if guess == word:
        for cell in board[row]:
            cell.color = CellColors.GREEN
        return True
    else:
        # make a list for alphabet - color corrects in green, guesses in yellow, wrongs in black
        to_be_guessed = list(letters)

        for index, letter in enumerate(letters):
            if letter == guess_letters[index]:
                if guess_letters[index] not in to_be_guessed:
                    [setattr(cell, 'color', CellColors.BLACK) for cell in board[row] if cell.text == guess_letters[index] and cell.color == CellColors.YELLOW]
                    to_be_guessed.append(guess_letters[index])
                to_be_guessed.remove(guess_letters[index])
                board[row][index].color = CellColors.GREEN
                board[row][index].text = guess_letters[index]
                    
            elif guess_letters[index] in to_be_guessed:
                to_be_guessed.remove(guess_letters[index])
                board[row][index].color = CellColors.YELLOW
                board[row][index].text = guess_letters[index]
                    
            else:
                board[row][index].color = CellColors.BLACK
                board[row][index].text = guess_letters[index]
    return False

class CellColors(Enum):
    BLACK = (10, 10, 10)
    WHITE = (128, 128, 128)
    YELLOW = (200, 200, 0)
    GREEN = (0, 255, 0)

class Cell:
    def __init__(self, letter: Optional[pygame.Surface] = None, color=CellColors.WHITE,x=0,y=0, text=''):
        self.letter = letter
        self.color = color
        self.x = x
        self.y = y
        self.text = text

pygame.init()

pygame.font.init() 
my_font = pygame.font.SysFont('Arial', 30)

screen = pygame.display.set_mode((640,640))
clock = pygame.time.Clock()
delta_time = 0.1

# this needs to be changed during runtime
mode = 5 #5,6,7
amount_of_guesses = number_of_guesses()
chosen_list, longer_list = mode_choice(mode)
chosen_word = choose_random_word(chosen_list)

guess_list = [[] for _ in range(amount_of_guesses)]
word_number = 0
letter_number = 0

valid_letter_inputs = [getattr(pygame, f"K_{chr(i)}") for i in range(ord('a'), ord('z') + 1)]

grid_size, grid_height, cell_size = mode, amount_of_guesses, 50
board = [[Cell() for _ in range(grid_size)] for _ in range(grid_height)]

round_active = True

running = True

pygame.display.set_caption('PVP Wordle')
while running:
    # closing the window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if round_active:
            if event.type == pygame.KEYDOWN:
                # delete character
                if event.key == pygame.K_BACKSPACE:

                    guess_list[word_number] = guess_list[word_number][:-1]

                    if letter_number != 0:
                        letter_number-=1

                    board[word_number][letter_number].letter = my_font.render(''.upper(),False,(250,250,250))

                elif event.key == pygame.K_RETURN and len(guess_list[word_number]) == mode:
                    if not is_word_valid(''.join(guess_list[word_number]),longer_list):
                        print("Invalid word")
                        continue

                    if guessing(board,word_number,guess_list[word_number],''.join(chosen_word)):
                        round_active = False
                        print("You Won!")
                        
                    else:
                        word_number+=1

                        if word_number == amount_of_guesses:
                            round_active = False
                            print(f"You Lost! The word was {''.join(chosen_word)}")
                            
                    letter_number = 0

                elif event.key in valid_letter_inputs and len(guess_list[word_number])<mode:
                    guess_list[word_number].append(event.unicode)
                    board[word_number][letter_number].letter = my_font.render(str(event.unicode).upper(),False,(250,250,250))
                    letter_number+=1

    # white background
    screen.fill((255,255,255))

    # display each cell
    for iy, rowOfCells in enumerate(board):
        for ix, cell in enumerate(rowOfCells):
            cell_rect = pygame.Rect(ix*cell_size+180, iy*cell_size+100, cell_size-5, cell_size-5)
            cell.x = ix*cell_size+180 + 15
            cell.y = iy*cell_size+100 + 3
            pygame.draw.rect(screen, cell.color.value, cell_rect)
 
    # display letter per cell
    for row in board:
        for cell in row:
            if cell.letter is not None:
                screen.blit(cell.letter, (cell.x,cell.y))

    # display stuff on the window
    pygame.display.flip()

    # time handling for framerate
    delta_time = clock.tick(60) / 1000
    delta_time = max(0.001, min(0.1,delta_time))

pygame.quit()