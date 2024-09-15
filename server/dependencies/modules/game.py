# -*- coding: utf-8 -*-
"""
Each game is handled by a separate instance of the Game class.
"""

import time
import pickle
import socket
import threading
import logging
from dependencies.modules.communicator import send, receive  # noqa
from dependencies.modules.sentence_generator import generate_sentence  # noqa


def sort_dict(dictionary: dict, reverse: bool = False) -> dict:
    """
    Sorts a dictionary by its values.
    :param dictionary: The dictionary to sort.
    :param reverse: Whether to sort in reverse order.
    :return: The sorted dictionary.
    """
    return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1], reverse=reverse)}


class Game:
    """
    It represents a game of TypSpeed.
    It handles the game logic and the communication between the clients
    during the game.
    """

    host: socket.socket
    player_count: int
    game_id: str
    # dictionary of player's socket and their username
    players: dict[socket.socket, str]
    clients: list[socket.socket]

    active: bool
    game_started: bool
    sentence: str | None
    # list of threads for receiving time from clients
    threads: list[threading.Thread]
    # dictionary of player's socket and their time taken
    time_taken: dict[socket.socket, float]

    round_result: dict[str, tuple[float, int]]
    game_result: dict[str, int]

    def __init__(self, host: socket.socket, username: str, player_count: int, game_id: str):
        self.host = host
        self.player_count = player_count
        self.game_id = game_id
        self.players = {host: username}
        self.clients = [self.host]

        self._send(self.game_id, self.host)
        # Tell that only one player is currently in the game
        self._send('1', self.host)

        self.active = True
        self.game_started = False
        self.sentence = None
        self.threads = []
        self.time_taken = {}
        self.round_result = {}
        self.game_result = {}

        threading.Thread(target=self.check_clients_active, daemon=True).start()

        logging.info('game(%s): Game activated(%s, %s, %s)',
                     game_id, host.getpeername(), username, player_count)
        self.check_start()

    def deactivate(self) -> None:
        """Deactivates the game."""
        self.active = False
        logging.info('game(%s): Game deactivated.', self.game_id)

    def add_player(self, client: socket.socket, username: str) -> None:
        """
         Adds a player to the game.
        :param username: The username of the player.
        :param client: The socket of the player.
        Note
            A player should only be added if the game has not yet
            started, this should be checked before calling this
            method.
        """
        self.players[client] = username
        self.clients.append(client)

        self._send(str(self.player_count), client)
        self._broadcast(str(len(self.clients)))

        logging.info('game(%s): Player added(%s, %s)',
                     self.game_id, client.getpeername(), username)
        self.check_start()

    def remove_player(self, client: socket.socket) -> None:
        """
        Removes a player from the game.
        If the game has already started, the player's score is also
        removed from the game result.
        """
        if client in self.clients:
            self.clients.remove(client)
            if self.players[client] in self.game_result:
                del self.game_result[self.players[client]]
            logging.warning('game(%s): Player removed(%s)', self.game_id, self.players[client])
            del self.players[client]

        # If the game has not started, send the new player count to
        # the players if there are any.
        if not self.game_started:
            if len(self.clients):
                self._broadcast(str(len(self.clients)))
            else:
                logging.warning('game(%s): No players left.', self.game_id)
                self.deactivate()

    def main(self) -> None:
        """
        The main game loop.
        It runs for five rounds and then determines the results for
        each round and the game.
        """

        self.game_started = True
        # Tell the clients that the game has started
        self._broadcast('0')

        # Initialize the game result by setting the score of each
        # player to 0.
        for client in self.clients:
            self.game_result[self.players[client]] = 0

        for _ in range(5):
            self.threads.clear()
            self.round_result.clear()

            self.sentence = generate_sentence()
            self._broadcast(self.sentence)

            # Receive the time taken from each client in a separate
            # thread.
            for client in self.clients:
                thread = threading.Thread(target=self.receive_time, args=(client,), daemon=True)
                self.threads.append(thread)
                thread.start()
            for thread in self.threads:
                thread.join()

            # Calculate the results for the round and broadcast them
            # to the clients.
            self.determine_results()
            self._broadcast(pickle.dumps(self.round_result), encode=False)

        # Determine the game result and broadcast it to the clients.
        self._broadcast(pickle.dumps(sort_dict(self.game_result, reverse=True)), encode=False)
        self.deactivate()

    def check_start(self) -> None:
        """
        Checks if the game can start and then starts the game if
        possible.
        """
        if len(self.clients) == self.player_count:
            self.main()

    def check_clients_active(self) -> None:
        """Checks if the clients are still connected to the game."""
        while not self.game_started:
            # Send a ping to the clients to check if they are still
            # connected.
            time.sleep(1)
            for client in self.clients:
                self._send('-1', client)

    def receive_time(self, client: socket.socket) -> None:
        """Receives the time taken from a client."""
        time_taken = self._receive(client)
        if time_taken:
            self.time_taken[client] = float(time_taken)

    def determine_results(self) -> None:
        """Determines the results of the game."""
        self.time_taken = sort_dict(self.time_taken)
        for client in self.time_taken:
            try:
                # If the sentence was incorrect
                if self.time_taken[client] == 0:
                    wpm = 0
                # If the client cheated by copying and pasting the sentence
                elif self.time_taken[client] == -1:
                    wpm = -50
                else:
                    wpm = round((len(self.sentence) / 5) / (self.time_taken[client] / 60))
                self.round_result[self.players[client]] = (self.time_taken[client], wpm)
                self.game_result[self.players[client]] += wpm
            except KeyError:
                pass

    def _broadcast(self, *args, **kwargs):
        for client in self.clients:
            self._send(*args, **kwargs, connection=client)

    def _send(self, *args, **kwargs):
        try:
            send(*args, **kwargs)
        except ConnectionResetError:
            try:
                connection = args[1]
            except IndexError:
                connection = kwargs['connection']
            self._close(connection)

    def _receive(self, *args, **kwargs):
        try:
            return receive(*args, **kwargs)
        except ConnectionResetError:
            self._close(args[0])

    def _close(self, connection: socket.socket) -> None:
        self.remove_player(connection)
        logging.info('game(%s): Connection closed(%s)', self.game_id, connection)
        connection.close()
