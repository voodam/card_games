import itertools
import util

player_starts = util.list_rotate

class Player:
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return self.name

  def __repr__(self):
    return str(self)

  def to_json(self):
    return self.name

  def from_json(name):
    return Player(name)

class Team:
  def __init__(self, score = 0):
    self.score = score
    self.players = []

  def __str__(self):
    return " & ".join([str(p) for p in self.players])

  def __repr__(self):
    return str(self)

def assign_to_teams(players, teams_number, team_scores = None):
  if not team_scores:
    team_scores = [0] * teams_number

  assert len(players) % teams_number == 0
  assert teams_number == len(team_scores)

  teams = [Team(score) for score in team_scores]
  it = itertools.cycle(teams)
  for player in players:
    team = next(it)
    player.team = team
    team.players.append(player)
  return teams

