from pytchat import create
from threading import Thread, Event
from queue import Queue, Empty
from sys import argv
from escpos.printer import Network, Dummy
from pexpect import TIMEOUT, EOF
import re

import game_api as game

VIDEO_ID = argv[1] if len(argv) > 1 else "HyzaQ3npd4U"
QUEUE_LOOKBACK = 10
PRINTER_ADDRESS = "10.0.0.51"


chat_queue = Queue()
terminate_event = Event()


def chat_crawler():

    chat = create(video_id=VIDEO_ID)
    while chat.is_alive() and not terminate_event.is_set():
        for c in chat.get().sync_items():
            chat_queue.put((c.author.name, c.message))

    terminate_event.set()


def game_loop():

    while not terminate_event.is_set():
        try:

            return game_run()
        
        except (TIMEOUT, EOF) as err:
            pass # restart game if it crashes


def game_run():
    
    txt = game.start()
    print_formatted(txt)
    
    game.restore()

    while not terminate_event.is_set():
        try:
            n = spool_messages()
            if n > 0:
                print(f"...skipping {n} messages...")

            author, message = chat_queue.get(timeout=5)
            print(f"[{author}] \'{message}\' ")

            txt=game.step(message)
            print_formatted(txt, message, author)
            
            game.save()
            

        except Empty:
            print("...no new messages...")
            pass
    return


def spool_messages():

    # skip messages if queue gets too long
    n = chat_queue.qsize()
    if n > QUEUE_LOOKBACK:
        skip_messages = n - QUEUE_LOOKBACK
        for _ in range(skip_messages):
            chat_queue.get_nowait()
        return skip_messages
    return 0


def print_formatted(txt, cmd="", author=""):
    """
    Parse game output and send formatted text to printer
    """
    #n = Network(PRINTER_ADDRESS)
    n = Dummy()
    
    if cmd:
        line = author[:13] + ".." if len(author)>15 else author
        line += " " if author else ""
        n.set()
        n.text(line)
        line = "> " + cmd + "\n"
        n.set(bold=True)
        n.text(line)
    
    location = None
    for line in txt.split("\n"):
        n.set()
        if re.match(".+[S|Score]: \d+\s+[M|Moves]: \d+", line):
            location = re.findall(".*(?=[S|Score]:)", line)[0].strip()
            n.set(invert=True)
        if line in [cmd, location]:
            continue
        n.text(line + "\n")

    n.close()


def main():

    try:
        game_loop_thread = Thread(target=game_loop)
        game_loop_thread.start()
        chat_crawler()
        game_loop_thread.join()

    except KeyboardInterrupt:
        terminate_event.set()


main()
