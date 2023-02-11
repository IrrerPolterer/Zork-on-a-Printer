import pexpect
import os
from charset_normalizer import from_bytes
from os import environ

GAMEFILE = environ.get("GAME_FILE", "zork1.z5")
SAVEFILE = environ.get("SAVE_FILE", "zork1.sav")

game = None


def start(width=48, first_cmd="verbose"):
    """
    Start the game and return the initial output
    """
    global game

    if game != None:
        game.terminate()

    game = pexpect.spawn(
        f'bash -c "$(pwd)/dfrotz -p -w {width} $(pwd)/{GAMEFILE}"', timeout=5
    )

    if first_cmd:
        game.expect(">")
        game.sendline(first_cmd)

    game.expect(">")
    try:
        output = game.before.decode("utf-8").replace("\r", "").strip()
    except Exception:
        try:
            output = (
                str(from_bytes(game.before).best()).replace("\r", "").strip()
            )
        except Exception:
            output = "[ERROR] Oops, something broke. Let's try that again!"

    return output


def step(cmd):
    """
    Execute a game command and return the output
    """
    global game

    game.sendline(cmd)

    game.expect(">")
    try:
        output = game.before.decode("utf-8").replace("\r", "").strip()
    except Exception:
        try:
            output = (
                str(from_bytes(game.before).best()).replace("\r", "").strip()
            )
        except Exception:
            output = "[ERROR] Oops, something broke. Let's try that again!"

    return output


def restore():
    """
    Restore the game from a save file
    """
    global game

    if os.path.isfile(SAVEFILE):
        game.sendline("restore")
        game.expect(":")
        game.sendline(SAVEFILE)
        game.expect(">")
        if "Ok." in game.before.decode("UTF-8"):
            return True
    return False


def save():
    """
    Save game state to a file
    """
    global game

    game.sendline("save")
    game.expect(":")
    game.sendline(SAVEFILE)
    if (
        game.expect(["Overwrite existing file?", pexpect.TIMEOUT], timeout=0.5)
        == 0
    ):
        game.sendline("y")
    game.expect(">")
