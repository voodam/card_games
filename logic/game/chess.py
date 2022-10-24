from itertools import chain

from lib.util import Color
import lib.list
from logic.board import BlackWhitePieceType, Piece, SegType, bw_enemy
import logic.board

class ChessPiece(BlackWhitePieceType):
  King = ("♚", "♔")
  Queen = ("♛", "♕")
  Rook = ("♜", "♖")
  Bishop = ("♝", "♗")
  Knight = ("♞", "♘")
  Pawn = ("♟", "♙")

class Chess:
  def __init__(self, board):
    self.board = board
    self.kings = {}
    self.last_double_step_pawn = {
      Color.White: None,
      Color.Black: None
    }
    self.is_en_passant_last = False
    self.unmoved_castlers = {}

  def is_valid_move(self, piece, to):
    color = piece.color
    target = self.board.get_piece(to)

    if target and target.color == color:
      return False

    with logic.board.move_virtually(self.board, piece.coords, to):
      if self.is_check(color):
        return False

    self.last_double_step_pawn[color] = None
    return self._is_valid_move_internal(piece, to)

  def _is_valid_move_internal(self, piece, to):
    color = piece.color
    target = self.board.get_piece(to)
    x1, y1 = piece.coords
    x2, y2 = to
    delta_x = abs(x2 - x1)
    abs_delta = {delta_x, abs(y2 - y1)}
    segment, segtype = logic.board.get_segment_cells(self.board, piece.coords, to)
    is_free_segment = logic.board.is_free_segment(segment, segtype)

    assert not target or target.color != color

    if piece.type == ChessPiece.Pawn:
      is_one_step = self._own_side_y(y2, color) == self._own_side_y(y1, color) + 1
      is_double_step = y1 == self._own_side_y(1, color) and y2 == self._own_side_y(3, color)

      if x1 == x2 and (is_one_step or is_double_step) and not target:
        if is_double_step:
          self.last_double_step_pawn[color] = piece
        return True

      cell = self.board.get_piece([x2, y1])
      is_en_passant = bool(cell) and cell == self.last_double_step_pawn[bw_enemy(color)]
      if delta_x == 1 and is_one_step and (target or is_en_passant):
        if is_en_passant:
          self.is_en_passant_last = True
        return True
      return False

    elif piece.type == ChessPiece.King:
      if abs_delta in ({0, 1}, {1}):
        self.unmoved_castlers[color] = []
        return True

      if piece in self.unmoved_castlers[color] and y1 == y2 and delta_x == 2:
        return self._is_valid_castling(piece, to)
      return False

    elif piece.type == ChessPiece.Rook:
      if segtype == SegType.LINE and is_free_segment:
        lib.list.remove_if_exists(self.unmoved_castlers[color], piece)
        return True
      return False

    return {
      ChessPiece.Bishop: segtype == SegType.DIAG and is_free_segment,
      ChessPiece.Queen: is_free_segment,
      ChessPiece.Knight: abs_delta == {1, 2}
    }[piece.type]

  def move(self, piece, to):
    logic.board.kill_if_placed(self.board, piece.coords, to)
    self._castling(piece.color)
    self._en_passant(piece)

  def _is_valid_castling(self, piece, to):
    x1, y1 = piece.coords
    x2 = to[0]
    color = piece.color

    rook_x = 0 if x1 > x2 else 7
    rook_y = self._own_side_y(0, color)
    rook = self.board.get_piece([rook_x, rook_y])
    if rook not in self.unmoved_castlers[color]:
      return False

    res = logic.board.get_segment_cells(self.board, piece.coords, [rook_x, rook_y])
    if logic.board.is_free_segment(*res):
      return False
    
    cross_cell_x = x1 - 1 if x1 > x2 else x1 + 1
    if self.is_check(color) or self.is_under_attack(color, [cross_cell_x, y1]):
      return False

    self.unmoved_castlers[color] = [rook]
    return True

  def _castling(self, color):
    if len(self.unmoved_castlers[color]) != 1:
      return

    rook = self.unmoved_castlers.pop(color)
    x, y = rook.coords
    x2 = 3 if x == 0 else 5

    logic.board.move(self.board, rook.coords, [x2, y])

  def _en_passant(self, piece):
    if not self.is_en_passant_last:
      return

    enemy_color = bw_enemy(piece.color)
    pawn = self.last_double_step_pawn[enemy_color]
    assert pawn and pawn.type == ChessPiece.Pawn

    self.board.remove(pawn.coords)
    self.is_en_passant_last = False
    self.last_double_step_pawn[enemy_color] = None

  def is_under_attack(self, color, coords):
    enemy_pieces = self.board.get_pieces_grouped()[bw_enemy(color)]
    return any(p for p in enemy_pieces if p.coords and self._is_valid_move_internal(p, coords))

  def is_check(self, color):
    king = self.kings[color]
    return self.is_under_attack(color, king.coords)

  def is_promotion(self, piece, to):
    return piece.type == ChessPiece.Pawn and to[1] == self._own_side_y(7, piece.color)

  def setup_board(self):
    def setup_higher(color):
      y = self._own_side_y(0, color)
      rook1 = Piece(ChessPiece.Rook, color)
      self.board.place([0, y], rook1)
      rook2 = Piece(ChessPiece.Rook, color)
      self.board.place([7, y], rook2)
      self.board.place([1, y], Piece(ChessPiece.Knight, color))
      self.board.place([6, y], Piece(ChessPiece.Knight, color))
      self.board.place([2, y], Piece(ChessPiece.Bishop, color))
      self.board.place([5, y], Piece(ChessPiece.Bishop, color))
      self.board.place([3, y], Piece(ChessPiece.Queen, color))
      king = Piece(ChessPiece.King, color)
      self.board.place([4, y], king)

      self.kings[color] = king
      self.unmoved_castlers[color] = [king, rook1, rook2]

    for i in range(8):
      self.board.place([i, 1], Piece(ChessPiece.Pawn, Color.White))
      self.board.place([i, 6], Piece(ChessPiece.Pawn, Color.Black))
    setup_higher(Color.White)
    setup_higher(Color.Black)

  def _own_side_y(self, y, color):
    return y if color == Color.White else 7 - y

