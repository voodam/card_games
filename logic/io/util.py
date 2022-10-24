from logic.io import EvtType, send_event_all
import logic.cards
from logic.cardgame import sort_by_rank_suit
import logic.board

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

class BoardObserver:
  def __init__(self, underlying, players = []):
    self.underlying = underlying
    self.init_players(players)

  def init_players(self, players):
    self.players = players

  def place(self, coords, piece, virtual = False):
    self.underlying.place(coords, piece)
    if not virtual:
      for p in self.players:
        p.io.place(coords, piece)

  def remove(self, coords, virtual = False):
    piece = self.underlying.remove(coords)
    if not virtual:
      for p in self.players:
        p.io.remove(coords)
    return piece

  def get_piece(self, coords):
    return self.underlying.get_piece(coords)

  def get_pieces_grouped(self):
    return self.underlying.get_pieces_grouped()

def board_after_reconnect(board):
  def f(io):
    for piece in logic.board.get_pieces_all(board):
      io.place(piece.coords, piece)
  return f

