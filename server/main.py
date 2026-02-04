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
        self.waiting_for_pair = None

    def handle_connect(self, client):
        while True:
            self.send(Protocols.Response.NICKNAME, None, client)
            message = json.loads(client.recv(1024).decode("ascii"))
            r_type = message.get("type")
            nickname = message.get("data")

            if r_type == Protocols.Request.NICKNAME:
                self.client_names[client] = nickname
            else:
                continue

            #change    
            if not self.waiting_for_pair:
                self.waiting_for_pair = client
                print("waiting for a room")
            else:
                self.create_room(client)

            break

    def create_room(self,client):
        print("Creating room.")
        room = Room(client,self.waiting_for_pair)
        self.opponent[client] = self.waiting_for_pair
        #change
        self.opponent[self.waiting_for_pair] = client

        self.send(Protocols.Response.OPPONENT, self.client_names[client], self.waiting_for_pair)
        self.send(Protocols.Response.OPPONENT, self.client_names[self.waiting_for_pair], client)

        self.rooms[client] = room
        #change
        self.rooms[self.waiting_for_pair] = room
        self.waiting_for_pair = None

    #change
    def wait_for_room(self,client):
        while True:
            room = self.rooms.get(client)
            opponent = self.opponent.get(client)

            if room and opponent:
                self.send(Protocols.Response.GUESSES, room.guesses, client)
                time.sleep(1)
                self.send(Protocols.Response.START, None, client)
                break

    def handle(self, client):
        self.handle_connect(client)
        self.wait_for_room(client)

        while True:
            try:
                data = client.recv(1024).decode("ascii")
                if not data:
                    break
                message = json.loads(data)
                self.handle_receive(message,client)
            except:
                break

        self.send_to_opponent(Protocols.Response.OPPONENT_LEFT,None,client)
        self.disconnect(client)

    def disconnect(self, client):
        opponent = self.opponent.get(client)
        if opponent in self.opponent:
            del self.opponent[opponent]

        if client in self.opponent:
            del self.opponent[client]


        if client in self.client_names:
            del self.client_names[client]

        if opponent in self.client_names:
            del self.client_names[opponent]


        if client in self.rooms:
            del self.rooms[client]

        if opponent in self.rooms:
            del self.rooms[opponent]

        client.close()

    def start_new_round_for_room(self, room):
        if len(room.finished_players) < 2:
            return

        for client in room.round_indexes.keys():
            self.send(Protocols.Response.NEW_ROUND, None, client)

        room.start_new_round()

    def handle_receive(self, message,client):
        r_type = message.get("type")
        data = message.get("data")
        room = self.rooms[client]

        opponent = self.opponent.get(client)
        if not opponent:
            return

        if r_type != Protocols.Request.ANSWER:
            return
        
        room.client_finished(client, data)

        # mark client finished all rounds
        if room.round_indexes[client] == len(room.guesses):
            room.all_finished_players.add(client)

        # if both players finished, decide winner
        if len(room.all_finished_players) == len(room.round_indexes):
            winner = max(room.points, key=lambda c: room.points[c])

            for c in room.points.keys():
                self.send(
                    Protocols.Response.WINNER,
                    self.client_names[winner],
                    c
                )
            return

        # marks that client finished the round
        room.finished_players.add(client)

        # checks if both clients finished; send NEW_ROUND to both if so
        self.start_new_round_for_room(room)


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