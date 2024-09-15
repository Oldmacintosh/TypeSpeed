# -*- coding: utf-8 -*-
"""This module generates random sentences for the game."""

import os
import random


def get_sentences(
        data_path: str = os.path.join(os.path.dirname(__file__), 'data', 'sentences.txt')) -> list:
    """
    Reads the sentences from the file and returns them as a list.
    :param data_path: The path to the file containing the sentences.
    :return: The list of sentences.
    """
    with open(data_path, encoding='utf-8') as file:
        return file.readlines()


sentences: list = get_sentences()


def generate_sentence() -> str:
    """
    Generates a random sentence for the game.
    :return: The generated sentence.
    """
    global sentences
    if not sentences:
        sentences = get_sentences()
    sentence = random.choice(sentences)
    sentences.remove(sentence)
    return sentence.strip()


if __name__ == '__main__':
    print(generate_sentence())
