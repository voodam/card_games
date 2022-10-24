import itertools

from logic.io import EvtType, send_event_all, send_text_all
from logic.io.util import put_card_on_table
import logic.game
import logic.cards
from logic.cardgame import hitting_card

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
    card = put_card_on_table(p, players, cards)
    trick_cards.append(card)

  taker = hitting_card(game, trick_cards, trump).player
  points = sum(game.card_points(card) for card in trick_cards)
  taker.team.points += points
  send_text_all(players, f"{taker} забирает взятку ({points})")

  logic.cards.detach_from_player(trick_cards)
  logic.game.player_starts(players, taker)

def party(players, game, can_player_select_trump = False, trump = None):
  for p in players:
    p.selected_trumps = set()
    p.team.points = 0

  while players[0].cards:
    trick(players, game, can_player_select_trump, trump)

