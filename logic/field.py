from enum import Enum, auto
from itertools import chain
import contextlib
import math

from lib.util import Color, opposite_in_pair

class Field2D:
  def __init__(self, x_size = 8, y_size = 8, group_units_by = lambda p: p.color):
    self.x_size = x_size
    self.y_size = y_size
    self.underlying = [[None] * y_size for _ in range(x_size)]
    self.group_units_by = group_units_by
    self.units = {}

  def place(self, coords, unit, virtual = False):
    x, y = self._get_coords(coords)
    assert self.underlying[x][y] is None, coords
    assert not getattr(unit, "coords", None)

    self.underlying[x][y] = unit
    unit.coords = coords
    group = self.group_units_by(unit)
    self.units.setdefault(group, []).append(unit)

  def remove(self, coords, virtual = False):
    x, y = self._get_coords(coords)
    unit = self.underlying[x][y]
    assert unit, coords
    assert unit.coords, unit

    self.underlying[x][y] = None
    unit.coords = None
    group = self.group_units_by(unit)
    self.units[group].remove(unit)
    return unit

  def get_unit(self, coords):
    x, y = self._get_coords(coords)
    return self.underlying[x][y]

  def get_units_grouped(self):
    return self.units

  def _get_coords(self, coords):
    x, y = coords
    assert 0 <= x <= self.x_size - 1, x
    assert 0 <= y <= self.y_size - 1, y
    return x, y

def move(field, from_, to, virtual = False):
  unit = field.remove(from_, virtual)
  field.place(to, unit, virtual)

def replace(field, coords, unit, virtual = False):
  field.remove(coords, virtual)
  field.place(coords, unit, virtual)

def kill(field, from_, to, virtual = False):
  killed = field.remove(to, virtual)
  move(field, from_, to, virtual)
  return killed

def remove_if_placed(field, coords, virtual = False):
  if field.get_unit(coords):
    return field.remove(coords, virtual)
  return None

def kill_if_placed(field, from_, to, virtual = False):
  killed = remove_if_placed(field, to, virtual)
  move(field, from_, to, virtual)
  return killed

def get_units_all(field):
  return chain.from_iterable(field.get_units_grouped().values())

@contextlib.contextmanager
def move_virtually(field, from_, to):
  unit = remove_if_placed(field, to, virtual=True)
  move(field, from_, to, virtual=True)
  yield
  move(field, to, from_, virtual=True)
  if unit:
    field.place(to, unit, virtual=True)

class SegType(Enum):
  LINE = auto()
  DIAG = auto()
  NOT_SEGMENT = auto()

def get_segment_coords(from_, to):
  x1, y1 = from_
  x2, y2 = to

  if x1 == x2:
    if y2 < y1:
      y1, y2 = y2, y1
    return [[x1, y] for y in range(y1 + 1, y2)], SegType.LINE

  elif y1 == y2:
    if x2 < x1:
      x1, x2 = x2, x1
    return [[x, y1] for x in range(x1 + 1, x2)], SegType.LINE

  elif abs(x2 - x1) == abs(y2 - y1):
    if x2 < x1:
      x1, x2 = x2, x1
      y1, y2 = y2, y1
    sign = int(math.copysign(1, y2 - y1))
    return [[x1 + delta_x, y1 + sign * delta_x] for delta_x in range(1, x2 - x1)], SegType.DIAG

  return [], SegType.NOT_SEGMENT

def is_free_segment(segment, segtype):
  return segtype != SegType.NOT_SEGMENT and not list(filter(None, segment))

def get_segment_cells(field, from_, to):
  segment, segtype = get_segment_coords(from_, to)
  return map(field.get_unit, segment), segtype

class BlackWhitePieceType(Enum):
  def print(self, color):
    assert color in (Color.Black, Color.White)
    idx = 0 if color == Color.Black else 1
    return self.value[idx]

  def __str__(self): return self.print(Color.Black)
  def __repr__(self): return str(self)
  def to_json(self): return str(self)

  @classmethod
  def from_json(cls, pic):
    value = [p.value for p in list(cls) if p.value[0] == pic][0]
    return cls(value)

class Piece:
  def __init__(self, piece_type, color):
    self.type = piece_type
    self.color = color

  def __str__(self): return self.type.print(self.color)
  def __repr__(self): return str(self)
  def to_json(self): return str(self)

def is_valid_move(game, piece, to, color):
  return piece and piece.color == color and game.is_valid_move(piece, to)

def bw_enemy(color):
  return opposite_in_pair((Color.Black, Color.White), color)

