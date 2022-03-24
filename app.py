from distutils import text_file
from pytchat import create
from threading import Thread, Event
from queue import Queue, Empty
from sys import argv
from pexpect import TIMEOUT, EOF
from time import sleep
import re

import game_api as game
from printer_api import tsp_print

QUEUE_LOOKBACK = 1
VIDEO_ID = argv[1]
FONT = "Ubuntu Mono Bold Nerd Font Complete Mono.ttf"
FONT = "Meslo LG L Bold Nerd Font Complete Mono.ttf"
TEXT_WIDTH = 48

chat_queue = Queue()
terminate_event = Event()


def chat_crawler():
    """
    Continuously retrieve chat messages from YT stream and plug them into the queue 
    """

    chat = create(video_id=VIDEO_ID)
    while chat.is_alive() and not terminate_event.is_set():
        for c in chat.get().sync_items():
            chat_queue.put((c.author.name, c.message))

    terminate_event.set()


def game_loop():
    """
    Primary Gameplay Controller
    """

    while not terminate_event.is_set():
        try:

            # start & restore the game
            txt = game.start(width=TEXT_WIDTH)
            if game.restore():
                txt = game.step("look")
                print2paper(txt, "look", "[AUTO RECOVERY]")
            else:
                print2paper(txt)

            # interactive game cycle
            while not terminate_event.is_set():
                try:

                    # retrieve latest player message
                    n = spool_messages()
                    if n > 0:
                        print(f"...skipping {n} messages...")

                    author, message = chat_queue.get(timeout=10)
                    print(f"[{author}] \'{message}\'")

                    # execute game step
                    txt = game.step(message)
                    print2paper(txt, message, author)

                    # autosave
                    game.save()

                    sleep(3)

                except Empty:
                    print("...waiting for new messages...")

        except (TIMEOUT, EOF) as err:
            pass  # restart game if it crashes


def spool_messages():
    """
    Skip messages in the queue if queue gets too long, so the game play doesn't drag behind incoming chats too much
    """
    n = chat_queue.qsize()
    if n > QUEUE_LOOKBACK:
        skip_messages = n - QUEUE_LOOKBACK
        for _ in range(skip_messages):
            chat_queue.get_nowait()
        return skip_messages
    return 0


def print2paper(txt, cmd="", author=""):
    """
    Parse game output and send formatted text to printer
    """

    # print author and command
    if cmd:
        line = author[:13] + ".." if len(author) > 15 else author
        line += " > " if author else "> "
        line += cmd
        tsp_print(line, text_width=TEXT_WIDTH, cut=False)

    # walk through all lines of the game-text
    location = None
    for line in txt.split("\n"):
        # print game-text header with inversed colors
        if re.match(".+[S|Score]: -?\d+\s+[M|Moves]: -?\d+", line):
            location = re.findall(".*(?=[S|Score]:)", line)[0].strip()
            tsp_print(line, fg="#fff", bg="#000", text_width=TEXT_WIDTH, cut=False)
        # skip command & location echo
        elif line in [cmd, location]:
            continue
        # print game-text line
        else:
            tsp_print(line, text_width=TEXT_WIDTH, cut=False)

    # add empty lines for spacing and close connection
    tsp_print("\n"*2, text_width=TEXT_WIDTH, cut=True)


def main():
    """
    Start game-loop and run chat crawler 
    """

    try:
        game_loop_thread = Thread(target=game_loop)
        game_loop_thread.start()
        chat_crawler()
        game_loop_thread.join()

    finally:
        terminate_event.set()
        tsp_print("[stream lost]\n\n")


main()
