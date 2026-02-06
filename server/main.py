import socket
import threading
import json
from typing import Any, Dict
from protocols import Protocols
import time # may not need
from room import Room 

class Server:
    def __init__(self, host="127.0.0.1",port=55555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

        self.client_names = {}
        self.opponent: Dict[Any, Any] = {}
        self.rooms = {}
        self.waiting_rooms = {}  # room_code -> Room

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

        self.send_to_opponent(
            Protocols.Response.OPPONENT_LEFT,
            None,
            client
        )

    def start_new_round_for_room(self, room):
        if len(room.finished_players) < 2:
            return

        room.rounds -= 1

        if room.rounds <= 0:
            winner_client = max(room.points, key=room.points.get)
            winner_name = self.client_names[winner_client]

            for c in room.round_indexes.keys():
                self.send(Protocols.Response.WINNER, winner_name, c)
                del self.rooms[c]
                if c in self.opponent:
                    del self.opponent[c]

            return

        for client in room.round_indexes.keys():
            self.send(Protocols.Response.NEW_ROUND, None, client)

        room.finished_players.clear()

    def handle_receive(self, message, client):
        r_type = message.get("type")
        data = message.get("data")

        room = self.rooms.get(client)

        if r_type == Protocols.Request.CREATE_GAME:
            room_code = data.get("room_code")
            nickname = data.get("nickname")
            mode = data.get("mode", 5)
            attempts = data.get("attempts", mode + 1)
            rounds = data.get("rounds", 5)
            infinite = data.get("infinite", False)

            default_settings = {
                "mode": 5,
                "rounds": 5,
                "infinite": False,
                "max_guesses": 6
            }
            room = Room(client, default_settings) 
            room.mode = mode
            room.rounds = rounds
            room.max_guesses = attempts
            room.is_infinite = infinite

            self.rooms[room_code] = room
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
            if not room:
                return
            room.client_finished(client, data)

            self.start_new_round_for_room(room)
            
        elif r_type == Protocols.Request.LEAVE:
            room = self.rooms.get(client)
            if room:
                opponent = self.opponent.get(client)
                if opponent:
                    self.send(Protocols.Response.OPPONENT_LEFT, None, opponent)
                    del self.opponent[opponent]
                del self.rooms[client]
                if client in room.round_indexes:
                    del room.round_indexes[client]

        elif r_type == Protocols.Request.JOIN_GAME:
            room_code = data.get("room_code")
            nickname = data.get("nickname")
            room = self.rooms[room_code]

            if not room:
                self.send(Protocols.Response.ANSWER_INVALID, "Room not found", client)
                return

            if len(room.round_indexes) >= 2:
                self.send(Protocols.Response.ANSWER_INVALID, "Room full", client)
                return

            second_client = client
            room.round_indexes[second_client] = 0
            room.points[second_client] = 0
            self.client_names[second_client] = nickname

            first_client = [c for c in room.round_indexes.keys() if c != second_client][0]
            self.opponent[first_client] = second_client
            self.opponent[second_client] = first_client

            self.rooms[second_client] = room
            self.rooms[first_client] = room

            print(f"Client {nickname} joining room {room_code}")
            print(f"Room round_indexes now: {list(room.round_indexes.keys())}")

            if len(room.round_indexes) == 2:
                for c in room.round_indexes.keys():
                    self.send(Protocols.Response.GUESSES, room.guesses, c)
                    self.send(Protocols.Response.SETTINGS, {  # Add this!
                        "mode": room.mode,
                        "max_guesses": room.max_guesses,
                        "rounds": room.rounds,
                        "infinite": room.is_infinite
                    }, c)
                    self.send(Protocols.Response.START, None, c)

    def send(self, r_type, data, client):
        message = {"type": r_type, "data": data}
        message_str = json.dumps(message) + "\n"
        client.send(message_str.encode("ascii"))

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