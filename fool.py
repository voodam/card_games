import playing_cards
from playing_cards import Rank
from card_game import CardGame
import card_game
import util

class Fool(CardGame):
  def __init__(self, players_number):
    CardGame.__init__(self, playing_cards.deck_from(Rank.Six), players_number)

  def allowed_cards(self, _, __, ___):
     raise NotImplementedError()

class TrickCards:
  def __init__(self, underlying = None):
    if not underlying:
      underlying = {}
    self.underlying = underlying

  def add_unbeaten(self, cards):
    cards = util.make_list(cards)
    self.underlying.update({c: None for c in cards})

  def get_unbeaten(self):
    return [c for c in self.underlying if not self.underlying[c]]

  def get_all(self):
    return list(self.underlying) + [c for c in self.underlying.values() if c is not None]

  def beat(self, target, hit_card):
    assert target in self.underlying
    self.underlying[target] = hit_card

def attacker_cards(player, trick_cards):
  put_cards = trick_cards.get_all()

  if not put_cards:
    return player.cards
  else:
    put_ranks = {c.rank for c in put_cards}
    return [c for c in player.cards if c.rank in put_ranks]

def defender_cards(game, player, trick_cards, trump):
  unbeaten_cards = trick_cards.get_unbeaten()
  return [c for c in player.cards if card_game.can_hit_any(game, c, unbeaten_cards, trump)]

def beat(game, hit_card, trick_cards, trump):
  unbeaten_cards = trick_cards.get_unbeaten()
  sorted_cards = reversed(card_game.sort_by_rank_suit(game, unbeaten_cards, trump))

  for c in sorted_cards:
    if card_game.can_hit(game, hit_card, c, trump):
      trick_cards.beat(c, hit_card)
      return c
  assert False, "No cards to beat available"

def replenish_cards(player_cards, deck):
  need_cards = 6 - len(player_cards)
  if need_cards <= 0:
    return []
  cards = deck[:need_cards]
  deck[:] = deck[need_cards:]
  return cards

