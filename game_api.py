import pexpect
import os


GAMEFILE = "zork1.z5"
SAVEFILE = "zork1.sav"

game = None


def start(width=48):
    """
    Start the game and return the initial output
    """
    global game
    
    if game != None:
        game.terminate()
    
    game = pexpect.spawn(f"bash -c \"$(pwd)/dfrotz -p -w {width} $(pwd)/{GAMEFILE}\"", timeout=5)

    game.expect(">")
    output = game.before.decode('utf-8').replace("\r", "").strip()

    return output


def step(cmd):
    """
    Execute a game command and return the output
    """
    global game
    
    game.sendline(cmd)

    game.expect(">")
    output = game.before.decode('utf-8').replace("\r", "").strip()

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


def save():
    """
    Save game state to a file
    """
    global game

    game.sendline("save")
    game.expect(":")
    game.sendline(SAVEFILE)
    if game.expect(["Overwrite existing file?", pexpect.TIMEOUT], timeout=0.5) == 0:
        game.sendline("y")
    game.expect(">")
