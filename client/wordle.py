import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import pygame
from client_s import Client
from protocols import Protocols


class CellColors(Enum):
    BLACK = (10, 10, 10)
    WHITE = (128, 128, 128)
    YELLOW = (200, 200, 0)
    GREEN = (0, 255, 0)


class Cell:
    def __init__(
        self,
        letter: Optional[pygame.Surface] = None,
        color: CellColors = CellColors.WHITE,
        x: int = 0,
        y: int = 0,
        text: str = ''
    ) -> None:
        self.letter: Optional[pygame.Surface] = letter
        self.color: CellColors = color
        self.x: int = x
        self.y: int = y
        self.text: str = text


class Button:
    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        font: Optional[pygame.font.Font],
        bg_color: Tuple[int, int, int] = (200, 200, 200),
        text_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.text: str = text
        self.font: Optional[pygame.font.Font] = font
        self.bg_color: Tuple[int, int, int] = bg_color
        self.text_color: Tuple[int, int, int] = text_color

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.bg_color, self.rect)
        if self.font is not None:  # Add check
            text_surface: pygame.Surface = self.font.render(
                self.text, True, self.text_color
            )
            screen.blit(
                text_surface,
                (
                    self.rect.centerx - text_surface.get_width() / 2,
                    self.rect.centery - text_surface.get_height() / 2
                )
            )

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(mouse_pos)


class InputBox:
    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        font: Optional[pygame.font.Font],
        text: str = ''
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.font: Optional[pygame.font.Font] = font
        self.text: str = text
        self.color_active: pygame.Color = pygame.Color('gray')
        self.color_inactive: pygame.Color = pygame.Color('black')
        self.color: Union[pygame.Color, Tuple[int, int, int]] = self.color_inactive
        self.active: bool = False
        self.hidden: bool = False

    def toggle(self) -> None:
        if self.hidden:
            self.color = (0, 0, 0)
        else:
            self.color = (255, 255, 255)
        self.hidden = not self.hidden

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and not self.hidden:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        return None

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.color, self.rect, 2)
        if not self.font:
            return
        text_surface: pygame.Surface = self.font.render(
            self.text, True, self.color
        )
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))


class Wordle:
    def __init__(self, client: Client) -> None:
        self.client: Client = client
        client.start()

        self.game_state: str = "startup"
        self.room_code: str = ""
        self.settings: Dict[str, Any] = dict()

        self.font: Optional[pygame.font.Font] = None
        self.back_button: Button = Button(
            (20, 20, 150, 40), "Main Menu", self.font, bg_color=(200, 100, 100)
        )

        self.round_active: bool = False
        self.mode: int = 5
        self.amount_of_guesses: int = 6

        self.board: List[List[Cell]] = []

        self.round_start_time: float = time.time()

        self.guess_list: List[List[str]] = [[] for _ in range(self.amount_of_guesses)]
        self.word_number: int = 0
        self.letter_number: int = 0

        self.valid_letter_inputs: List[int] = [
            getattr(pygame, f"K_{chr(i)}") for i in range(ord('a'), ord('z') + 1)
        ]

        self.startup_buttons: List[Button] = []
        self.create_buttons: Dict[str, Button] = {}
        self.create_input_boxes: Dict[str, InputBox] = {}

        self.join_input_box: Optional[InputBox] = None
        self.join_nickname_box: InputBox = InputBox((150, 250, 300, 50), self.font)
        self.join_nickname_text: Optional[pygame.Surface] = None
        self.join_info_text: Optional[pygame.Surface] = None

        self.nickname: str = ""

        self.warning_text: str = ""

        self.infinite_mode: bool = False

        self.keyboard_letters: Dict[str, CellColors] = {
            'A': CellColors.WHITE, 'B': CellColors.WHITE, 'C': CellColors.WHITE,
            'D': CellColors.WHITE, 'E': CellColors.WHITE, 'F': CellColors.WHITE,
            'G': CellColors.WHITE, 'H': CellColors.WHITE, 'I': CellColors.WHITE,
            'J': CellColors.WHITE, 'K': CellColors.WHITE, 'L': CellColors.WHITE,
            'M': CellColors.WHITE, 'N': CellColors.WHITE, 'O': CellColors.WHITE,
            'P': CellColors.WHITE, 'Q': CellColors.WHITE, 'R': CellColors.WHITE,
            'S': CellColors.WHITE, 'T': CellColors.WHITE, 'U': CellColors.WHITE,
            'V': CellColors.WHITE, 'W': CellColors.WHITE, 'X': CellColors.WHITE,
            'Y': CellColors.WHITE, 'Z': CellColors.WHITE
        }

    # draws keyboard for easier guessing in wordle (cosmetic)
    def draw_keyboard(self, screen: pygame.Surface) -> None:
        # keyboard layout (QWERTY)
        keyboard_rows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]

        key_size = 40
        key_spacing = 5
        start_y = 500

        for row_idx, row in enumerate(keyboard_rows):
            row_width = len(row) * (key_size + key_spacing) - key_spacing
            start_x = (640 - row_width) // 2

            for col_idx, letter in enumerate(row):
                key_x = start_x + col_idx * (key_size + key_spacing)
                key_y = start_y + row_idx * (key_size + key_spacing + 5)

                key_color = self.keyboard_letters.get(letter, CellColors.WHITE)

                # draw key background
                pygame.draw.rect(
                    screen,
                    key_color.value,
                    (key_x, key_y, key_size, key_size),
                    border_radius=4
                )

                # draw key border
                pygame.draw.rect(
                    screen,
                    (50, 50, 50),
                    (key_x, key_y, key_size, key_size),
                    2,
                    border_radius=4
                )

                # draw letter
                font = pygame.font.SysFont('Arial', 20, bold=True)
                text_color = (
                    (255, 255, 255)
                    if key_color in [CellColors.BLACK, CellColors.GREEN]
                    else (0, 0, 0)
                )
                letter_surface = font.render(letter, True, text_color)
                text_x = key_x + (key_size - letter_surface.get_width()) // 2
                text_y = key_y + (key_size - letter_surface.get_height()) // 2
                screen.blit(letter_surface, (text_x, text_y))

    # draws startup screen with 3 options - joining a game,
    # creating a game and showing a leaderboard
    def draw_startup_screen(self, screen: pygame.Surface) -> None:
        self.back_button = Button(
            (20, 20, 150, 40), "Main Menu",
            pygame.font.SysFont('Arial', 25), bg_color=(200, 100, 100)
        )
        screen.fill((255, 255, 255))
        if not self.startup_buttons:
            self.font = pygame.font.SysFont("Arial", 30)
            self.startup_buttons = [
                Button((200, 200, 200, 50), "Join Game", self.font),
                Button((200, 300, 200, 50), "Create Game", self.font),
                Button((200, 400, 200, 50), "Leaderboard", self.font)
            ]
        for btn in self.startup_buttons:
            btn.draw(screen)

    def draw_leaderboard(self, screen: pygame.Surface) -> None:
        screen.fill((255, 255, 255))

        # title
        title_font = pygame.font.SysFont('Arial', 40, bold=True)
        title = title_font.render("LEADERBOARD - Top 10 Players", True, (0, 0, 0))
        screen.blit(title, (70, 70))

        # column headers
        header_font = pygame.font.SysFont('Arial', 28, bold=True)
        headers = ["Rank", "Player", "Wins"]
        x_positions = [100, 300, 450]

        for i, header in enumerate(headers):
            header_surface = header_font.render(header, True, (50, 50, 150))
            screen.blit(header_surface, (x_positions[i], 120))

        # leaderboard data
        data_font = pygame.font.SysFont('Arial', 24)
        y_offset = 160

        leaderboard_data = self.client.leaderboard_data

        # draws the player data
        for idx, player in enumerate(leaderboard_data):
            rank = idx + 1
            username = player['username']
            wins = player['wins']

            row_color = (240, 240, 240) if idx % 2 == 0 else (220, 220, 220)
            pygame.draw.rect(screen, row_color, (100, y_offset, 440, 30))

            data_items = [str(rank), username, str(wins)]

            for i, item in enumerate(data_items):
                text_surface = data_font.render(item, True, (0, 0, 0))
                screen.blit(text_surface, (x_positions[i], y_offset))

            y_offset += 40

        # back button
        self.back_button.draw(screen)

        # no data message (if theres no entries yet)
        if not leaderboard_data:
            no_data_font = pygame.font.SysFont('Arial', 30)
            no_data_text = no_data_font.render(
                "No leaderboard data available", True, (150, 0, 0)
            )
            screen.blit(no_data_text, (180, 300))

    # draws join screen with 2 input boxes - nickname and room code
    def draw_join_screen(self, screen: pygame.Surface) -> None:
        self.back_button = Button(
            (20, 20, 150, 40), "Main Menu",
            pygame.font.SysFont('Arial', 25), bg_color=(200, 100, 100)
        )
        screen.fill((255, 255, 255))
        if not self.join_input_box:
            self.font = pygame.font.SysFont("Arial", 30)
            self.join_nickname_box = InputBox((150, 250, 300, 50), self.font)
            self.join_nickname_text = self.font.render(
                "Enter your nickname:", True, (0, 0, 0)
            )
            self.join_input_box = InputBox((150, 350, 300, 50), self.font)
            self.join_info_text = self.font.render(
                "Enter room code to join:", True, (0, 0, 0)
            )
        if not self.join_info_text or not self.join_nickname_text:
            return
        screen.blit(self.join_info_text, (100, 300))
        screen.blit(self.join_nickname_text, (100, 200))

        self.back_button.draw(screen)

        self.join_nickname_box.draw(screen)
        self.join_input_box.draw(screen)

    # draws create screen where you have to submit the details
    # for a game (+ nickname and room code/password)
    def draw_create_screen(self, screen: pygame.Surface) -> None:
        screen.fill((255, 255, 255))
        self.font = pygame.font.SysFont("Arial", 30)
        self.back_button = Button(
            (20, 20, 150, 40), "Main Menu",
            pygame.font.SysFont('Arial', 25), bg_color=(200, 100, 100)
        )
        if not self.create_buttons:
            box_x = 360
            start_y = 140
            step = 70

            self.create_input_boxes = {
                "nickname": InputBox((box_x, start_y, 200, 40), self.font, text=''),
                "mode": InputBox((box_x, start_y + step, 100, 40), self.font,
                                 text=str(self.mode)),
                "attempts": InputBox((box_x, start_y + 2 * step, 100, 40), self.font,
                                     text=str(self.amount_of_guesses)),
                "rounds": InputBox((box_x, start_y + 3 * step, 100, 40), self.font,
                                   text='5'),
                "room_code": InputBox((box_x, start_y + 4 * step, 100, 40), self.font,
                                      text='ABCD'),
            }
            self.create_buttons = {
                "infinite": Button(
                    (270, start_y + 5 * step, 150, 40),
                    "Infinite: OFF",
                    self.font,
                    bg_color=(250, 150, 150)
                ),
                "start": Button(
                    (270, start_y + 6 * step, 100, 40),
                    "Start",
                    self.font,
                    bg_color=(180, 180, 180)
                ),
            }
        labels = [
            ("Nickname:", 140),
            ("Word Length (5-7)", 210),
            ("Attempts (2-(len+1))", 280),
            ("Rounds:", 350),
            ("Room Code:", 420),
        ]
        for text, y in labels:
            label_surface = self.font.render(text, True, (0, 0, 0))
            screen.blit(label_surface, (120, y))
        for box in self.create_input_boxes.values():
            box.draw(screen)
        for btn in self.create_buttons.values():
            btn.draw(screen)
        self.back_button.draw(screen)

    # draws waiting screen
    def draw_waiting(self, screen: pygame.Surface) -> None:
        self.font = pygame.font.SysFont('Arial', 30)

        text = "Waiting For Player..."

        text_surface = self.font.render(text, True, (0, 0, 0))
        screen.blit(
            text_surface,
            (screen.get_width() / 2 - text_surface.get_width() / 2,
             screen.get_height() / 2 - text_surface.get_height() / 2)
        )

    # draws score tab on the side of the screen during a game
    def draw_score(self, screen: pygame.Surface) -> None:
        score_font = pygame.font.SysFont('Arial', 24)
        title_font = pygame.font.SysFont('Arial', 28, bold=True)

        # score box position
        score_box_x = 20
        score_box_y = 150
        box_width = 140
        box_height = 120

        # draw score box background
        pygame.draw.rect(
            screen, (240, 240, 240),
            (score_box_x, score_box_y, box_width, box_height)
        )
        pygame.draw.rect(
            screen, (100, 100, 100),
            (score_box_x, score_box_y, box_width, box_height), 2
        )

        # draw title
        title = title_font.render("SCORE", True, (0, 0, 0))
        screen.blit(
            title,
            (score_box_x + (box_width - title.get_width()) // 2, score_box_y + 10)
        )

        # draw player score
        player_score = score_font.render(f"You: {self.client.points}", True, (0, 100, 0))
        screen.blit(player_score, (score_box_x + 20, score_box_y + 50))

        # draw opponent score (if opponent exists)
        if self.client.opponent_name:
            opponent_score = score_font.render(
                f"{self.client.opponent_name}: {self.client.opponent_points}",
                True,
                (200, 0, 0)
            )
            screen.blit(opponent_score, (score_box_x + 20, score_box_y + 80))

    # draws the guessing board
    def draw_game(self, screen: pygame.Surface) -> None:
        cell_size = 50

        # display each cell
        for iy, rowOfCells in enumerate(self.board):
            for ix, cell in enumerate(rowOfCells):
                cell_rect = pygame.Rect(
                    ix * cell_size + 180,
                    iy * cell_size + 100,
                    cell_size - 5,
                    cell_size - 5
                )
                cell.x = ix * cell_size + 180 + 15
                cell.y = iy * cell_size + 100 + 3
                pygame.draw.rect(screen, cell.color.value, cell_rect)

        # display letter per cell
        for row in self.board:
            for cell in row:
                if cell.letter is not None:
                    screen.blit(cell.letter, (cell.x, cell.y))

        self.draw_score(screen)

        self.draw_keyboard(screen)

    # resets board state
    def reset_board(self) -> None:
        self.board = [[Cell() for _ in range(self.mode)]
                      for _ in range(self.amount_of_guesses)]
        self.guess_list = [[] for _ in range(self.amount_of_guesses)]
        self.word_number = 0
        self.letter_number = 0
        self.round_start_time = time.time()

        self.client.warning = ""
        self.warning_text = ""

        # reset keyboard colors
        for letter in self.keyboard_letters:
            self.keyboard_letters[letter] = CellColors.WHITE

        self.round_active = True

    def draw_warning(self, screen:pygame.Surface) -> None:
        self.font = pygame.font.SysFont('Arial', 30)

        warning_surface = self.font.render(self.warning_text, True, (0, 0, 250))

        warning_rect = warning_surface.get_rect()
        warning_rect.centerx = screen.get_rect().centerx
        warning_rect.top = 60

        screen.blit(warning_surface, warning_rect)

    # main draw function that alternates between states
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((255, 255, 255))

        if self.game_state == "startup":
            self.draw_startup_screen(screen)
        elif self.game_state == "join":
            self.draw_join_screen(screen)
        elif self.game_state == "create":
            self.draw_create_screen(screen)
        elif self.game_state == "leaderboard":
            self.draw_leaderboard(screen)
        elif self.game_state == "waiting":
            self.draw_waiting(screen)
        elif self.game_state == "playing":
            self.client.warning = ""
            self.draw_game(screen)

        if self.warning_text:
            self.draw_warning(screen)

        pygame.display.flip()

    # color each cell based on the validity of the guess
    def guessing(self, row: int, guess_letters: List[str], word: str) -> bool:
        guess = ''.join(guess_letters).upper()
        guess_letters = list(guess)
        letters = list(word.upper())

        # handle keyboard letter statuses
        letter_status: Dict[str, CellColors] = {}

        for index, letter in enumerate(letters):
            if letter == guess_letters[index]:
                letter_status[letter] = CellColors.GREEN

        for index, guess_letter in enumerate(guess_letters):
            if guess_letter in letters and guess_letter != letters[index]:
                if guess_letter not in letter_status:
                    letter_status[guess_letter] = CellColors.YELLOW

        for guess_letter in guess_letters:
            if guess_letter not in letters:
                letter_status[guess_letter] = CellColors.BLACK

        for letter, status in letter_status.items():
            current_status = self.keyboard_letters.get(letter, CellColors.WHITE)

            if status == CellColors.GREEN:
                self.keyboard_letters[letter] = CellColors.GREEN
            elif (
                status == CellColors.YELLOW
                and current_status not in [CellColors.GREEN]
            ):
                self.keyboard_letters[letter] = CellColors.YELLOW
            elif status == CellColors.BLACK and current_status == CellColors.WHITE:
                self.keyboard_letters[letter] = CellColors.BLACK

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
                        for cell in self.board[row]:
                            if cell.text == guess_letters[index] and cell.color == CellColors.YELLOW:
                                setattr(cell, 'color', CellColors.BLACK)
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

    # main handle function that alternates between states
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.game_state == "startup":
            self.handle_event_startup(event)
        elif self.game_state == "join":
            self.handle_event_join(event)
        elif self.game_state == "create":
            self.handle_event_create(event)
        elif self.game_state == "leaderboard":
            self.handle_event_leaderboard(event)
        elif self.game_state == "playing" and self.round_active:
            self.handle_wordle_event(event)

    # startup - handles join and create, and sends a leaderboard request
    def handle_event_startup(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.startup_buttons:
                if btn.is_clicked(event.pos):
                    if btn.text == "Leaderboard":
                        self.game_state = "leaderboard"
                        self.client.send(Protocols.Request.GET_LEADERBOARD, {})
                    self.game_state = btn.text.lower().split()[0]

    # only handles leaderboard back button
    def handle_event_leaderboard(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                self.game_state = "startup"

    # handles join - processes nickname and room code
    def handle_event_join(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                self.return_to_main_menu()
                return

        if not self.join_input_box or not self.join_nickname_box:
            return

        self.join_input_box.handle_event(event)
        self.join_nickname_box.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            room_code = self.join_input_box.text.strip()
            nickname = self.join_nickname_box.text.strip()

            if not room_code or not nickname:
                return

            self.client.send(Protocols.Request.JOIN_GAME, {
                "room_code": room_code,
                "nickname": nickname
            })

            print(self.client.warning)

            if self.client.warning:
                self.game_state = "join"
            else:
                self.game_state = "waiting"

    # handles the create screen - has input boxes for all settings +
    # nickname and creates room based on them
    def handle_event_create(self, event: pygame.event.Event) -> None:
        for box in self.create_input_boxes.values():
            box.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                self.return_to_main_menu()
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.create_buttons["infinite"].is_clicked(event.pos):
                self.infinite_mode = not self.infinite_mode
                btn = self.create_buttons["infinite"]
                if self.infinite_mode:
                    btn.text = "Infinite: ON"
                    btn.bg_color = (150, 250, 150)
                    self.create_input_boxes["rounds"].toggle()
                else:
                    btn.text = "Infinite: OFF"
                    btn.bg_color = (250, 150, 150)
                    self.create_input_boxes["rounds"].toggle()

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
            nickname = self.create_input_boxes["nickname"].text.strip()[:15]
            c_mode = self.create_input_boxes["mode"].text
            c_attempts = self.create_input_boxes["attempts"].text
            c_rounds = self.create_input_boxes["rounds"].text
            c_room_code = self.create_input_boxes["room_code"].text.strip()[:4]

            is_mode_valid = c_mode.isdigit() and int(c_mode) in range(5, 8)
            is_attempts_valid = (
                is_mode_valid and c_attempts.isdigit()
                and int(c_attempts) in range(2, int(c_mode) + 2)
            )
            is_rounds_valid = c_rounds.isdigit() and int(c_rounds)>0

            are_inputs_invalid = (
                not nickname or not c_room_code or not is_rounds_valid
                or not is_mode_valid or not is_attempts_valid
            )
            if are_inputs_invalid:
                self.warning_text = "Please make sure all fields are valid!"
                return

            self.warning_text = ""
            payload = {
                "mode": int(c_mode),
                "attempts": int(c_attempts),
                "rounds": int(c_rounds),
                "room_code": c_room_code,
                "nickname": nickname,
                "infinite": self.infinite_mode
            }

            self.mode = payload["mode"]
            self.amount_of_guesses = payload["attempts"]

            self.client.send(Protocols.Request.CREATE_GAME, payload)
            self.game_state = "waiting"

    # handles the game scene, which is just a basic wordle gameset
    def handle_wordle_event(self, event: pygame.event.Event) -> None:
        self.font = pygame.font.SysFont('Arial', 30)

        if self.client.current_round_index >= len(self.client.guesses):
            return

        chosen_word = self.client.guesses[self.client.current_round_index]

        if self.round_active:
            if event.type == pygame.KEYDOWN:
                # delete character
                if event.key == pygame.K_BACKSPACE:
                    self.guess_list[self.word_number] = (
                        self.guess_list[self.word_number][:-1]
                    )

                    if self.letter_number != 0:
                        self.letter_number -= 1

                    self.board[self.word_number][self.letter_number].letter = (
                        self.font.render(''.upper(), False, (250, 250, 250))
                    )

                elif (
                    event.key == pygame.K_RETURN
                    and len(self.guess_list[self.word_number]) == self.mode
                ):
                    if not self.client.is_word_valid(
                        ''.join(self.guess_list[self.word_number])
                    ):
                        self.warning_text = "Invalid word"
                        return

                    self.warning_text = ""

                    if self.guessing(
                        self.word_number,
                        self.guess_list[self.word_number],
                        ''.join(chosen_word)
                    ):
                        self.warning_text = "You guessed it right!"
                        print(f"You guessed it right! - {chosen_word}")
                        guess_str = ''.join(self.guess_list[self.word_number])
                        seconds_taken = time.time() - self.round_start_time

                        payload = {
                            "guess": guess_str,
                            "guesses_used": self.word_number + 1,
                            "seconds": seconds_taken,
                            "success": True
                        }

                        self.client.send(Protocols.Request.ANSWER, payload)
                        print(self.client.new_round)

                    else:
                        self.word_number += 1

                        if self.word_number == self.amount_of_guesses:
                            seconds_taken = time.time() - self.round_start_time
                            guess_str = ''.join(self.guess_list[self.word_number - 1])

                            payload = {
                                "guess": guess_str,
                                "guesses_used": self.word_number + 1,
                                "seconds": seconds_taken,
                                "success": False
                            }

                            self.client.send(Protocols.Request.ANSWER, payload)
                            self.warning_text = (
                                f"You didn't guess it! "
                                f"The word was {''.join(chosen_word)}"
                            )
                            print(self.client.new_round)

                    self.letter_number = 0

                elif (
                    event.key in self.valid_letter_inputs
                    and len(self.guess_list[self.word_number]) < self.mode
                ):
                    self.guess_list[self.word_number].append(event.unicode)
                    self.board[self.word_number][self.letter_number].letter = (
                        self.font.render(
                            str(event.unicode).upper(), False, (250, 250, 250)
                        )
                    )
                    self.letter_number += 1

    # resets game variables
    def return_to_main_menu(self) -> None:
        self.game_state = "startup"
        self.round_active = False
        self.reset_board()

        self.nickname = ""

        self.warning_text = ""

        self.client.started = False
        self.client.new_round = False

        self.client.warning = ""

        self.client.opponent_left = False
        self.client.winner = None

        self.client.current_round_index = 0
        self.client.guesses = []
        self.client.points = 0
        self.client.opponent_points = 0

    # handles the end state for the game
    def handle_end(self, screen: pygame.Surface) -> None:
        self.font = pygame.font.SysFont('Arial', 30)

        run = True
        while run:
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

            self.back_button.draw(screen)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    self.client.close()
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.back_button.is_clicked(event.pos):
                        self.client.send(Protocols.Request.LEAVE, {})

                        self.return_to_main_menu()

                        run = False

    # runs the game
    def run(self) -> None:
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

                self.handle_event(event)

            if self.client.warning:
                self.warning_text = self.client.warning
                self.client.warning = ""

            self.draw(screen)

            if self.game_state == "waiting":
                if self.client.started:
                    self.game_state = "playing"
                    self.mode = self.client.mode
                    self.amount_of_guesses = self.client.max_guesses
                    self.board = [
                        [Cell() for _ in range(self.mode)]
                        for _ in range(self.amount_of_guesses)
                    ]
                    self.round_active = True
                    self.round_start_time = time.time()

            if self.client.new_round:
                time.sleep(1)
                self.reset_board()
                self.client.new_round = False

            if self.client.winner or self.client.opponent_left:
                self.handle_end(screen)
                self.return_to_main_menu()
                continue

            delta_time = clock.tick(60) / 1000
            delta_time = max(0.001, min(0.1, delta_time))
        self.client.close()
        pygame.quit()


if __name__ == "__main__":
    game = Wordle(Client())
    game.run()