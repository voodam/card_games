from playing_cards import Rank, Suit
import playing_cards
import card_game
from card_game import CardGame

teams_number = 2

class Goat(CardGame):
  def __init__(self):
    CardGame.__init__(self, playing_cards.deck_from(Rank.Seven),
                      players_number=4)
    
  def card_hit_value(self, card, trick_cards, trump):
    if card == playing_cards.get_card(Rank.Seven, trump):
      return 100
    elif card == playing_cards.get("♣J"):
      return 99
    elif card == playing_cards.get("♠J"):
      return 98
    elif card == playing_cards.get("♥J"):
      return 97
    elif card == playing_cards.get("♦J"):
      return 96
    else:
      return CardGame.card_hit_value(self, card, trick_cards, trump)

  def eq_suits(self, card1, card2, trump):
    def is_trump(c):
      return True if c.rank == Rank.Jack else c.suit == trump

    if is_trump(card1):
      return is_trump(card2)
    if is_trump(card2):
      return is_trump(card1)
    return CardGame.eq_suits(self, card1, card2, trump)

def calc_score(attacking_team, defending_team):
  assert attacking_team.points + defending_team.points == 120

  if attacking_team.points < 30:
    return defending_team, 4
  elif attacking_team.points < 60:
    return defending_team, 2
  elif attacking_team.points == 60:
    return defending_team, 0
  elif attacking_team.points <= 90:
    return attacking_team, 1
  elif attacking_team.points < 120:
    return attacking_team, 2
  else:
    return attacking_team, 4

def get_winner(teams):
  winners = [team for team in teams if team.score >= 12]
  assert len(winners) <= 1
  return winners[0] if winners else None

