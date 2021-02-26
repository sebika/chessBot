from selenium import webdriver
import chess
import chess.engine

if __name__ == "__main__":

    # engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")

    # board = chess.Board()

    # result = engine.play(board, chess.engine.Limit(time=0.1))
    # board.push(result.move)
    # print(board, end="\n\n")

    # opponent_move = board.parse_san('Na6')
    # board.push(opponent_move)
    # print(board, end="\n\n")

    # engine.quit()

    browser = webdriver.Firefox(executable_path="/usr/bin/geckodriver")
    browser.get("https://google.com")