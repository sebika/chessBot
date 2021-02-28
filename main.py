import chess
import chess.engine

from selenium import webdriver

import os
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s\n")

from constants import *

if __name__ == '__main__':

    # Init the browser
    driver = webdriver.Firefox(executable_path='/usr/bin/geckodriver')
    driver.get('https://chess.com')
    driver.implicitly_wait(5)
    driver.maximize_window()

    # Close annoying cookie messages
    driver.find_element_by_xpath("//button[@class='close svelte-t5zni7']").click()
    logging.info("Cookie message closed")

    # Login the user
    driver.find_element_by_xpath("//a[@class='button auth login']").click()
    logging.info("Clicked login button")

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

    try:
        driver.find_element_by_xpath("//a[text()='Skip Trial']").click()
        logging.info('Closed Trial advertisement')
    except:
        logging.info('No trial advertisement')

    # Play a new game
    driver.get('https://www.chess.com/play/online')
    driver.find_element_by_xpath("//div[@class='new-game-index-selector']").click()
    driver.find_element_by_xpath(f"//button[text()='{GAMEMODE}']").click()
    logging.info("Gamemode selected")


    # engine = chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish')

    # board = chess.Board()

    # result = engine.play(board, chess.engine.Limit(time=0.1))
    # board.push(result.move)
    # print(board, end='\n\n')

    # opponent_move = board.parse_san('Na6')
    # board.push(opponent_move)
    # print(board, end='\n\n')

    # engine.quit()
