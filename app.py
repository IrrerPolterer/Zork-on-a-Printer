import re
from distutils import text_file
from queue import Empty, Queue
from sys import argv
from threading import Event, Thread
from time import sleep

from pexpect import EOF, TIMEOUT
from pytchat import create

import game_api as game
from printer_api import tsp_print

VIDEO_ID = argv[1] if len(argv) == 2 else None
FONT = "Meslo LG L Bold Nerd Font Complete Mono.ttf"
TEXT_WIDTH = 42

FORBIDDEN_CMDS = [
    "",
    "save",
    "restore",
    "restart",
    "reboot",
    "quit",
    "verbose",
    "brief",
    "superbrief",
]

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


def local_input():
    """
    Read local input as an alternative to YT chat
    """

    while not terminate_event.is_set():
        chat_queue.put(("[LOCAL PLAYER]", input().strip()))

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
                    # retrieve latest commands from queue
                    spool_messages()
                    author, message = chat_queue.get(timeout=10)

                    if message.strip() not in FORBIDDEN_CMDS:
                        # execute game step
                        txt = game.step(message)
                        if (not f"I don't know the word" in txt) and (
                            not f"There was no verb in that sentence!" in txt
                        ):
                            print2paper(txt, message, author)
                            # autosave
                            game.save()
                            # pace the game
                            sleep(3)
                    else:
                        print()

                except Empty:
                    print("...waiting for new messages...")

        except (TIMEOUT, EOF) as err:
            pass  # restart game if it crashes


def spool_messages():
    """
    Skip queue ahead to the latest message
    """
    n = chat_queue.qsize()
    if n > 1:
        print(f"...skipping {n-1} messages...")
        for _ in range(n - 1):
            chat_queue.get_nowait()


def print2paper(txt, cmd="", author=""):
    """
    Parse game output and send formatted text to printer
    """

    # print author and command
    if cmd:
        line = author[:13] + ".." if len(author) > 15 else author
        line += " > " if author else "> "
        line += cmd
        try:
            print(line)
            tsp_print(
                line,
                text_width=TEXT_WIDTH,
                cut=False,
                font_path=FONT,
            )
        except Exception:
            author = author or "someone"
            tsp_print(
                f"[ERROR] Whoopsie, {author} broke something! Let's try that again, shall we?",
                text_width=TEXT_WIDTH,
                cut=False,
                font_path=FONT,
            )

    # walk through all lines of the game-text
    location = None
    for line in txt.split("\n"):
        # print game-text header with inversed colors
        if re.match(".+[S|Score]: -?\d+\s+[M|Moves]: -?\d+", line):
            location = re.findall(".*(?=[S|Score]:)", line)[0].strip()
            print(line)
            tsp_print(
                line,
                fg="#fff",
                bg="#000",
                text_width=TEXT_WIDTH,
                cut=False,
                font_path=FONT,
            )
        # skip command & location echo
        elif line in [cmd, location]:
            continue
        # print game-text line
        else:
            print(line)
            tsp_print(
                line,
                text_width=TEXT_WIDTH,
                cut=False,
                font_path=FONT,
            )

    # add empty lines for spacing and close connection
    tsp_print("\n" * 2, text_width=TEXT_WIDTH, cut=True)


def main():
    """
    Start game-loop and run chat crawler
    """

    try:
        game_loop_thread = Thread(target=game_loop)
        game_loop_thread.start()
        local_input_thread = Thread(target=local_input)
        local_input_thread.start()
        if VIDEO_ID:
            chat_crawler()
        game_loop_thread.join()

    finally:
        terminate_event.set()
        tsp_print("[stream lost]\n\n")


main()
