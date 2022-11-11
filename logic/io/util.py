from logic.io import EvtType, send_event_all
import logic.cards
from logic.cardgame import sort_by_rank_suit
import logic.field

def deal(players, game, hand_amount = None):
  widdle = logic.cards.deal(players, game.deck, hand_amount)
  for p in players:
    p.cards = sort_by_rank_suit(game, p.cards)
    p.io.send_event(EvtType.DEAL, p.cards)
  return widdle

def attach_cards(player, cards):
  logic.cards.attach_to_player(cards, player)
  player.io.send_event(EvtType.DEAL, player.cards)

def select_card(player, allowed_cards, detached = False):
  card = player.io.select_card(allowed_cards)
  if detached:
    logic.cards.detach_from_player(card)
  return card

def put_card_on_table(player, players, allowed_cards, detached = False):
  card = select_card(player, allowed_cards, detached)
  send_event_all(players, EvtType.CARD, {"card": card, "from": player})
  return card

class FieldObserver:
  def __init__(self, underlying, players = []):
    self.underlying = underlying
    self.init_players(players)

  def init_players(self, players):
    self.players = players

  def place(self, coords, unit, virtual = False):
    self.underlying.place(coords, unit)
    if not virtual:
      for p in self.players:
        p.io.place(coords, unit)

  def remove(self, coords, virtual = False):
    unit = self.underlying.remove(coords)
    if not virtual:
      for p in self.players:
        p.io.remove(coords)
    return unit

  def get_unit(self, coords):
    return self.underlying.get_unit(coords)

  def get_units_grouped(self):
    return self.underlying.get_units_grouped()

def field_after_reconnect(field):
  def f(io):
    for unit in logic.field.get_units_all(field):
      io.place(unit.coords, unit)
  return f

