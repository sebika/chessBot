import os
import re
import chess
import chess.engine
import pyautogui as gui

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep

from logger import Logger
from constants import *


class ChessBot:
    def __init__(self):
        self.init_firefox_driver()
        self.init_chess_engine()

        self.logger = Logger().get_logger()
        self.engine = chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish')
        self.board = chess.Board()


    def init_firefox_driver(self):
        ''' Init the browser '''
        self.driver = webdriver.Firefox(executable_path='/usr/bin/geckodriver')
        self.window_size = self.driver.get_window_size()


    def init_chess_engine(self):
        self.engine.configure({"Minimum Thinking Time": 10})    # 0 - 500
        self.engine.configure({"Slow Mover": 10})               # 10 - 1000
        self.engine.configure({"Threads": 1})
        self.engine.configure({"UCI_Elo": 2000})                # 1350 - 2850


    def end_game_teardown(self):
        self.board.reset_board()


    def teardown(self):
        self.engine.close()
        self.driver.close()


    def close_site_cookies_message(self):
        self.driver.find_element_by_xpath("//button[@class='close svelte-t5zni7']").click()
        self.logger.info("Cookie message closed")


    def close_site_trial_message(self):
        try:
            self.driver.find_element_by_xpath("//a[text()='Skip Trial']").click()
            self.logger.info('Closed Trial advertisement')
        except:
            self.logger.info('No trial advertisement')


    def login_client(self):
        self.driver.get('https://www.chess.com/login_and_go?returnUrl=https%3A%2F%2Fwww.chess.com%2F')
        username = self.driver.find_element_by_id('username')
        username.send_keys(os.environ['USER'])
        password = self.driver.find_element_by_id('password')
        password.send_keys(os.environ['PASSWORD'])
        self.logger.info('Filled the credentials')

        self.driver.find_element_by_id('login').click()
        self.logger.info('Logging in')

        if self.driver.current_url != 'https://www.chess.com/home':
            self.logger.critical('There was a problem with the authentication')
            exit(-1)
        self.logger.info('Logged in successfully !')


    def check_resign_or_timeout(self):
        try:
            self.driver.find_element_by_xpath(f"//*[text()='You Won!']")
            self.logger.info("Yey I won :)")
            return "WON"
        except:
            pass

        try:
            self.driver.find_element_by_xpath(f"//*[text()='You Lost!']")
            self.logger.info("Nooo I lost ;(")
            return "LOST"
        except:
            pass

        return "Not ended"


    def select_gamemode(self, gamemode):
         # Select gamemode
        self.driver.get('https://www.chess.com/play/online')

        try:
            self.driver.find_element_by_xpath("//a[@class='board-modal-header-close icon-font-chess x']").click()
            self.logger.info("Closed last game summary banner")
        except:
            self.logger.info("No last game summary")

        self.driver.find_element_by_xpath(f"//span[text()='New Game']").click()
        self.driver.find_element_by_xpath("//div[@class='new-game-index-selector']").click()
        self.driver.find_element_by_xpath(f"//button[text()='{gamemode}']").click()
        self.logger.info("Gamemode selected")


    def find_new_game(self):
        last_game_url = ''
        if re.match("https://www.chess.com/game/live/[0-9]+", self.driver.current_url):
            last_game_url = self.driver.current_url

        self.driver.find_element_by_xpath(
            "//button[@class='ui_v5-button-component ui_v5-button-primary ui_v5-button-large ui_v5-button-full']"
        ).click()

        # Scroll to the top of the page
        self.driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)

        # Wait until the new game is found
        while(True):
            if (self.driver.current_url != last_game_url and
                re.match("https://www.chess.com/game/live/[0-9]+", self.driver.current_url)):
                break

            self.logger.info("Waiting for a game to start !")
            sleep(1)

        self.logger.info("Match found !")


    def find_bot_color(self):
        # Find if you have white or black pieces
        white_rook = self.driver.find_element_by_xpath("//div[@class='piece wr square-11']")
        self.bot_color = 'WHITE'
        if white_rook.location['y'] < self.window_size['height'] / 2:
            self.bot_color = 'BLACK'
        self.logger.info(f'You are playing as: {self.bot_color}')


    def find_squares_coordinates(self):
        # Get coodinates of the squares
        self.pos = []
        for i in range(9):
            self.pos.append(9 * [(-1, -1)])

        white_rook = self.driver.find_element_by_xpath("//div[@class='piece wr square-11']")
        square_width = white_rook.rect['width']
        self.pos[1][1] = (white_rook.rect['x'] + square_width/2, white_rook.rect['y'] + 1.5*square_width)

        for line in range(1, 9):
            for col in range(1, 9):
                if not (line == 1 and col == 1):
                    if self.bot_color == 'WHITE':
                        if col != 1:
                            self.pos[line][col] = (self.pos[line][col-1][0] + square_width, self.pos[line][col-1][1])
                        else:
                            self.pos[line][col] = (self.pos[line-1][col][0], self.pos[line-1][col][1] - square_width)
                    elif self.bot_color == 'BLACK':
                        if col != 1:
                            self.pos[line][col] = (self.pos[line][col-1][0] - square_width, self.pos[line][col-1][1])
                        else:
                            self.pos[line][col] = (self.pos[line-1][col][0], self.pos[line-1][col][1] + square_width)

        # transpose the matrix
        for line in range(1, 9):
            for col in range(line, 9):
                aux = self.pos[line][col]
                self.pos[line][col] = self.pos[col][line]
                self.pos[col][line] = aux


    def play_game(self):
        self.find_bot_color()
        self.find_squares_coordinates()

        no_moves = 0
        moves = []

        # If the bot is black he needs to wait for the opponent to make a move
        print(SEPARATOR)
        if self.bot_color == 'BLACK':
            while no_moves == len(moves):
                moves = self.driver.find_elements_by_xpath("//div[@class='move']")
            opponent_move = moves[0].text.split("\n")[1]
            opponent_move = self.board.push_san(opponent_move)
            self.logger.info(f"Opponent moved: {opponent_move.uci()}")
            no_moves += 1

        while(True):
            bot_move = self.engine.play(self.board, chess.engine.Limit(time=0.1))
            self.board.push(bot_move.move)

            bot_move_uci = bot_move.move.uci()
            from_square = bot_move_uci[:2]
            to_square = bot_move_uci[2:]

            gui.moveTo(self.pos[ord(from_square[0]) - ord('a') + 1][int(from_square[1])])
            gui.click()

            gui.moveTo(self.pos[ord(to_square[0]) - ord('a') + 1][int(to_square[1])])
            gui.click()

            self.logger.info(f"Bot moved: {bot_move.move}")
            if self.bot_color == 'BLACK':
                print(SEPARATOR)

            end_game_result = self.check_resign_or_timeout()
            if end_game_result != "Not ended":
                return end_game_result

            if self.board.is_game_over():
                return "WON"

            # wait for the opponent to make a move
            if self.bot_color == 'BLACK':
                while no_moves == len(moves):
                    moves = self.driver.find_elements_by_xpath("//div[@class='move']")
                    end_game_result = self.check_resign_or_timeout()
                    if end_game_result != "Not ended":
                        return end_game_result

                opponent_move = moves[-1].text.split("\n")[1]
            else:
                while(True):
                    moves = self.driver.find_elements_by_xpath("//div[@class='move']")
                    try:
                        opponent_move = moves[-1].text.split("\n")[3]
                        break
                    except:
                        pass
                    end_game_result = self.check_resign_or_timeout()
                    if end_game_result != "Not ended":
                        return end_game_result

            opponent_move = self.board.push_san(opponent_move)

            self.logger.info(f"Opponent moved: {opponent_move.uci()}")
            if self.bot_color == 'WHITE':
                print(SEPARATOR)

            no_moves += 1
