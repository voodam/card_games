import json
from enum import Enum, auto

class Color(Enum):
  Black = auto()
  White = auto()

class TextColor(Enum):
  Black = 30
  Red = 31
  Green = 32
  Yellow = 33
  Blue = 34
  Magenta = 35
  Cyan = 36
  White = 37

  def __str__(self): return str(self.value)

class TextStyle(Enum):
  Nothing = 0
  Bold = 1
  Weak = 2
  Italic = 3
  Underscore = 4
  Blink = 5
  ReverseColor = 7
  Concealed = 8
  Strike = 9

  def __str__(self): return str(self.value)

def colored(text, color, style = TextStyle.Nothing):
  return f"\33[{style};{color}m{text}\33[m"

def opposite_in_pair(pair, obj):
  assert len(pair) == 2
  return pair[1] if pair[0] == obj else pair[0]

def dict_merge(*dicts):
  res = {}
  for d in dicts:
    res.update(d)
  return res

def json_dumps(obj):
  def f(v):
    if isinstance(v, set):
      return list(v)
    else:
      return v.to_json()

  return json.dumps(obj, default=f)

