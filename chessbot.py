import chess
import json
from enum import Enum

def get_help():
    return '"!chess <names...>" to start a new game with the specified participants.\n'\
            '"!chess board" to show the current board. \n'\
            '"!chess takeback" to undo the last move. \n'\
            '"!chess takeback <number>" to undo the last N moves. \n'\
            '"!chess <move>" to make a move specified in standard algebraic notation. \n'\
            '"!chess help" to show this help information. \n'\
            '"!game stop" to stop game.'


class GameState(Enum):
    stop = 0
    started = 1

class Game:
    def __init__(self):
        json_savestate = self.load_saved_state()
        if json_savestate:
            self.board = chess.Board(json_savestate["fen"])
            self.players = json_savestate["players"]
            self.gamestate = GameState(json_savestate["gamestate"])
        else:
            self.board = chess.Board()
            self.gamestate = GameState.stop

    def load_saved_state(self):
        try:
            f = open("chessboardsave.txt", "r")
            json_savestate = json.load(f)
        except FileNotFoundError:
            return None
            
        f.close()
        return json_savestate

    def save_state(self):
        json_savestate = dict()
        json_savestate["players"] = self.players
        json_savestate["fen"] = self.board.fen()
        json_savestate["gamestate"] = self.gamestate.value
        with open("chessboardsave.txt", "w") as f:
            f.write(json.dumps(json_savestate))

    def set_participants(self, players):
        self.players = players

    def start_game(self):
        self.board.reset()

    def get_current_player(self):
        return self.players[0] if self.board.turn == chess.WHITE else self.players[1]

    def show_board(self):
        try:
            last_move = self.board.peek().uci()
        except:
            last_move = None

        fen = self.board.fen().split()[0]
        turn = "White" if self.board.turn == chess.WHITE else "Black"
        flip = "-flip" if self.board.turn == chess.BLACK else ""
        response = "{} ({}) to move".format(self.get_current_player(), turn)
        if last_move: response += ", last move was {}".format(last_move)
        response += ": https://chessboardimage.com/{}{}.png".format(fen, flip)
        return response

    def finish_game(self):
        response = ""
        if self.board.is_checkmate():
            response += "Checkmate!\n"
        if self.board.is_stalemate():
            response += "Stalemate!\n"
        if self.board.is_insufficient_material():
            response += "Draw by insufficient material\n"

        winner = self.players[0] if self.board.result() == "1-0" else None
        winner = self.players[1] if self.board.result() == "0-1" else None
        response += "Game result: {}\n".format(self.board.result())
        if winner: 
            response += "The winner is {}!".format(winner)
        return response

    def elaborate_query(self, sender, query):

        query = query.split()
        command = query[0] if len(query) > 0 else ""
        params = query[1:]

        if command == "stop":
            self.gamestate = GameState.stop
            response = "Game stopped"
        elif command == "help":
            response = get_help()
        elif self.gamestate == GameState.stop:
            if len(query) >= 2:
                self.set_participants(query)
                self.start_game()
                response = "Chess game started, GLHF! {}".format(self.show_board())
                self.gamestate = GameState.started
            else:
                response = "Type the names of the two participants separated by space (!chess <names...>): "
        elif self.gamestate == GameState.started:
            if command == "board":
                response = self.show_board()
            elif command == "takeback":
                number_takebacks = 1
                if len(params)>0:
                    number_takebacks = int(params[0])
                for _ in range(number_takebacks):
                    self.board.pop()
                response = self.show_board()
                self.save_state()
            elif sender == self.get_current_player():
                try:
                    move = self.board.push_san(command)
                    response = self.show_board()
                except ValueError:
                    response = "Illegal move\n"

                if self.board.is_game_over():
                    response += "\n"
                    response += self.finish_game()
                    self.gamestate = GameState.stop

                self.save_state()
            else:
                response = "{}, it's not your turn!!".format(sender)
                
        return response