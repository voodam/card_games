from typing import final
import itertools
from playing_cards import Rank, Suit
import playing_cards
from player_io import EvtType, send_event_all, send_text_all
import player_io
import gaming
import util

ace_ten_king_points = {
  Rank.Ace: 11,
  Rank.Ten: 10,
  Rank.King: 4,
  Rank.Queen: 3,
  Rank.Jack: 2
}

class CardGame:
  def __init__(self, deck, players_number, widdle_amount = 0):
    self.deck = deck
    self.players_number = players_number
    self.widdle_amount = widdle_amount

  def hand_amount(self, after_bidding = True):
    free_deck_len = len(self.deck)
    if not after_bidding:
      free_deck_len -= self.widdle_amount
    return free_deck_len // self.players_number

  def allowed_cards(self, player_cards, trick_cards, trump):
    if not trick_cards:
      return player_cards
    
    return [c for c in player_cards if self.eq_suits(trick_cards[0], c, trump)] or player_cards

  @final
  def hitting_card(self, trick_cards, trump):
    def key(c):
      return self.card_hit_value(c, trick_cards, trump)
    return sorted(trick_cards, key=key, reverse=True)[0]

  def card_hit_value(self, card, trick_cards, trump):
    if card.suit == trump:
      return self.card_points(card) + list(Rank).index(card.rank) + 50
    elif card.suit == trick_cards[0].suit:
      return self.card_points(card) + list(Rank).index(card.rank)
    else:
      return 0

  def card_points(self, card):
    return ace_ten_king_points.get(card.rank, 0)

  def eq_suits(self, card1, card2, trump):
    return card1.suit == card2.suit

def attach_cards(player, cards):
  playing_cards.attach_to_player(cards, player)
  player_io.send_deal(player)

def reattach_cards(to_player, cards):
  playing_cards.detach_from_player(cards)
  playing_cards.attach_to_player(cards, to_player)
  player_io.send_deal(to_player)

# Trick-taking game reusable components

def bidding(players, game, start_min_bid = None):
  if start_min_bid is None:
    start_min_bid = game.min_bid

  bid_players = [p for p in players if game.can_bid(p)]
  if len(bid_players) == 0:
    send_text_all(players, f"{players[0]} победил без торга ({start_min_bid})")
    return players[0], start_min_bid

  def conduct_bidding():
    min_bid = start_min_bid
    can_skip = False
    while True:
      assert bid_players
      for p in bid_players.copy():
        max_bid = game.max_bid(p)
        message = f"Сделайте ставку от {min_bid} до {max_bid}"
        bid = p.io.select_bid(min_bid, max_bid, game.bid_step, can_skip, message)
        can_skip = True
        if bid is None:
          bid_players.remove(p)
          send_text_all(players, f'{p} сказал "пас"')
        else:
          min_bid = bid + game.bid_step
          send_text_all(players, f"{p} идет на {bid}")
        if len(bid_players) == 1:
          return min_bid - game.bid_step

  bid = conduct_bidding()
  send_text_all(players, f"{bid_players[0]} победил в торгах ({bid})")
  return bid_players[0], bid

def trick(players, game, points_holder = util.id,
          can_player_select_trump = False, trump = None):
  send_event_all(players, EvtType.TRICK)
  trick_cards = []

  if can_player_select_trump:
    p = players[0]
    trumps = game.allowed_trumps(p)
    if trumps and p.io.select_yesno("Хотите выбрать козырь?"):
      if len(trumps) == 1:
        trump = list(trumps)[0]
      else:
        trump = p.io.select_suit(trumps)
      p.selected_trumps.add(trump)
      send_event_all(players, EvtType.TRUMP, trump)
      send_text_all(players, f"{p} выбрал козырь {trump}")

  for p in players:
    send_text_all(players, f"Ходит {p}")
    cards = game.allowed_cards(p.cards, trick_cards, trump)
    card = p.io.select_card(cards)
    trick_cards.append(card)
    send_event_all(players, EvtType.CARD, {"card": card, "from": p})

  taker = game.hitting_card(trick_cards, trump).player
  points = sum(game.card_points(card) for card in trick_cards)
  points_holder(taker).points += points
  send_text_all(players, f"{taker} забирает взятку ({points})")

  for card in trick_cards:
    playing_cards.detach_from_player(card)
  gaming.player_starts(players, taker)

def init_player(p):
  p.selected_trumps = set()

def party(players, game, points_holder = util.id,
          can_player_select_trump = False, trump = None):
  for p in players:
    init_player(p)
    points_holder(p).points = 0

  while players[0].cards:
    trick(players, game, points_holder, can_player_select_trump, trump)

