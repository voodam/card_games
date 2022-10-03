from board_game import BlackWhitePieceType

class CheckersPiece(BlackWhitePieceType):
  Man = ("⛂", "⛀")
  King = ("⛃", "⛁")

class Checkers:
  def __init__(self, board):
    self.board = board

  def setup_board(self):
    for x in range(0, 8, 2):
      for y in [0, 2]:
        self.board.place([x, y], Piece(CheckersPiece.Man, Color.Black))
      self.board.place([x, 6], Piece(CheckersPiece.Man, Color.White))

    for x in range(1, 8, 2):
      for y in [5, 7]:
        self.board.place([x, y], Piece(CheckersPiece.Man, Color.White))
      self.board.place([x, 1], Piece(CheckersPiece.Man, Color.Black))

  def _own_side_y(self, y, color):
    return y if color == Color.Black else 7 - y

