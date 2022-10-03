import itertools
from playing_cards import Rank, Suit
import playing_cards
from player_io import EvtType, send_event_all, send_text_all
import player_io
import game_io
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
  def __init__(self, deck, players_number):
    self.deck = deck
    self.players_number = players_number

  def hand_amount(self):
    return len(self.deck) // self.players_number

  def allowed_cards(self, player_cards, trick_cards, trump):
    if not trick_cards:
      return player_cards
    
    return [c for c in player_cards if self.eq_suits(trick_cards[0], c, trump)] or player_cards

  def eq_suits(self, card1, card2, trump):
    return card1.suit == card2.suit

  def is_trump(self, card, trump):
    return card.suit == trump

  def card_hit_value(self, card, trump, trick_cards = None):
    """The sense of the algorithm is: "rely on card points, but if it's zero, rely on it's rank".
       So, override card_points method to rely not only on a rank."""

    total_rank = self.card_points(card) + list(Rank).index(card.rank)

    if card.suit == trump:
      return total_rank + 50
    elif not trick_cards or card.suit == trick_cards[0].suit:
      return total_rank
    else:
      return 0

  def card_points(self, card):
    return 0

def can_hit(game, hit_card, target_card, trump):
  return game.card_hit_value(hit_card, trump, [target_card]) > game.card_hit_value(target_card, trump)

def can_hit_any(game, hit_card, target_cards, trump):
  return any(can_hit(game, hit_card, c, trump) for c in target_cards)

def sort_by_hit_value(game, trick_cards, trump):
  return sorted(trick_cards, key=lambda c: game.card_hit_value(c, trump, trick_cards))

def hitting_card(game, trick_cards, trump):
  return sort_by_hit_value(game, trick_cards, trump)[-1]

def sort_by_rank_suit(game, trick_cards, trump = None):
  def key(c):
    suit_value = 10 if trump and game.is_trump(c, trump) else list(Suit).index(c.suit)
    return suit_value * 100 + list(Rank).index(c.rank)
  return sorted(trick_cards, key=key)

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

def trick(players, game, can_player_select_trump = False, trump = None):
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
    card = game_io.put_card_on_table(p, players, cards)
    trick_cards.append(card)

  taker = hitting_card(game, trick_cards, trump).player
  points = sum(game.card_points(card) for card in trick_cards)
  taker.team.points += points
  send_text_all(players, f"{taker} забирает взятку ({points})")

  playing_cards.detach_from_player(trick_cards)
  gaming.player_starts(players, taker)

def init_player(p):
  p.selected_trumps = set()

def party(players, game, can_player_select_trump = False, trump = None):
  for p in players:
    init_player(p)
    p.team.points = 0

  while players[0].cards:
    trick(players, game, can_player_select_trump, trump)

