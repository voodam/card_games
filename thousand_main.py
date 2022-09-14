import argparse
import random
import itertools
import sys
import gaming
import card_game
from playing_cards import Rank
import playing_cards
from player_io import EvtType, send_event_all, send_text_all, send_deal
import player_io
import util
import thousand
#pass 4 человека

parser = argparse.ArgumentParser(description="Thousand card game")
player_io.add_cli_arguments(parser)
args = parser.parse_args()

game = thousand.Thousand()
players = player_io.new_players(game.players_number, 
                                after_reconnect=lambda io: send_deal(io.player), **vars(args))

first_player = random.choice(players)
gaming.player_starts(players, first_player)
parties_cycle = itertools.cycle(players.copy())
next(parties_cycle)

parties_amount = 0
redeals_amount = 0
golden_party = True
for p in players:
  thousand.init_player(p)

def party_occured():
  global parties_amount
  global redeals_amount
  parties_amount += 1
  redeals_amount = 0
  gaming.player_starts(players, next(parties_cycle))

def penalize_dealer():
  players[-1].score -= 120
  send_text_all(players, f"{players[-1]} плохо сдал (-120)")
  party_occured()

while True:
  if redeals_amount >= 3:
    penalize_dealer()
    continue

  golden_party = parties_amount < game.players_number
  if not golden_party and not [p for p in players if p.wins > 0]:
    golden_party = True
    parties_amount = 0
    send_text_all(players, f"Золотой кон заново")

  if golden_party:
    double_score = True
  else:
    double_score = False
    min_bid = game.min_bid
    if thousand.player_can_double_score(players):
      double_score = players[0].io.select_yesno("Хотите затемнить?")
      if double_score:
        send_text_all(players, f"{players[0]} затемнил")
        min_bid = 120

  if not thousand.shuffle(game.deck):
    penalize_dealer()
    continue

  widdle = playing_cards.deal(players, game.deck, game.widdle_amount)
  for p in players:
    send_deal(p)

  if golden_party:
    bid_winner = players[0]
    bid = 120
  else:
    bid_winner, bid = card_game.bidding(players, game, min_bid)
    if double_score and bid != 120:
      double_score = False
  other_player1, other_player2 = set(players) - {bid_winner}

  card_game.attach_cards(bid_winner, widdle)
  
  bid_winner_questioned = False
  for p in players:
    widdle_can_be_rejected = game.widdle_can_be_rejected(widdle) \
      if p == bid_winner else False

    if widdle_can_be_rejected or game.hand_can_be_rejected(p.cards, p == players[0]):
      if p.io.select_yesno("Пересдать?"):
        redeals_amount += 1
        send_text_all(players, f"{p} попросил пересдать")
        continue
      elif p == bid_winner:
        bid_winner_questioned = True

  if bid_winner_questioned or bid_winner.io.select_yesno("Хотите играть?"):
    bid_winner.io.send_event(EvtType.TEXT, f"Выберите карту для {other_player1}")
    card1 = bid_winner.io.select_card(bid_winner.cards)
    card_game.reattach_cards(other_player1, card1)
    bid_winner.io.send_event(EvtType.TEXT, f"Выберите карту для {other_player2}")
    card2 = bid_winner.io.select_card(bid_winner.cards)
    card_game.reattach_cards(other_player2, card2)
    assert {len(p.cards) for p in players} == {game.hand_amount()}
    card_game.party(players, game, can_player_select_trump=True)
  else:
    # minimal bid just to fail without bolts
    bid_winner.points = 1
    other_player1.points = bid // 2
    other_player2.points = bid // 2
    send_text_all(players, f"{bid_winner} решил не играть ({bid})")
  party_occured()

  for player in players:
    thousand.calc_score(player, bid_winner, bid, double_score)
    if player.score >= 1000:
      send_text_all(players, f"{p} победил!")
      sys.exit(0)

  thousand.handle_barrel(players)
  send_text_all(players, f"Cчет. {thousand.score_message(players)}")

