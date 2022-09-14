import argparse
import random
import itertools
import gaming
import util
from playing_cards import Rank, Suit
import playing_cards
import card_game
import goat
from player_io import EvtType, send_event_all, send_text_all, send_deal
import player_io

parser = argparse.ArgumentParser(description="Goat card game")
player_io.add_cli_arguments(parser)
parser.add_argument("--team-scores", type=int, nargs="+", help="Team start scores")
args = parser.parse_args()

game = goat.Goat()
players = player_io.new_players(game.players_number, 
                                after_reconnect=lambda io: send_deal(io.player), **vars(args))
teams = gaming.assign_to_teams(players, goat.teams_number, args.team_scores)
team1, team2 = teams
first_player = random.choice(players)
gaming.player_starts(players, first_player)
parties_cycle = itertools.cycle(players.copy())
send_text_all(players, f"{team1} против {team2}")

while True:
  winner = None
  while not winner:
    gaming.player_starts(players, next(parties_cycle))

    random.shuffle(game.deck)
    playing_cards.deal(players, game.deck)
    for p in players:
      send_deal(p)

    clubs_jack_owner = playing_cards.get("♣J").player
    send_text_all(players, f"{clubs_jack_owner} выбирает козырь")
    trump = clubs_jack_owner.io.select_suit(list(Suit))
    send_event_all(players, EvtType.TRUMP, trump)

    card_game.party(players, game, points_holder=lambda p: p.team, trump=trump)

    defending_team = util.opposite_in_pair(teams, clubs_jack_owner.team)
    team, score = goat.calc_score(clubs_jack_owner.team, defending_team)
    team.score += score
    send_text_all(players, f"{team} набрали {score} очков ({team.points})! Счет: {team1.score}-{team2.score}")
    winner = goat.get_winner(teams)

  send_text_all(players, f"{winner} победили ({winner.score} очков)!")
  loser = util.opposite_in_pair(teams, winner)
  winner.score -= 12
  loser.score = 0

