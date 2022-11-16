from enum import Enum, Flag, auto

class Cell:
  def __init__(self):
    self.coords
    self.unit
    self.terrain
    self.spice_amount

class Terrain(Enum):
  SAND = auto()
  DESERT = auto()
  ROCK = auto()
  MOUNTAIN = auto()

class House(Flag):
  ATREIDES = auto()
  HARKONNEN = auto()
  ORDOS = auto()
  IMPERATOR = auto()
  ALL = ATREIDES | HARKONNEN | ORDOS | IMPERATOR

