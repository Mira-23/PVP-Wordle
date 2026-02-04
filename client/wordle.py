import pygame
import time
from enum import Enum
from typing import List
from typing import Optional
from client_s import Client
from protocols import Protocols

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

class Wordle:
    def __init__(self,client):
        self.client = client
        client.start()

        self.done = False
        self.logged_in = False

        self.font = None

        self.round_active = False
        self.mode = 5
        self.amount_of_guesses = 6

        self.color_active = pygame.Color("gray")
        self.color_inactive = pygame.Color("black")
        self.color = self.color_inactive
        self.input_box = pygame.Rect(100,100,400,32)
        self.text = ""
        self.board = [[Cell() for _ in range(self.mode)] for _ in range(self.amount_of_guesses)]

        self.round_start_time = time.time()

        self.guess_list = [[] for _ in range(self.amount_of_guesses)]
        self.word_number = 0
        self.letter_number = 0

        self.valid_letter_inputs = [getattr(pygame, f"K_{chr(i)}") for i in range(ord('a'), ord('z') + 1)]


    def draw_waiting(self, screen):
        self.font = pygame.font.SysFont('Arial', 30)
        text = 'Waiting For Player'
        text_surface = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_surface, (screen.get_width()/2-text_surface.get_width()/2, screen.get_width()/2-text_surface.get_height()/2))

    def draw_login(self, screen):
        self.font = pygame.font.SysFont('Arial', 30)
        text = 'Enter A Nickname'
        text_surface = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_surface, (100, 50))

        pygame.draw.rect(screen, self.color, self.input_box, 2)
        txt_surface = self.font.render(self.text, True, self.color)
        screen.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))
        self.input_box.w = max(100, txt_surface.get_width() * 10)

    def draw_game(self,screen):
        cell_size = 50

        # display each cell
        for iy, rowOfCells in enumerate(self.board):
            for ix, cell in enumerate(rowOfCells):
                cell_rect = pygame.Rect(ix*cell_size+180, iy*cell_size+100, cell_size-5, cell_size-5)
                cell.x = ix*cell_size+180 + 15
                cell.y = iy*cell_size+100 + 3
                pygame.draw.rect(screen, cell.color.value, cell_rect)
        
        # display letter per cell
        for row in self.board:
            for cell in row:
                if cell.letter is not None:
                    screen.blit(cell.letter, (cell.x,cell.y))

    def reset_board(self):
        self.board = [[Cell() for _ in range(self.mode)]
                    for _ in range(self.amount_of_guesses)]
        self.guess_list = [[] for _ in range(self.amount_of_guesses)]
        self.word_number = 0
        self.letter_number = 0
        self.client.finished = False
        self.round_start_time = time.time()

    def draw(self,screen):
        # white background
        screen.fill((255,255,255))

        if not self.logged_in and not self.client.started:
            self.draw_login(screen)
        elif not self.client.started:
            self.draw_waiting(screen)
        else:
            self.draw_game(screen)

        # display stuff on the window
        pygame.display.flip()

# fix board type hint
    def guessing(self, row: int, guess_letters: List[str], word : str) -> bool:
        guess = ''.join(guess_letters).upper()
        guess_letters = list(guess)
        letters = list(word.upper())

        # logic
        if guess == word:
            for cell in self.board[row]:
                cell.color = CellColors.GREEN
            return True
        else:
            to_be_guessed = list(letters)

            for index, letter in enumerate(letters):
                if letter == guess_letters[index]:
                    if guess_letters[index] not in to_be_guessed:
                        [setattr(cell, 'color', CellColors.BLACK) for cell in self.board[row] if cell.text == guess_letters[index] and cell.color == CellColors.YELLOW]
                        to_be_guessed.append(guess_letters[index])

                    to_be_guessed.remove(guess_letters[index])
                    color = CellColors.GREEN
                        
                elif guess_letters[index] in to_be_guessed:
                    to_be_guessed.remove(guess_letters[index])
                    color = CellColors.YELLOW

                else:
                    color = CellColors.BLACK
                
                self.board[row][index].text = guess_letters[index]
                self.board[row][index].color = color

        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and not self.round_active:
                if not self.logged_in:
                    self.client.send(Protocols.Request.NICKNAME, self.text)
                    self.client.nickname = self.text
                    self.logged_in = True
                    self.text = ""
                    self.round_active = True
            elif event.key == pygame.K_BACKSPACE and not self.round_active:
                self.text = self.text[:-1]
            elif self.round_active:
                self.text = ""
                self.handle_wordle_event(event)
            else:
                self.text += event.unicode

    def handle_wordle_event(self,event):
        self.font = pygame.font.SysFont('Arial', 30)
        chosen_word = self.client.guesses[self.client.current_round_index]

        if self.round_active:
            if event.type == pygame.KEYDOWN:
                 # delete character
                if event.key == pygame.K_BACKSPACE:

                    self.guess_list[self.word_number] = self.guess_list[self.word_number][:-1]

                    if self.letter_number != 0:
                        self.letter_number-=1

                    self.board[self.word_number][self.letter_number].letter = self.font.render(''.upper(),False,(250,250,250))

                elif event.key == pygame.K_RETURN and len(self.guess_list[self.word_number]) == self.mode:
                    if not self.client.is_word_valid(''.join(self.guess_list[self.word_number])):
                        print("Invalid word")
                        return

                    if self.guessing(self.word_number,self.guess_list[self.word_number],''.join(chosen_word)):
                        print("You guessed it right!")
                        self.client.current_round_index+=1
                        guess_str = ''.join(self.guess_list[self.word_number])
                        seconds_taken = time.time() - self.round_start_time

                        payload = {
                            "guess": guess_str,
                            "guesses_used": self.word_number + 1,
                            "seconds": seconds_taken
                        }

                        self.client.send(Protocols.Request.ANSWER, payload)
                        print(self.client.new_round)
                                
                    else:
                        self.word_number+=1

                        if self.word_number == self.amount_of_guesses:
                            seconds_taken = time.time() - self.round_start_time
                            self.client.current_round_index+=1
                            guess_str = ''.join(self.guess_list[self.word_number-1])
                            
                            payload = {
                                "guess": guess_str,
                                "guesses_used": self.word_number + 1,
                                "seconds": seconds_taken
                            }

                            self.client.send(Protocols.Request.ANSWER, payload)
                            print(f"You didn't guess it! The word was {''.join(chosen_word)}")
                            print(self.client.new_round)
                                    
                    self.letter_number = 0

                elif event.key in self.valid_letter_inputs and len(self.guess_list[self.word_number])<self.mode:
                    self.guess_list[self.word_number].append(event.unicode)
                    self.board[self.word_number][self.letter_number].letter = self.font.render(str(event.unicode).upper(),False,(250,250,250))
                    self.letter_number+=1

    def handle_end(self,screen):
        self.font = pygame.font.SysFont('Arial', 30)

        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            if self.client.winner:
                text = f"{self.client.winner} has won the game!"
            else:
                text = f"Opponent left the game..."

            text_surface = self.font.render(text, True, (0, 0, 0))
            screen.blit(text_surface, (screen.get_width() / 2 - text_surface.get_width() / 2, screen.get_height() / 2 - text_surface.get_height() / 2))
            pygame.display.update()

    def run(self):
        pygame.init()

        self.font = pygame.font.SysFont('Arial', 30)
        pygame.font.init() 

        screen = pygame.display.set_mode((640,640))
        clock = pygame.time.Clock()
        delta_time = 0.1
        
        pygame.display.set_caption('PVP Wordle')
        while not self.client.closed:
            # closing the window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.close()
                    pygame.quit()
                else:
                    if self.client.new_round:
                        self.reset_board()
                        self.client.new_round = False
                    self.handle_event(event)
            
            self.draw(screen)

            # time handling for framerate
            delta_time = clock.tick(60) / 1000
            delta_time = max(0.001, min(0.1,delta_time))

        self.handle_end(screen)
        pygame.quit()

if __name__ == "__main__":
    game = Wordle(Client())
    game.run()