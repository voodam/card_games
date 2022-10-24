from argparse import ArgumentParser
import sys

from lib.util import Color
from logic.io import GameType
import logic.io
from logic.io.util import BoardObserver, board_after_reconnect
import logic.game
import logic.board
from logic.game.chess import *

parser = ArgumentParser(description="Chess")
logic.io.add_cli_args(parser)
args = parser.parse_args()

board = BoardObserver(logic.board.Board2D())
players = logic.io.new_players(2, game_type=GameType.BOARD, after_reconnect=board_after_reconnect(board), **vars(args))
board.init_players(players)
logic.game.assign_to_teams(players, team_colors=[Color.White, Color.Black])

chess = Chess(board)
chess.setup_board()

def move(player):
  while True:
    from_, to = player.io.select_move()
    piece = board.get_piece(from_)
    if logic.board.is_valid_move(chess, piece, to, player.team.color):
      break

  chess.move(piece, to)

  if chess.is_promotion(piece, to):
    piece_type = player.io.select_promotion([ChessPiece.Queen, ChessPiece.Knight])
    new_piece = logic.board.Piece(piece_type, player.team.color)
    logic.board.replace(board, to, new_piece)

while True:
  for player in players:
    move(player)

