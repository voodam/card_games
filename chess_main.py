import argparse
import sys
import logging
import player_io
from player_io import GameType
import game_io
import gaming
from util import Color
import board_game
from chess import Chess, ChessPiece

parser = argparse.ArgumentParser(description="Chess")
player_io.add_cli_args(parser)
args = parser.parse_args()

board = game_io.BoardObserver(board_game.Board2D())
players = player_io.new_players(2, game_type=GameType.BOARD, after_reconnect=game_io.board_after_reconnect(board), **vars(args))
board.init_players(players)
gaming.assign_to_teams(players, team_colors=[Color.White, Color.Black])

chess = Chess(board)
chess.setup_board()

def move(player):
  while True:
    from_, to = player.io.select_move()
    piece = board.get_piece(from_)
    if board_game.is_valid_move(chess, piece, to, player.team.color):
      break

  chess.move(piece, to)

  if chess.is_promotion(piece, to):
    piece_type = player.io.select_promotion([ChessPiece.Queen, ChessPiece.Knight])
    new_piece = board_game.Piece(piece_type, player.team.color)
    board_game.replace(board, to, new_piece)

while True:
  for player in players:
    move(player)

