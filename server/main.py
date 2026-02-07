import random
import socket
import threading
import json
from typing import Any, Dict
from protocols import Protocols
from room import Room 
from db import DB

class Server:
    def __init__(self, host="127.0.0.1",port=55555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

        self.client_names = {}
        self.opponent: Dict[Any, Any] = {}
        self.rooms_by_code = {}      # room_code -> Room
        self.client_to_room = {}     # client -> Room

        self.db = DB()

    def handle(self, client):
        print("Client connected.")
        while True:
            try:
                data = client.recv(1024).decode("ascii")
                if not data:
                    break
                message = json.loads(data)
                self.handle_receive(message, client)
            except:
                break
        try:
            self.send_to_opponent(
                Protocols.Response.OPPONENT_LEFT,
                None,
                client
            )
        except:
            pass  # opponent already disconnected

    def start_new_round_for_room(self, room):
        if len(room.finished_players) < 2:
            return

        if room.is_infinite and len(room.failed_players) == 2:
            winner_client = max(room.points, key=room.points.get)
            winner_name = self.client_names[winner_client]
            
            for c in room.round_indexes.keys():
                self.send(Protocols.Response.WINNER, winner_name, c)
            return
        
        if not room.is_infinite:
            room.rounds -= 1
        
        if room.rounds <= 0 and not room.is_infinite:
            winner_client = max(room.points, key=room.points.get)
            winner_name = self.client_names[winner_client]
            
            for c in room.round_indexes.keys():
                self.send(Protocols.Response.WINNER, winner_name, c)
            return
        
        if room.is_infinite:
            random_word = room.chosen_list[random.randint(0, len(room.chosen_list)-1)]
            letters = list(random_word)
            room.guesses.append(letters)
            for c in room.round_indexes.keys():
                self.send(Protocols.Response.GUESSES, room.guesses, c)
        
        for client in room.round_indexes.keys():
            opponent_client = self.opponent.get(client)
            if opponent_client:
                opponent_name = self.client_names[opponent_client]
                opponent_points = room.points[opponent_client]
                self.send(Protocols.Response.OPPONENT, {
                    "name": opponent_name,
                    "points": opponent_points
                }, client)
            if not room.is_infinite:
                room.round_indexes[client] += 1
            self.send(Protocols.Response.NEW_ROUND, None, client)
        
        room.finished_players.clear()
        room.failed_players.clear()

    def handle_receive(self, message, client):
        r_type = message.get("type")
        data = message.get("data")

        if r_type == Protocols.Request.CREATE_GAME:
            room_code = data.get("room_code")
            nickname = data.get("nickname")
            mode = data.get("mode", 5)
            attempts = data.get("attempts", mode + 1)
            rounds = data.get("rounds", 5)
            infinite = data.get("infinite", False)

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
            if not room:
                return
            room.client_finished(client, data)

            opponent = self.opponent.get(client)
            self.send(Protocols.Response.POINTS_UPDATE, {
                "your_points": room.points[client],
                "opponent_points": room.points.get(opponent, 0) if opponent else 0
            }, client)
            
            # Also send to opponent if they exist
            if opponent:
                self.send(Protocols.Response.POINTS_UPDATE, {
                    "your_points": room.points[opponent],
                    "opponent_points": room.points[client]
                }, opponent)

            self.start_new_round_for_room(room)
            
        elif r_type == Protocols.Request.LEAVE:
            room = self.client_to_room.get(client)
            if not room:
                return   

            room_code = None
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

        elif r_type == Protocols.Request.JOIN_GAME:
            room_code = data.get("room_code")
            nickname = data.get("nickname")
            room = self.rooms_by_code.get(room_code)

            if not room:
                self.send(Protocols.Response.INVALID_REQUEST, "Room not found", client)
                return

            if len(room.round_indexes) >= 2:
                self.send(Protocols.Response.INVALID_REQUEST, "Room full", client)
                return

            second_client = client
            room.round_indexes[second_client] = 0
            room.points[second_client] = 0
            self.client_names[second_client] = nickname

            first_client = [c for c in room.round_indexes.keys() if c != second_client][0]
            self.opponent[first_client] = second_client
            self.opponent[second_client] = first_client
            
            self.client_to_room[second_client] = room
            self.client_to_room[first_client] = room

            print(f"Client {nickname} joining room {room_code}")

            if len(room.round_indexes) == 2:
                for c in room.round_indexes.keys():
                    self.send(Protocols.Response.GUESSES, room.guesses, c)
                    self.send(Protocols.Response.SETTINGS, {  # Add this!
                        "mode": room.mode,
                        "max_guesses": room.max_guesses,
                        "rounds": room.rounds,
                        "infinite": room.is_infinite
                    }, c)
                    opponent_client = self.opponent.get(c)
                    if opponent_client:
                        opponent_name = self.client_names[opponent_client]
                        opponent_points = room.points[opponent_client]
                        self.send(Protocols.Response.OPPONENT, {
                            "name": opponent_name,
                            "points": opponent_points
                        }, c)
                    self.send(Protocols.Response.START, None, c)

    def send(self, r_type, data, client):
        message = {"type": r_type, "data": data}
        message_str = json.dumps(message) + "\n"
        try:
                client.send(message_str.encode("ascii"))
        except (ConnectionResetError, BrokenPipeError):
            pass

    def send_to_opponent(self, r_type, data, client): 
        opponent = self.opponent.get(client)
        if not opponent:
            return
        self.send(r_type,data,opponent)

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}")
            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

if __name__ == "__main__":
    server = Server()
    server.receive()