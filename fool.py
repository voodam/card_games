from argparse import ArgumentParser
import random

import lib.list
from logic.io import EvtType, send_event_all, send_text_all
import logic.io
from logic.io.util import attach_cards, deal, put_card_on_table
import logic.game
from logic.game.fool import *

def trick(players, fool, trump):
  trick_cards = TrickCards()
  attacker1, defender, *other_players = players
  attacker2 = lib.list.get(other_players, 0)

  def put_card(p, can_skip = True):
    if not p:
      return None

    allowed_cards = attacker_cards(p, trick_cards)
    if not allowed_cards or len(defender.cards) <= len(trick_cards.get_unbeaten()):
      return None
    if can_skip and not p.io.select_yesno("Карту?"):
      return None

    send_text_all(players, f"Ходит {p}")
    card = put_card_on_table(p, players, allowed_cards, detached=True)
    trick_cards.add_unbeaten(card)
    return card

  def grab_cards(p):
    attach_cards(p, trick_cards.get_all())
    send_text_all(players, f"{p} забрал карты")

  send_event_all(players, EvtType.TRICK)
  card1 = put_card(attacker1, can_skip=False)
  card2 = put_card(attacker2)

  while (card1 or card2) and defender.cards:
    assert len(defender.cards) >= 1

    send_text_all(players, f"Ходит {defender}")
    if defender.io.select_yesno("Хотите забрать карты?"):
      grab_cards(defender)
      return True

    while trick_cards.get_unbeaten():
      allowed_cards = defender_cards(fool, defender, trick_cards, trump)
      if not allowed_cards:
        grab_cards(defender)
        return True
      card = put_card_on_table(defender, players, allowed_cards, detached=True)
      beat(fool, card, trick_cards, trump)

    card1 = put_card(attacker1)
    card2 = put_card(attacker2)
  return False


parser = ArgumentParser(description="Durak card game")
logic.io.add_cli_args(parser)
parser.add_argument("--total-players", type=int, choices=range(2, 7), metavar="[2-6]",
                    help="Total game players number", default=2)
args = parser.parse_args()
all_players = logic.io.new_players(args.total_players, **vars(args))

fool = Fool(args.total_players)
logic.game.player_starts(all_players, random.choice(all_players))

while True:
  random.shuffle(fool.deck)
  trump = fool.deck[-1]
  players = all_players.copy()
  send_event_all(players, EvtType.TRUMP, trump.suit)
  send_text_all(players, f"Козырь {trump}")
  deck = deal(players, fool, 6)

  while True:
    defender = players[1]
    cards_grabbed = trick(players, fool, trump.suit)

    if deck:
      for p in players:
        if p != defender:
          attach_cards(p, replenish_cards(p.cards, deck))
      attach_cards(defender, replenish_cards(defender.cards, deck))
    for p in players:
      if not p.cards:
        players.remove(p)
        send_text_all(players, f"{p} выиграл!")

    if len(players) <= 1:
      break

    is_next_attacker = cards_grabbed or not defender in players
    next_player = players[2 % len(players)] if is_next_attacker else defender
    send_text_all(players, f"Ходит {next_player}")
    logic.game.player_starts(players, next_player)

  if players:
    fool_player = players[0]
    send_text_all(players, f"{fool_player} проиграл!")
    next_i = (all_players.index(fool_player) - 1) % args.total_players
    next_player = all_players[next_i]
  else:
    send_text_all(players, f"Ничья!")
    next_player = all_players[1]

  logic.game.player_starts(all_players, next_player)

