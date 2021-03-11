import argparse

from constants import DEFAULT_GAMEMODE
from bot import ChessBot
from logger import Logger


if __name__ == "__main__":
    # Initiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-G",
        "--gamemode",
        type=str,
        help="Select the gamemode you want to play",
    )
    args = parser.parse_args()

    # Init the logger
    logger = Logger().get_logger()

    # Login to an account
    chessBot = ChessBot()
    chessBot.login_client()
    chessBot.close_site_cookies_message()

    gamemode = args.gamemode if args.gamemode else DEFAULT_GAMEMODE

    while(True):
        chessBot.select_gamemode(gamemode)
        chessBot.find_new_game()
        logger.info(f"End game result: {chessBot.play_game()}\n")
        chessBot.end_game_teardown()

