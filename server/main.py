# -*- coding: utf-8 -*-
"""
This module is the server for TypsSpeed.
It listens for incoming connections and handles them accordingly.

Each game is run in a separate thread and has a four-digit
unique id which can be used to join the game.
"""

__author__: str = 'Oldmacintosh'
__version__: list[str] = ['v1.1.0', 'v1.1.1']
__date__: str = 'July 2024'
__PROJECT__: str = 'TypeSpeed'

import random
import socket
import threading
import logging
from dependencies.modules.game import Game
from dependencies.modules.communicator import send, receive

SERVER: str = ''
PORT: int = 6969
# Create the socket for the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((SERVER, PORT))
server.listen()
server.settimeout(1)

games: dict[str, Game] = {}

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s')
logging.getLogger().setLevel(logging.INFO)


def handle_client(client: socket.socket, address: tuple[str, int]) -> None:
    """
    Handles the client connection.
    It allows the client to host or join a game.
    :param client: The client socket.
    :param address: The address of the client.
    """
    game: Game | None = None
    try:
        message = receive(client)
        # Host a game
        if message == '0':
            # Get the number of players and the username and create
            # a game with the client as the host.
            player_count = int(receive(client))
            username = receive(client)
            game = Game(client, username, player_count, create_id())
            games[game.game_id] = game
        # Join a game
        elif message == '1':
            while True:
                # Get the game id and check if the game exists and
                # is active and then check if the game has not yet
                # started and then join the game.
                game_id = receive(client)
                if game_id in games and games[game_id].active:
                    if not games[game_id].game_started:
                        # Game join able
                        send('1', client)
                        game = games[game_id]
                        break
                    # Game already started
                    send('2', client)
                else:
                    # Game does not exist
                    send('0', client)
            while True:
                # Get the username and check if it is unique and
                # the game has not yet started and then
                # add the player to the game.
                username = receive(client)
                if username not in game.players.values():
                    if not game.game_started:
                        # Game join successful
                        send('1', client)
                        game.add_player(client, username)
                        break
                    # Game already started
                    send('2', client)
                else:
                    # Username not unique
                    send('0', client)

    except ConnectionResetError:
        if game:
            game.remove_player(client)
        client.close()
        logging.info('main: Connection closed(%s)', address)

    except Exception as _error:
        logging.exception(_error)


def create_id() -> str:
    """Creates a random four digit unique id."""
    while True:
        _id = str(random.randint(1000, 9999))
        if _id not in games:
            return _id


if __name__ == '__main__':
    logging.info('main: Server is listening for connections...')
    try:
        while True:
            connection = None
            try:
                connection = server.accept()
                # Ensure that the connection is by a client and not a
                # random connection.
                connection[0].settimeout(30)
                if connection[0].recv(64).decode() == '1':
                    connection[0].settimeout(None)
                else:
                    raise ConnectionResetError
                threading.Thread(target=handle_client,
                                 args=(connection[0], connection[1]),
                                 daemon=True).start()
                logging.info('main: Connection accepted(%s)', connection[1])
            except (UnicodeDecodeError, ConnectionResetError, socket.timeout):
                if connection:
                    connection[0].close()
                continue
    except KeyboardInterrupt:
        pass

    except Exception as error:
        logging.exception(error)

    finally:
        server.close()
        logging.info('main: Server shutdown successful.')
