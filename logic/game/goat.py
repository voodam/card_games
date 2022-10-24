from logic.cards import Rank, Suit, c, card as p_card
import logic.cards
from logic.cardgame import CardGame, ace_ten_king_points

class Goat(CardGame):
  def __init__(self):
    CardGame.__init__(self, logic.cards.deck_from(Rank.Seven),
                      players_number=4)
    
  def card_hit_value(self, card, trump, trick_cards = None):
    return {
      c(Rank.Seven, trump): 100,
      p_card("♣J"): 99,
      p_card("♠J"): 98,
      p_card("♥J"): 97,
      p_card("♦J"): 96,
    }.get(card) or \
    CardGame.card_hit_value(self, card, trump, trick_cards)

  def eq_suits(self, card1, card2, trump):
    is_trump1 = self.is_trump(card1, trump)
    is_trump2 = self.is_trump(card2, trump)

    if is_trump1:
      return is_trump2
    if is_trump2:
      return is_trump1
    return CardGame.eq_suits(self, card1, card2, trump)
  
  def is_trump(self, card, trump):
    return True if card.rank == Rank.Jack else card.suit == trump

  def card_points(self, card):
    return ace_ten_king_points.get(card.rank, 0)

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

