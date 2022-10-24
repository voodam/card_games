import itertools

from logic.cards import Rank, Suit

ace_ten_king_points = {
  Rank.Ace: 11,
  Rank.Ten: 10,
  Rank.King: 4,
  Rank.Queen: 3,
  Rank.Jack: 2
}

class CardGame:
  def __init__(self, deck, players_number):
    self.deck = deck
    self.players_number = players_number

  def hand_amount(self):
    return len(self.deck) // self.players_number

  def allowed_cards(self, player_cards, trick_cards, trump):
    if not trick_cards:
      return player_cards
    
    return [c for c in player_cards if self.eq_suits(trick_cards[0], c, trump)] or player_cards

  def eq_suits(self, card1, card2, trump):
    return card1.suit == card2.suit

  def is_trump(self, card, trump):
    return card.suit == trump

  def card_hit_value(self, card, trump, trick_cards = None):
    """The sense of the algorithm is: "rely on card points, but if it's zero, rely on it's rank".
       So, override card_points method to rely not only on a rank."""

    total_rank = self.card_points(card) + list(Rank).index(card.rank)

    if card.suit == trump:
      return total_rank + 50
    elif not trick_cards or card.suit == trick_cards[0].suit:
      return total_rank
    else:
      return 0

  def card_points(self, card):
    return 0

def can_hit(game, hit_card, target_card, trump):
  return game.card_hit_value(hit_card, trump, [target_card]) > game.card_hit_value(target_card, trump)

def can_hit_any(game, hit_card, target_cards, trump):
  return any(can_hit(game, hit_card, c, trump) for c in target_cards)

def sort_by_hit_value(game, trick_cards, trump):
  return sorted(trick_cards, key=lambda c: game.card_hit_value(c, trump, trick_cards))

def hitting_card(game, trick_cards, trump):
  return sort_by_hit_value(game, trick_cards, trump)[-1]

def sort_by_rank_suit(game, trick_cards, trump = None):
  def key(c):
    suit_value = 10 if trump and game.is_trump(c, trump) else list(Suit).index(c.suit)
    return suit_value * 100 + list(Rank).index(c.rank)
  return sorted(trick_cards, key=key)

