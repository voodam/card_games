import argparse
import random
import itertools
import sys

from logic.io import EvtType, send_event_all, send_text_all
import logic.io
import logic.io.trick_taking as trick_taking
from logic.io.util import deal, attach_cards, select_card
import logic.game
from logic.game.thousand import *

parser = argparse.ArgumentParser(description="1000 card game")
logic.io.add_cli_args(parser)
logic.game.add_team_args(parser)
args = parser.parse_args()

thousand = Thousand()
players = logic.io.new_players(thousand.players_number, **vars(args))
logic.game.assign_to_teams(players, team_scores=args.team_scores)
parties_cycle = itertools.cycle(players.copy())
next(parties_cycle)

logic.game.player_starts(players, random.choice(players))
parties_amount = 0
redeals_amount = 0
golden_party = True
for p in players:
  init_player(p)

def party_occured():
  global parties_amount
  global redeals_amount
  parties_amount += 1
  redeals_amount = 0
  logic.game.player_starts(players, next(parties_cycle))

def penalize_dealer():
  players[-1].score -= 120
  send_text_all(players, f"{players[-1]} плохо сдал (-120)")
  party_occured()

while True:
  if redeals_amount >= 3:
    penalize_dealer()
    continue

  golden_party = parties_amount < thousand.players_number
  if not golden_party and not [p for p in players if p.wins > 0]:
    golden_party = True
    parties_amount = 0
    send_text_all(players, f"Золотой кон заново")

  if golden_party:
    double_score = True
  else:
    double_score = False
    min_bid = thousand.min_bid
    if player_can_double_score(players):
      double_score = players[0].io.select_yesno("Хотите затемнить?")
      if double_score:
        send_text_all(players, f"{players[0]} затемнил")
        min_bid = 120

  if not shuffle(thousand.deck):
    penalize_dealer()
    continue

  widdle = deal(players, thousand, 7)

  if golden_party:
    bid_winner = players[0]
    bid = 120
  else:
    bid_winner, bid = trick_taking.bidding(players, thousand, min_bid)
    if double_score and bid != 120:
      double_score = False
  other_player1, other_player2 = set(players) - {bid_winner}

  attach_cards(bid_winner, widdle)
  
  bid_winner_questioned = False
  for p in players:
    widdle_cb_rejected = widdle_can_be_rejected(thousand, widdle) \
      if p == bid_winner else False

    if widdle_cb_rejected or hand_can_be_rejected(thousand, p.cards, p == players[0]):
      if p.io.select_yesno("Пересдать?"):
        redeals_amount += 1
        send_text_all(players, f"{p} попросил пересдать")
        continue
      elif p == bid_winner:
        bid_winner_questioned = True

  if bid_winner_questioned or bid_winner.io.select_yesno("Хотите играть?"):
    bid_winner.io.send_event(EvtType.TEXT, f"Выберите карту для {other_player1}")
    card1 = select_card(bid_winner, bid_winner.cards, detached=True)
    attach_cards(other_player1, card1)
    bid_winner.io.send_event(EvtType.TEXT, f"Выберите карту для {other_player2}")
    card2 = select_card(bid_winner, bid_winner.cards, detached=True)
    attach_cards(other_player2, card2)
    assert {len(p.cards) for p in players} == {thousand.hand_amount()}
    trick_taking.party(players, thousand, can_player_select_trump=True)
  else:
    # minimal bid just to fail without bolts
    bid_winner.points = 1
    other_player1.points = bid // 2
    other_player2.points = bid // 2
    send_text_all(players, f"{bid_winner} решил не играть ({bid})")
  party_occured()

  for p in players:
    calc_score(p, bid_winner, bid, double_score)
    if p.score >= 1000:
      send_text_all(players, f"{p} победил!")
      sys.exit(0)

  handle_barrel(players)
  send_text_all(players, f"Cчет. {score_message(players)}")

