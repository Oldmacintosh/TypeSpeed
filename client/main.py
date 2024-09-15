# -*- coding: utf-8 -*-
"""
TypeSpeed is a typing speed test game where the user can host or
join a game and compete with other players to see who can type
the fastest. Each game can have a maximum of 10 players and each
game has five rounds.

This module is the client for TypeSpeed.
It handles the user input and the communication between the server.
"""

__author__: str = 'Oldmacintosh'
__version__: str = 'v1.1.1'
__date__: str = 'September 2024'
__PROJECT__: str = 'TypeSpeed'
__DEBUG__: bool = False

SERVER: str = '45.79.122.54'
PORT: int = 6969

if __name__ == '__main__':
    import os
    import sys
    import time
    import pickle
    import socket
    import inputimeout
    from pynput import keyboard
    from colorama import Fore, Style
    from dependencies.modules.communicator import send, receive
    from dependencies.modules.loader import Loader

    startup: bool = True
    server: socket.socket | None = None


    def print_bright(text: str) -> None:
        """
        Function to print text in bright color.
        :param text: The text to print.
        """
        print(Style.BRIGHT + text + Style.RESET_ALL)


    def print_green(text: str) -> None:
        """
        Function to print text in green color.
        :param text: The text to print.
        """
        print(Fore.GREEN + text + Style.RESET_ALL)


    def print_red(text: str) -> None:
        """
        Function to print text in red color.
        :param text: The text to print.
        """
        print(Fore.RED + text + Style.RESET_ALL)


    def cls(prompt: str | None = None) -> None:
        """
        Function to clear the screen.
        :param prompt: The prompt to display after clearing the screen.
        """
        os.system('clear' if os.name == 'posix' else 'cls')
        if prompt:
            print_bright(prompt)


    def flush_input() -> None:
        """Function to flush the input buffer."""
        try:
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except ModuleNotFoundError:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()


    def return_menu_input(prompt: str) -> str:
        """
        Input that also allows to return to a menu by typing 'menu' in
        the input.
        :param prompt: The prompt to display.
        :return: The user input.
        """
        _user_input = input(prompt)
        if _user_input.lower() == 'menu':
            raise InterruptedError
        return _user_input


    def compare_words(original: str, typed: str) -> str:
        """
        Compare two words and return the incorrect parts in red.
        :param original: The original word.
        :param typed: The typed word.
        :return: The incorrect parts in red.
        """
        if len(typed) < len(original):
            return Fore.RED + typed + Style.RESET_ALL

        incorrect_parts = []
        for original_char, typed_char in zip(original, typed):
            if original_char != typed_char:
                incorrect_parts.append(Fore.RED + typed_char + Style.RESET_ALL)
            else:
                incorrect_parts.append(typed_char)

        if len(typed) > len(original):
            excess_chars = typed[len(original):]
            incorrect_parts.extend([Fore.RED + char + Style.RESET_ALL for char in excess_chars])

        return ''.join(incorrect_parts)


    def compare_sentences(original: str, typed: str) -> str:
        """
        Compare two sentences and return the incorrect parts in red.
        :param original: The original sentence.
        :param typed: The typed sentence.
        :return: The incorrect parts in red.
        """
        original_words = original.split()
        typed_words = typed.split()

        if len(typed_words) < len(original_words):
            return Fore.RED + typed + Style.RESET_ALL

        incorrect_parts = []
        for original_word, typed_word in zip(original_words, typed_words):
            if original_word != typed_word:
                incorrect_parts.append(compare_words(original_word, typed_word))
            else:
                incorrect_parts.append(typed_word)

        if len(typed_words) > len(original_words):
            excess_words = typed_words[len(original_words):]
            incorrect_parts.extend([Fore.RED + word + Style.RESET_ALL for word in excess_words])

        return ' '.join(incorrect_parts)


    def check_username(_username) -> str:
        """
        Check if the given username is of the user.
        :param _username: The username to check.
        :return: The username with '(you)' if it is the user's username.
        """
        if _username == username:
            return _username + '(you)'
        return _username


    def get_username(header: str) -> str:
        """Get the username from the user."""
        while True:
            try:
                cls()
                print_bright(header)
                _username = return_menu_input('Enter your username: ')
                assert _username and len(_username) <= 20
                return _username
            except AssertionError:
                cls()
                print_red('Please enter a valid username!')
                input('Press enter to try again...')


    while True:
        while True:
            loader = None
            try:
                cls(f'{__PROJECT__}')
                loader = Loader('Connecting to the server...', end='')
                loader.start()
                if not __DEBUG__ and startup:
                    time.sleep(2)
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                server.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                server.connect((SERVER, PORT))
                server.send(b'1')
                loader.stop()
                if startup:
                    cls(f'{__PROJECT__}')
                    print_green('Connected to the server!')
                    time.sleep(2)
                    startup = False
                break
            except (ConnectionRefusedError, ConnectionResetError,
                    ConnectionAbortedError, TimeoutError):
                if loader:
                    loader.stop()
                cls(f'{__PROJECT__}')
                print_red('Could not connect to the server!')
                if input('Press enter to try again...') == 'dev':
                    cls(f'{__PROJECT__} {__version__}({__date__})')
                    print_green('Developer mode activated!')
                    SERVER = input('Enter the server IP: ')
                    PORT = int(input('Enter the server port: '))
        try:
            while True:
                cls()
                print_bright('Menu')
                print('0) Host a game')
                print('1) Join a game')
                print('2) Quit')
                user_input = input('Enter your choice: ')

                if user_input in ['0', '1', '2']:
                    break
                cls()
                print_red('Invalid input!')
                input('Press enter to try again...')

            if user_input == '0':
                while True:
                    try:
                        cls()
                        print_bright('Host a game')
                        players = int(return_menu_input('Enter the number of players(max 10): '))
                        assert 0 < players <= 10
                        break
                    except ValueError:
                        cls()
                        print_red('Invalid input!')
                    except AssertionError:
                        cls()
                        print_red('Invalid number of players!')
                    input('Press enter to try again...')

                username = get_username('Host a game')

                # Sending 0 to the server to tell that the user wants to
                # host a game.
                send('0', server)
                send(str(players), server)
                send(username, server)
                game_id = receive(server)

            elif user_input == '1':
                while True:
                    cls()
                    print_bright('Join a game')
                    game_id = return_menu_input('Enter the game ID: ')
                    # Sending 1 to the server to tell that the user wants
                    # to join a game.
                    send('1', server)
                    send(game_id, server)
                    message = receive(server)
                    if message == '1':
                        while True:
                            username = get_username('Join a game')
                            send(username, server)
                            message = receive(server)
                            if message == '1':
                                players = receive(server)
                                break
                            cls()
                            if message == '2':
                                print_red('Game is full!')
                                input('Press enter to try again...')
                                raise InterruptedError
                            print_red('Username already taken!')
                            input('Press enter to try again...')
                        break
                    cls()
                    if message == '0':
                        print_red('Invalid game ID!')
                    elif message == '2':
                        print_red('Game is full!')
                    input('Press enter to try again...')

            elif user_input == '2':
                break

            while True:
                players_connected = receive(server)
                # -1 is a ping from the server to check if the client
                # is still connected.
                if players_connected != '-1':
                    cls()
                    print(f'Game ID: {game_id}')  # noqa

                    if players_connected == '0':
                        print('Players connected: ' + Fore.GREEN +
                              f'{players}/{players}' + Style.RESET_ALL)  # noqa
                        time.sleep(2)
                        break
                    print('Players connected: ' + Fore.RED +
                          f'{players_connected}/{players}' + Style.RESET_ALL)

            for _round in range(1, 6):

                copy = False
                paste = False


                def on_copy() -> None:
                    """
                    Function executed when the copy hotkey is pressed.
                    """
                    global copy
                    copy = True


                def on_paste() -> None:
                    """
                    Function executed when the paste hotkey is pressed.
                    """
                    global paste
                    paste = True


                with keyboard.GlobalHotKeys({'<cmd>+c': on_copy,
                                             '<ctrl>+c': on_copy,
                                             '<cmd>+v': on_paste,
                                             '<ctrl>+v': on_paste}):

                    sentence = receive(server)

                    cls()
                    print_bright(f'Round no.{_round} is about to start! Get ready...')
                    time.sleep(2)

                    for time_left in range(5, -1, -1):
                        time.sleep(1)
                        cls()
                        print_bright(f'Round {_round}')
                        print('Type the following words as fast as you can: ' +
                              Style.BRIGHT + sentence + Style.RESET_ALL)
                        if time_left:
                            print(f'Start typing in {time_left}s')
                        else:
                            print('Start typing!')

                    flush_input()
                    try:
                        start = time.time()
                        user_sentence = inputimeout.inputimeout('Type: ', timeout=20)
                        end = time.time()
                    except inputimeout.TimeoutOccurred:
                        user_sentence = ''

                    if copy and paste:
                        send('-1', server)
                    elif user_sentence != sentence:
                        send('0', server)
                    else:
                        send(str(end - start), server)  # noqa

                    print('Waiting for other players to finish...')

                while True:
                    try:
                        result = receive(server, decode=False)
                        if result.decode() != '-1':
                            break
                    except UnicodeDecodeError:
                        break

                result = pickle.loads(result)  # noqa
                cls()
                print_bright(f'Round {_round}')
                print(f'Original sentence: {sentence}')
                if user_sentence != sentence:
                    print('Your sentence: ' + compare_sentences(sentence, user_sentence))
                else:
                    print('Your sentence: ' +
                          Fore.GREEN + Style.BRIGHT + user_sentence + Style.RESET_ALL)
                time.sleep(5)

                cls()

                print_bright(f'Round {_round} result')
                dnf = []
                cheat = []
                for key, value in result.items():
                    if value[0] == 0:
                        dnf.append(key)
                    elif value[0] == -1:
                        cheat.append(key)
                    else:
                        print(f'{check_username(key)}: {round(value[0], 2)}s({value[1]}WPM)')
                for key in cheat:
                    print(Fore.RED + f'{check_username(key)}: CHEATED' + Style.RESET_ALL)
                for key in dnf:
                    print(Style.DIM + f'{check_username(key)}: DNF' + Style.RESET_ALL)
                time.sleep(5)

            game_result = list(pickle.loads(receive(server, decode=False)).items())

            cls()
            print_bright('Game result')
            for position, player in enumerate(game_result):
                print(f'{position + 1}) {check_username(player[0])}: {player[1]}')
            input('Press enter to continue...')

        except (KeyboardInterrupt, InterruptedError):
            pass

        except ConnectionResetError:
            cls()
            print_bright('TypeSpeed')
            print_red('Connection lost!')
            input('Press enter to continue...')
            break

        finally:
            if server:
                server.close()
