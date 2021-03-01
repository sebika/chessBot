import chess
import chess.engine

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pyautogui as gui

import os
import re
from time import sleep
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")

from constants import *

def check_resign_or_timeout():
    try:
        driver.find_element_by_xpath(f"//*[text()='You Won!']")
        logging.info("Yey I won :)")
        return "WON"
    except:
        pass

    try:
        driver.find_element_by_xpath(f"//*[text()='You Lost!']")
        logging.info("Nooo I lost ;(")
        return "LOST"
    except:
        pass

    return "Not ended"

def play_one_game():
    # Select gamemode
    driver.get('https://www.chess.com/play/online')
    sleep(TIMEOUT)

    try:
        driver.find_element_by_xpath("//a[@class='board-modal-header-close icon-font-chess x']").click()
        logging.info("Closed last game summary banner")
    except:
        logging.info("No last game summary")
    driver.find_element_by_xpath(f"//span[text()='New Game']").click()
    driver.find_element_by_xpath("//div[@class='new-game-index-selector']").click()
    driver.find_element_by_xpath(f"//button[text()='{GAMEMODE}']").click()
    logging.info("Gamemode selected")

    last_game_url = ''
    if re.match("https://www.chess.com/game/live/[0-9]+", driver.current_url):
        last_game_url = driver.current_url

    # Play a game
    driver.find_element_by_xpath(
        "//button[@class='ui_v5-button-component ui_v5-button-primary ui_v5-button-large ui_v5-button-full']"
    ).click()

    # Scroll to the top of the page
    driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)

    # Wait until the new game is found
    while(True):
        if (driver.current_url != last_game_url and
            re.match("https://www.chess.com/game/live/[0-9]+", driver.current_url)):
            break

        logging.info("Waiting for a game to start !")
        sleep(1)

    logging.info("Match found !")

    # Find if you have white or black pieces
    white_rook = driver.find_element_by_xpath("//div[@class='piece wr square-11']")
    bot_color = 'WHITE'
    if white_rook.location['y'] < window_size['height'] / 2:
        bot_color = 'BLACK'
    logging.info(f'You are playing as: {bot_color}')

    # Get coodinates of the squares
    pos = []
    for i in range(9):
        pos.append(9 * [(-1, -1)])

    white_rook = driver.find_element_by_xpath("//div[@class='piece wr square-11']")
    square_width = white_rook.rect['width']
    pos[1][1] = (white_rook.rect['x'] + square_width/2, white_rook.rect['y'] + 1.5*square_width)

    for line in range(1, 9):
        for col in range(1, 9):
            if not (line == 1 and col == 1):
                if bot_color == 'WHITE':
                    if col != 1:
                        pos[line][col] = (pos[line][col-1][0] + square_width, pos[line][col-1][1])
                    else:
                        pos[line][col] = (pos[line-1][col][0], pos[line-1][col][1] - square_width)
                elif bot_color == 'BLACK':
                    if col != 1:
                        pos[line][col] = (pos[line][col-1][0] - square_width, pos[line][col-1][1])
                    else:
                        pos[line][col] = (pos[line-1][col][0], pos[line-1][col][1] + square_width)

    # transpose the matrix
    for line in range(1, 9):
        for col in range(line, 9):
            aux = pos[line][col]
            pos[line][col] = pos[col][line]
            pos[col][line] = aux


    engine = chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish')
    board = chess.Board()
    no_moves = 0
    moves = []

    # If the bot is black he needs to wait for the opponent to make a move
    print('===')
    if bot_color == 'BLACK':
        while no_moves == len(moves):
            moves = driver.find_elements_by_xpath("//div[@class='move']")
        opponent_move = moves[0].text.split("\n")[1]
        opponent_move = board.push_san(opponent_move)
        logging.info(f"Opponent moved: {opponent_move.uci()}")
        no_moves += 1

    while(True):
        bot_move = engine.play(board, chess.engine.Limit(time=0.1))
        board.push(bot_move.move)

        bot_move_uci = bot_move.move.uci()
        from_square = bot_move_uci[:2]
        to_square = bot_move_uci[2:]

        gui.moveTo(pos[ord(from_square[0]) - ord('a') + 1][int(from_square[1])])
        sleep(0.1)
        gui.click()
        sleep(0.1)
        gui.moveTo(pos[ord(to_square[0]) - ord('a') + 1][int(to_square[1])])
        sleep(0.1)
        gui.click()

        logging.info(f"Bot moved: {bot_move.move}")
        if bot_color == 'BLACK':
            print('===')

        end_game_result = check_resign_or_timeout()
        if end_game_result != "Not ended":
            engine.close()
            return end_game_result

        if board.is_game_over():
            logging.info("Yey I won")
            engine.close()
            return "WON"

        # wait for the opponent to make a move
        if bot_color == 'BLACK':
            while no_moves == len(moves):
                moves = driver.find_elements_by_xpath("//div[@class='move']")
                end_game_result = check_resign_or_timeout()
                if end_game_result != "Not ended":
                    engine.close()
                    return end_game_result

            opponent_move = moves[-1].text.split("\n")[1]
        else:
            while(True):
                moves = driver.find_elements_by_xpath("//div[@class='move']")
                try:
                    opponent_move = moves[-1].text.split("\n")[3]
                    break
                except:
                    pass
                end_game_result = check_resign_or_timeout()
                if end_game_result != "Not ended":
                    engine.close()
                    return end_game_result

        opponent_move = board.push_san(opponent_move)
        logging.info(f"Opponent moved: {opponent_move.uci()}")
        if bot_color == 'WHITE':
            print('===')
        no_moves += 1

if __name__ == '__main__':

    # Init the browser
    driver = webdriver.Firefox(executable_path='/usr/bin/geckodriver')
    driver.get('https://www.chess.com/login_and_go?returnUrl=https%3A%2F%2Fwww.chess.com%2F')
    window_size = driver.get_window_size()

    # Close annoying cookie messages
    driver.find_element_by_xpath("//button[@class='close svelte-t5zni7']").click()
    logging.info("Cookie message closed")

    # Login the user
    # driver.find_element_by_xpath("//a[@class='button auth login']").click()
    # logging.info("Clicked login button")

    username = driver.find_element_by_id('username')
    username.send_keys(os.environ['USER'])
    password = driver.find_element_by_id('password')
    password.send_keys(os.environ['PASSWORD'])
    logging.info('Filled the credentials')

    driver.find_element_by_id('login').click()

    if driver.current_url != 'https://www.chess.com/home':
        logging.critical('There was a problem with the authentication')
        exit(-1)
    logging.info('Logged in successfully !')

    # Close annoying trial messages
    try:
        driver.find_element_by_xpath("//a[text()='Skip Trial']").click()
        logging.info('Closed Trial advertisement')
    except:
        logging.info('No trial advertisement')

    play_one_game()
    play_one_game()

    # driver.close()

