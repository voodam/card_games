import argparse
import random
from player_io import EvtType, send_event_all, send_text_all
import player_io
import game_io
import card_game
import playing_cards
import gaming
import fool
import util

def trick(players, game, trump):
  trick_cards = fool.TrickCards()
  attacker1, defender, *other_players = players
  attacker2 = util.list_get(other_players, 0)

  def put_card(p, can_skip = True):
    if not p:
      return None

    allowed_cards = fool.attacker_cards(p, trick_cards)
    if not allowed_cards or len(defender.cards) <= len(trick_cards.get_unbeaten()):
      return None
    if can_skip and not p.io.select_yesno("Карту?"):
      return None

    send_text_all(players, f"Ходит {p}")
    card = game_io.put_card_on_table(p, players, allowed_cards, detached=True)
    trick_cards.add_unbeaten(card)
    return card

  def grab_cards(p):
    game_io.attach_cards(p, trick_cards.get_all())
    send_text_all(players, f"{p} забрал карты")

  send_event_all(players, EvtType.TRICK)
  card1 = put_card(attacker1, can_skip=False)
  card2 = put_card(attacker2)

  while (card1 or card2) and defender.cards:
    assert len(defender.cards) >= 1

    if defender.io.select_yesno("Хотите забрать карты?"):
      grab_cards(defender)
      return True

    while trick_cards.get_unbeaten():
      allowed_cards = fool.defender_cards(game, defender, trick_cards, trump)
      if not allowed_cards:
        grab_cards(defender)
        return True
      card = game_io.put_card_on_table(defender, players, allowed_cards, detached=True)
      fool.beat(game, card, trick_cards, trump)

    card1 = put_card(attacker1)
    card2 = put_card(attacker2)
  return False


parser = argparse.ArgumentParser(description="Fool card game")
player_io.add_cli_args(parser)
parser.add_argument("--total-players", type=int, choices=range(2, 7), metavar="[2-6]",
                    help="Total game players number", default=2)
args = parser.parse_args()
all_players = player_io.new_players(args.total_players, **vars(args))

game = fool.Fool(args.total_players)
gaming.player_starts(all_players, random.choice(all_players))

while True:
  random.shuffle(game.deck)
  trump = game.deck[-1]
  players = all_players.copy()
  send_event_all(players, EvtType.TRUMP, trump.suit)
  send_text_all(players, f"Козырь {trump}")
  deck = game_io.deal(players, game, 6)

  while True:
    defender = players[1]
    cards_grabbed = trick(players, game, trump.suit)

    if deck:
      for p in players:
        if p != defender:
          game_io.attach_cards(p, fool.replenish_cards(p.cards, deck))
      game_io.attach_cards(defender, fool.replenish_cards(defender.cards, deck))
    for p in players:
      if not p.cards:
        players.remove(p)
        send_text_all(players, f"{p} выиграл!")

    if len(players) <= 1:
      break

    is_next_attacker = cards_grabbed or not defender in players
    next_player = players[2 % len(players)] if is_next_attacker else defender
    send_text_all(players, f"Ходит {next_player}")
    gaming.player_starts(players, next_player)

  if players:
    fool_player = players[0]
    send_text_all(players, f"{fool_player} проиграл!")
    next_i = (all_players.index(fool_player) - 1) % args.total_players
    next_player = all_players[next_i]
  else:
    send_text_all(players, f"Ничья!")
    next_player = all_players[1]

  gaming.player_starts(all_players, next_player)

