import random
import socket
import threading
import json
from typing import Any, Dict, Optional, Union, cast
from protocols import Protocols
from room import Room
from db import DB


class Server:
    def __init__(self, host: str = "0.0.0.0", port: int = 55555) -> None:
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

        self.client_names: Dict[socket.socket, str] = {}
        self.opponent: Dict[socket.socket, socket.socket] = {}
        self.rooms_by_code: Dict[str, Room] = {}
        self.client_to_room: Dict[socket.socket, Room] = {}

        self.db = DB()

    def handle(self, client: socket.socket) -> None:
        print("Client connected.")
        while True:
            try:
                data = client.recv(1024).decode("ascii")
                if not data:
                    break
                message = json.loads(data)
                self.handle_receive(message, client)
            except Exception:
                break
        try:
            self.send_to_opponent(
                Protocols.Response.OPPONENT_LEFT,
                None,
                client
            )
        except Exception:
            pass  # opponent already disconnected

    def start_new_round_for_room(self, room: Room) -> None:
        if len(room.finished_players) < 2:
            return

        if room.is_infinite and len(room.failed_players) == 2:
            if room.points:

                winner_client = max(room.points.keys(), key=lambda k: room.points.get(k, 0))
                winner_name = self.client_names[winner_client]

                if len(set(room.points.values())) == 1:
                    winner_name = "everyone"
                    for client in room.points.keys():
                        self.db.increase_wins(self.client_names[client])
                else:
                    self.db.increase_wins(winner_name)

                for c in room.round_indexes.keys():
                    self.send(Protocols.Response.WINNER, winner_name, c)
            return

        if not room.is_infinite:
            room.rounds -= 1

        if room.rounds <= 0 and not room.is_infinite:
            if room.points:
                winner_client = max(room.points.keys(), key=lambda k: room.points.get(k, 0))
                winner_name = self.client_names[winner_client]

                self.db.increase_wins(winner_name)

                for c in room.round_indexes.keys():
                    self.send(Protocols.Response.WINNER, winner_name, c)
            return

        if room.is_infinite:
            random_word = room.chosen_list[
                random.randint(0, len(room.chosen_list) - 1)
            ]
            letters = list(random_word)
            room.guesses.append(letters)
            for c in room.round_indexes.keys():
                self.send(Protocols.Response.GUESSES, room.guesses, c)

        for client_socket in room.round_indexes.keys():
            opponent_client = self.opponent.get(client_socket)
            if opponent_client:
                opponent_name = self.client_names[opponent_client]
                opponent_points = room.points.get(opponent_client, 0)
                self.send(Protocols.Response.OPPONENT, {
                    "name": opponent_name,
                    "points": opponent_points
                }, client_socket)
            if not room.is_infinite:
                room.round_indexes[client_socket] += 1
            self.send(Protocols.Response.NEW_ROUND, None, client_socket)

        room.finished_players.clear()
        room.failed_players.clear()

    def handle_receive(self, message: Dict[str, Any], client: socket.socket) -> None:
        r_type = message.get("type")
        data = message.get("data")

        if r_type == Protocols.Request.CREATE_GAME:
            if not isinstance(data, dict):
                return
            room_code = data.get("room_code")
            nickname = data.get("nickname")
            mode = data.get("mode", 5)
            attempts = data.get("attempts", mode + 1)
            rounds = data.get("rounds", 5)
            infinite = data.get("infinite", False)

            if not isinstance(room_code, str) or not isinstance(nickname, str):
                return

            settings = {
                "mode": mode,
                "rounds": rounds,
                "infinite": infinite,
                "max_guesses": attempts
            }
            room = Room(client, settings)
            room.mode = mode
            room.rounds = rounds
            room.max_guesses = attempts
            room.is_infinite = infinite
            room.nicknames.append(nickname)

            self.rooms_by_code[room_code] = room
            self.client_to_room[client] = room
            self.client_names[client] = nickname

            room.round_indexes = {client: 0}
            room.points = {client: 0}

            self.send(Protocols.Response.SETTINGS, {
                "mode": mode,
                "max_guesses": attempts,
                "rounds": rounds,
                "infinite": infinite
            }, client)

        elif r_type == Protocols.Request.ANSWER:
            room = self.client_to_room.get(client)
            if not room or not isinstance(data, dict):
                return
            room.client_finished(client, cast(Dict[str, Any], data))

            opponent = self.opponent.get(client)
            self.send(Protocols.Response.POINTS_UPDATE, {
                "your_points": room.points.get(client, 0),
                "opponent_points": room.points.get(opponent, 0)
                if opponent else 0
            }, client)

            # Also send to opponent if they exist
            if opponent:
                self.send(Protocols.Response.POINTS_UPDATE, {
                    "your_points": room.points.get(opponent, 0),
                    "opponent_points": room.points.get(client, 0)
                }, opponent)

            self.start_new_round_for_room(room)

        elif r_type == Protocols.Request.LEAVE:
            room = self.client_to_room.get(client)
            if not room:
                return

            room_code: Optional[str] = None
            for code, r in self.rooms_by_code.items():
                if r == room:
                    room_code = code
                    break

            opponent = self.opponent.get(client)
            if opponent:
                self.send(Protocols.Response.OPPONENT_LEFT, None, opponent)

                if opponent in self.opponent and self.opponent[opponent] == client:
                    del self.opponent[opponent]
                del self.opponent[client]

            if client in self.client_to_room:
                del self.client_to_room[client]
            if client in self.client_names:
                del self.client_names[client]

            if client in room.round_indexes:
                del room.round_indexes[client]
            if client in room.points:
                del room.points[client]

            if room.host == client and room.guest:
                room.host = room.guest
                room.guest = None
            elif room.guest == client:
                room.guest = None

            if len(room.round_indexes) == 0:
                if room_code and room_code in self.rooms_by_code:
                    del self.rooms_by_code[room_code]
            else:
                remaining_client = list(room.round_indexes.keys())[0]
                self.send(Protocols.Response.OPPONENT_LEFT, None, remaining_client)

        elif r_type == Protocols.Request.GET_LEADERBOARD:
            leaderboard_data = self.db.get_leaderboard()
            self.send(Protocols.Response.LEADERBOARD, leaderboard_data, client)
        elif r_type == Protocols.Request.JOIN_GAME:
            if not isinstance(data, dict):
                return
            room_code = data.get("room_code")
            nickname = data.get("nickname")
            
            if not isinstance(room_code, str) or not isinstance(nickname, str):
                return
                
            room = self.rooms_by_code.get(room_code)

            if not room:
                self.send(
                    Protocols.Response.INVALID_REQUEST,
                    "Room not found",
                    client
                )
                return
            
            if nickname in room.nicknames:
                self.send(
                    Protocols.Response.INVALID_REQUEST,
                    "Nickname taken",
                    client
                )
                return

            if len(room.round_indexes) >= 2:
                self.send(
                    Protocols.Response.INVALID_REQUEST,
                    "Room full",
                    client
                )
                return

            second_client = client
            room.round_indexes[second_client] = 0
            room.points[second_client] = 0
            self.client_names[second_client] = nickname

            first_client = [
                c for c in room.round_indexes.keys() if c != second_client
            ][0]
            self.opponent[first_client] = second_client
            self.opponent[second_client] = first_client

            self.client_to_room[second_client] = room
            self.client_to_room[first_client] = room

            print(f"Client {nickname} joining room {room_code}")

            if len(room.round_indexes) == 2:
                for c in room.round_indexes.keys():
                    self.send(Protocols.Response.GUESSES, room.guesses, c)
                    self.send(Protocols.Response.SETTINGS, {
                        "mode": room.mode,
                        "max_guesses": room.max_guesses,
                        "rounds": room.rounds,
                        "infinite": room.is_infinite
                    }, c)
                    opponent_client = self.opponent.get(c)
                    if opponent_client:
                        opponent_name = self.client_names[opponent_client]
                        opponent_points = room.points.get(opponent_client, 0)
                        self.send(Protocols.Response.OPPONENT, {
                            "name": opponent_name,
                            "points": opponent_points
                        }, c)
                    self.send(Protocols.Response.START, None, c)

    def send(
        self,
        r_type: Union[Protocols.Response, str],
        data: Any,
        client: socket.socket
    ) -> None:
        message = {"type": r_type, "data": data}
        message_str = json.dumps(message) + "\n"
        try:
            client.send(message_str.encode("ascii"))
        except (ConnectionResetError, BrokenPipeError):
            pass

    def send_to_opponent(
        self,
        r_type: Union[Protocols.Response, str],
        data: Any,
        client: socket.socket
    ) -> None:
        opponent = self.opponent.get(client)
        if not opponent:
            return
        self.send(r_type, data, opponent)

    def receive(self) -> None:
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}")
            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()


if __name__ == "__main__":
    server = Server()
    server.receive()