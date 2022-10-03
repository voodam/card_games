from enum import Enum
from functools import total_ordering
import util

@total_ordering
class Rank(Enum):
  Two = "2"
  Three = "3"
  Four = "4"
  Five = "5"
  Six = "6"
  Seven = "7"
  Eight = "8"
  Nine = "9"
  Ten = "10"
  Jack = "J"
  Queen = "Q"
  King = "K"
  Ace = "A"

  def __lt__(self, other):
    if self.__class__ is not other.__class__:
      return NotImplemented
    return list(Rank).index(self) < list(Rank).index(other)

  def __str__(self): return self.value
  def __repr__(self): return str(self)
  def to_json(self): return self.value
  def from_json(value): return Rank(value)

class Suit(Enum):
  Clubs = "♣"
  Hearts = "♥"
  Spades = "♠"
  Diamonds = "♦"

  def __str__(self): return self.value
  def __repr__(self): return str(self)
  def to_json(self): return self.name
  def from_json(name): return Suit[name]

class Card:
  """Don't create cards by your own, use c and card procedures instead."""

  def __init__(self, rank, suit):
    self.rank = rank
    self.suit = suit

  def __str__(self): return f"{self.suit}{self.rank}"
  def __repr__(self): return str(self)
  def to_json(self): return self.__dict__
  def from_json(d): return c(Rank.from_json(d["rank"]), Suit.from_json(d["suit"]))

full_deck_dict = {(rank, suit): Card(rank, suit) for rank in list(Rank) for suit in list(Suit)}

def c(rank, suit):
  return full_deck_dict[(rank, suit)]

def card(string):
  suit, rank, *tail = string
  if tail:
    rank_end, = tail
    rank += rank_end
    assert rank == "10"
  return c(Rank(rank), Suit(suit))

def deck_from(rank):
  return [c for c in full_deck_dict.values() if c.rank >= rank]

def deal(players, deck, hand_amount = None):
  players_number = len(players)
  if not hand_amount:
    assert len(deck) % players_number == 0
    hand_amount = len(deck) // players_number
  detach_from_player(deck)

  widdle = deck[hand_amount*players_number:]
  deck = deck[:hand_amount*players_number]
  hands = util.list_chunks(deck, players_number)

  for player, hand in zip(players, hands):
    attach_to_player(hand, player)
  return widdle

def attach_to_player(cards, player):
  cards = util.make_list(cards)
  if not hasattr(player, "cards"):
    player.cards = []

  player.cards.extend(cards)
  for card in cards:
    card.player = player

def detach_from_player(cards):
  cards = util.make_list(cards)
  for c in cards:
    if getattr(c, "player", None):
      c.player.cards.remove(c)
      c.player = None

