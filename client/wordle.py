import pygame
import time
from enum import Enum
from typing import Any, Dict, List
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

class Button:
    def __init__(self, rect, text, font, bg_color=(200,200,200), text_color=(0,0,0)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        screen.blit(
            text_surface,
            (self.rect.centerx - text_surface.get_width()/2, self.rect.centery - text_surface.get_height()/2)
        )

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

class InputBox:
    def __init__(self, rect, font, text=''):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = text
        self.color_active = pygame.Color('gray')
        self.color_inactive = pygame.Color('black')
        self.color = self.color_inactive
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 2)
        text_surface = self.font.render(self.text, True, self.color)
        screen.blit(text_surface, (self.rect.x+5, self.rect.y+5))

class Wordle:
    def __init__(self,client):
        self.client = client
        client.start()

        self.game_state = "startup"
        self.choice = None
        self.room_code = None
        self.settings: Optional[Dict[str, Any]] = None

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

        self.startup_buttons = []
        self.create_buttons = {}
        self.join_input_box = None
        self.create_input_boxes = {}

        self.nickname = ""
        self.pending_join_code = None
        self.pending_settings = None


    def draw_startup_screen(self, screen):
        self.back_button = Button((20, 20, 150, 40), "Main Menu", pygame.font.SysFont('Arial', 25), bg_color=(200, 100, 100))
        screen.fill((255,255,255))
        if not self.startup_buttons:
            self.font = pygame.font.SysFont("Arial", 30)
            self.startup_buttons = [
                Button((200,200,200,50),"Join Game",self.font),
                Button((200,300,200,50),"Create Game",self.font)
            ]
        for btn in self.startup_buttons:
            btn.draw(screen)

    def draw_join_screen(self, screen):
        self.back_button = Button((20, 20, 150, 40), "Main Menu", pygame.font.SysFont('Arial', 25), bg_color=(200, 100, 100))
        screen.fill((255,255,255))
        if not self.join_input_box:
            self.font = pygame.font.SysFont("Arial",30)
            self.join_input_box = InputBox((150,250,300,50), self.font)
            self.join_info_text = self.font.render("Enter room code to join:", True, (0,0,0))
            self.join_nickname_box = InputBox((150,350,300,50), self.font)  # nickname
            self.join_nickname_text = self.font.render("Enter your nickname:", True, (0,0,0))
        screen.blit(self.join_info_text, (100, 150))
        screen.blit(self.join_nickname_text, (100, 300))

        self.back_button.draw(screen)

        self.join_nickname_box.draw(screen)
        self.join_input_box.draw(screen)

    def draw_create_screen(self, screen):
        self.back_button = Button((20, 20, 150, 40), "Main Menu", pygame.font.SysFont('Arial', 25), bg_color=(200, 100, 100))
        screen.fill((255,255,255))
        self.font = pygame.font.SysFont("Arial",30)
        if not self.create_buttons:
            screen.blit(self.font.render("Enter your nickname:", True, (0,0,0)), (50, 430))
            self.create_input_boxes = {
                "mode": InputBox((250,150,100,40), self.font, text=str(self.mode)),
                "attempts": InputBox((250,220,100,40), self.font, text=str(self.amount_of_guesses)),
                "rounds": InputBox((250,290,100,40), self.font, text='5'),
                "room_code": InputBox((250,360,100,40), self.font, text='ABCD'),
                "nickname": InputBox((250,430,300,40), self.font, text='')
            }
            self.create_buttons = {
                "infinite": Button((250,430,100,40),"Infinite",self.font,bg_color=(150,250,150)),
                "start": Button((250,500,100,40),"Start",self.font)
            }
            self.infinite_mode = False

        labels = ["Word Length (5-7):","Attempts (2-(Word Lenght+1)):","Rounds:","Room Code:"]
        y_positions = [150,220,290,360]
        for label,y in zip(labels,y_positions):
            screen.blit(self.font.render(label, True, (0,0,0)), (50,y))
        for box in self.create_input_boxes.values():
            box.draw(screen)
        for btn in self.create_buttons.values():
            btn.draw(screen)
        self.back_button.draw(screen)

    def draw_waiting(self, screen):
        self.font = pygame.font.SysFont('Arial', 30)
        
        text = "Waiting For Player..."
            
        text_surface = self.font.render(text, True, (0, 0, 0))
        screen.blit(
            text_surface,
            (screen.get_width()/2 - text_surface.get_width()/2, 
            screen.get_height()/2 - text_surface.get_height()/2)
        )

    def draw_login(self, screen):
        self.font = pygame.font.SysFont('Arial', 30)

        # Display prompt
        text = 'Enter A Nickname'
        text_surface = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_surface, (100, 50))

        # Draw input box
        pygame.draw.rect(screen, self.color, self.input_box, 2)

        # Render the actual nickname being typed
        txt_surface = self.font.render(self.nickname, True, self.color)
        screen.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))

        # Adjust width of input box dynamically
        self.input_box.w = max(100, txt_surface.get_width() + 10)

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

    def draw(self, screen):
        screen.fill((255, 255, 255))

        if self.game_state == "startup":
            self.draw_startup_screen(screen)
        elif self.game_state == "join":
            self.draw_join_screen(screen)
        elif self.game_state == "create":
            self.draw_create_screen(screen)
        elif self.game_state == "waiting":
            self.draw_waiting(screen)
        elif self.game_state == "playing":
            self.draw_game(screen)

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
        if self.game_state == "startup":
            self.handle_event_startup(event)
        elif self.game_state == "join":
            self.handle_event_join(event)
        elif self.game_state == "create":
            self.handle_event_create(event)
        elif self.game_state == "waiting":
            # allow main menu button if needed
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(self, "back_button") and self.back_button.is_clicked(event.pos):
                    self.return_to_main_menu()
        elif self.game_state == "playing" and self.round_active:
            self.handle_wordle_event(event)

    def handle_event_nickname(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.nickname.strip() != "":
                self.client.nickname = self.nickname

                if self.game_state == "join_nickname":
                    payload = {"room_code": self.pending_join_code, "nickname": self.nickname}
                    self.client.send(Protocols.Request.JOIN_GAME, payload)

                elif self.game_state == "create_nickname":
                    if not self.pending_settings:
                        return
                    payload = self.pending_settings.copy()
                    payload["nickname"] = self.nickname
                    self.client.send(Protocols.Request.CREATE_GAME, payload)

                # Enter waiting state for UI immediately
                self.game_state = "waiting"

            elif event.key == pygame.K_BACKSPACE:
                self.nickname = self.nickname[:-1]
            else:
                self.nickname += event.unicode

    def handle_event_startup(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.startup_buttons:
                if btn.is_clicked(event.pos):
                    self.choice = btn.text.lower().split()[0]
                    self.game_state = self.choice

    def handle_event_join(self, event):
        # Main menu button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                self.return_to_main_menu()
                return

        if not self.join_input_box or not self.join_nickname_box:
            return

        # Let the input boxes handle clicks and typing
        room_result = self.join_input_box.handle_event(event)
        nick_result = self.join_nickname_box.handle_event(event)

        # If Enter pressed in either box, try to submit
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            room_code = self.join_input_box.text.strip()
            nickname = self.join_nickname_box.text.strip()

            if not room_code or not nickname:
                return  # optionally, display warning

            # Send JOIN_GAME request with nickname
            self.client.send(Protocols.Request.JOIN_GAME, {
                "room_code": room_code,
                "nickname": nickname
            })

            # Move to waiting screen
            self.game_state = "waiting"



    def handle_event_create(self, event):
        # Handle typing in all input boxes
        for box in self.create_input_boxes.values():
            box.handle_event(event)

        # Main menu button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                self.return_to_main_menu()
                return

        # Infinite button toggle
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.create_buttons["infinite"].is_clicked(event.pos):
                self.infinite_mode = not self.infinite_mode
                self.create_buttons["infinite"].bg_color = (250,150,150) if self.infinite_mode else (150,250,150)

        # Start button or Enter key sends create request
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.create_buttons["start"].is_clicked(event.pos):
                send_create = True
            else:
                send_create = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            send_create = True
        else:
            send_create = False

        if send_create:
            nickname = self.create_input_boxes["nickname"].text.strip()
            if not nickname:
                return  # optionally, display warning

            payload = {
                "mode": int(self.create_input_boxes["mode"].text),
                "attempts": int(self.create_input_boxes["attempts"].text),
                "rounds": int(self.create_input_boxes["rounds"].text),
                "room_code": self.create_input_boxes["room_code"].text.strip(),
                "nickname": nickname,
                "infinite": self.infinite_mode
            }

            # Update local game settings
            self.mode = payload["mode"]
            self.amount_of_guesses = payload["attempts"]

            # Send CREATE_GAME request
            self.client.send(Protocols.Request.CREATE_GAME, payload)
            self.game_state = "waiting"


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

    def return_to_main_menu(self):
        # Reset game variables
        self.game_state = "startup"
        self.round_active = False
        self.word_number = 0
        self.letter_number = 0
        self.guess_list = [[] for _ in range(self.amount_of_guesses)]
        self.board = [[Cell() for _ in range(self.mode)] for _ in range(self.amount_of_guesses)]
        
        # Reset any pending room/nickname info
        self.nickname = ""
        self.pending_join_code = None
        self.pending_settings = None
        
        # Optionally reconnect or just reset game without closing server
        self.client.started = False
        self.client.new_round = False

        self.client.opponent_left = False
        self.client.winner = None


    def handle_end(self, screen):
        self.font = pygame.font.SysFont('Arial', 30)
        self.back_button = Button((20, 20, 150, 40), "Main Menu", pygame.font.SysFont('Arial', 25), bg_color=(200, 100, 100))

        run = True
        while run:
            #screen.fill((255, 255, 255))

            # Display winner / opponent left
            if self.client.winner:
                text = f"{self.client.winner} has won the game!"
            else:
                text = "Opponent left the game..."

            text_surface = self.font.render(text, True, (0, 0, 0))
            screen.blit(
                text_surface,
                (screen.get_width() / 2 - text_surface.get_width() / 2,
                screen.get_height() / 2 - text_surface.get_height() / 2)
            )

            # Draw the Main Menu button
            self.back_button.draw(screen)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    self.client.close()
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.back_button.is_clicked(event.pos):
                        # Notify server we're leaving
                        self.client.send(Protocols.Request.LEAVE, {})

                        # Reset everything for main menu
                        self.return_to_main_menu()

                        # Exit handle_end loop
                        run = False  # <-- don't use 'return' here

    def run(self):
        pygame.init()
        self.font = pygame.font.SysFont('Arial', 30)
        pygame.font.init()

        screen = pygame.display.set_mode((640, 640))
        clock = pygame.time.Clock()
        
        pygame.display.set_caption('PVP Wordle')

        while not self.client.closed:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.close()
                    pygame.quit()
                    return
                else:
                    self.handle_event(event)

            self.draw(screen)

            # Fix for waiting -> playing transition
            if self.game_state == "waiting":
                if self.client.started:
                    self.game_state = "playing"
                    self.round_active = True
                    self.round_start_time = time.time()

            if self.client.new_round:
                self.reset_board()
                self.client.new_round = False

            if self.client.winner or self.client.opponent_left:
                self.handle_end(screen)
                # Reset game for main menu
                self.return_to_main_menu()
                continue

            # Maintain framerate
            delta_time = clock.tick(60) / 1000
            delta_time = max(0.001, min(0.1, delta_time))

        # End screen
        #self.handle_end(screen)
        pygame.quit()



if __name__ == "__main__":
    game = Wordle(Client())
    game.run()