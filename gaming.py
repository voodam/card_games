from enum import Enum, auto
import itertools
import util

player_starts = util.list_rotate

class Player:
  def __init__(self, name):
    self.name = name

  def __str__(self): return self.name
  def __repr__(self): return str(self)
  def to_json(self): return self.name
  def from_json(name): return Player(name)

class Team:
  def __init__(self, score = 0, color = None):
    self.score = score
    self.color = color
    self.players = []

  def __str__(self):
    return " & ".join(str(p) for p in self.players)

  def __repr__(self):
    return str(self)

def assign_to_teams(players, teams_number = None, team_scores = None, team_colors = None):
  if not teams_number:
    teams_number = len(players)
  if not team_scores:
    team_scores = [0] * teams_number
  if not team_colors:
    team_colors = [None] * teams_number

  assert len(players) % teams_number == 0
  assert teams_number == len(team_scores) == len(team_colors)

  teams = [Team(score, color) for score, color in zip(team_scores, team_colors)]
  it = itertools.cycle(teams)
  for player in players:
    team = next(it)
    player.team = team
    team.players.append(player)
  return teams

def add_team_args(arg_parser):
  arg_parser.add_argument("--team-scores", type=int, nargs="+", help="Team start scores")

