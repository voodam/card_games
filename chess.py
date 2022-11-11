from argparse import ArgumentParser
import sys

from lib.util import Color
from logic.io import GameType
import logic.io
from logic.io.util import FieldObserver, field_after_reconnect
import logic.game
import logic.field
from logic.game.chess import *

parser = ArgumentParser(description="Chess")
logic.io.add_cli_args(parser)
args = parser.parse_args()

board = FieldObserver(logic.field.Field2D())
players = logic.io.new_players(2, game_type=GameType.FIELD, after_reconnect=field_after_reconnect(board), **vars(args))
board.init_players(players)
logic.game.assign_to_teams(players, team_colors=[Color.White, Color.Black])

chess = Chess(board)
chess.setup_board()

def move(player):
  while True:
    from_, to = player.io.select_move()
    piece = board.get_unit(from_)
    if logic.field.is_valid_move(chess, piece, to, player.team.color):
      break

  chess.move(piece, to)

  if chess.is_promotion(piece, to):
    piece_type = player.io.select_promotion([ChessPiece.Queen, ChessPiece.Knight])
    new_piece = logic.field.Piece(piece_type, player.team.color)
    logic.field.replace(board, to, new_piece)

while True:
  for player in players:
    move(player)

