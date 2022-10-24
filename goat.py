from argparse import ArgumentParser
import random
import itertools

from lib.util import opposite_in_pair
from logic.io import EvtType, send_event_all, send_text_all
import logic.io
import logic.io.trick_taking as trick_taking
from logic.io.util import deal
from logic.cards import Rank, Suit, card
import logic.game
from logic.game.goat import *

parser = ArgumentParser(description="Kozel card game")
logic.io.add_cli_args(parser)
logic.game.add_team_args(parser)
args = parser.parse_args()

goat = Goat()
players = logic.io.new_players(goat.players_number, **vars(args))
teams = logic.game.assign_to_teams(players, teams_number=2, team_scores=args.team_scores)
team1, team2 = teams
parties_cycle = itertools.cycle(players.copy())

logic.game.player_starts(players, random.choice(players))
send_text_all(players, f"{team1} против {team2}")

while True:
  winner = None
  while not winner:
    logic.game.player_starts(players, next(parties_cycle))

    random.shuffle(goat.deck)
    deal(players, goat)

    clubs_jack_owner = card("♣J").player
    send_text_all(players, f"{clubs_jack_owner} выбирает козырь")
    trump = clubs_jack_owner.io.select_suit(list(Suit))
    send_event_all(players, EvtType.TRUMP, trump)

    trick_taking.party(players, goat, trump=trump)

    defending_team = opposite_in_pair(teams, clubs_jack_owner.team)
    team, score = calc_score(clubs_jack_owner.team, defending_team)
    team.score += score
    send_text_all(players, f"{team} набрали {score} очков ({team.points})! Счет: {team1.score}-{team2.score}")
    winner = get_winner(teams)

  send_text_all(players, f"{winner} победили ({winner.score} очков)!")
  loser = opposite_in_pair(teams, winner)
  winner.score -= 12
  loser.score = 0

