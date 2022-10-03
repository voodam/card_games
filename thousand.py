import random
from playing_cards import Rank, Suit, c
import playing_cards
from card_game import CardGame
import card_game
import util

trump_points = {
  Suit.Hearts: 100,
  Suit.Diamonds: 80,
  Suit.Clubs: 60,
  Suit.Spades: 40
}

class Thousand(CardGame):
  def __init__(self):
    CardGame.__init__(self, playing_cards.deck_from(Rank.Nine),
                      players_number=3)
    self.min_bid = 100
    self.bid_step = 5

  def allowed_trumps(self, player):
    if len(player.cards) == self.hand_amount():
      return set()

    cards = set(player.cards)
    return {s for s in Suit if s not in player.selected_trumps \
            and {c(Rank.King, s), c(Rank.Queen, s)}.issubset(cards)}

  def can_bid(self, player):
    return player.score > -300

  def max_bid(self, player):
    return 120 + sum(trump_points[suit] for suit in self.allowed_trumps(player))

  def card_points(self, card):
    return card_game.ace_ten_king_points.get(card.rank, 0)

def player_can_double_score(players):
  return players[0].score > 0 and not [p for p in players if p.on_barrel]

def hand_can_be_rejected(game, hand, is_first_player = False):
  nine_enough = 3 if is_first_player else 4
  return len([c for c in hand if c.rank == Rank.Nine]) >= nine_enough \
         or len([c for c in hand if c.rank == Rank.Jack]) >= 4 \
         or sum(game.card_points(c) for c in hand) < 13

def widdle_can_be_rejected(game, widdle):
  return len([c for c in widdle if c.rank == Rank.Nine]) >= 2 \
         or len([c for c in widdle if c.rank == Rank.Jack]) >= 3 \
         or sum(game.card_points(c) for c in widdle) < 5

def shuffle(deck):
  random.shuffle(deck)
  if deck[-1].rank == Rank.Jack:
    random.shuffle(deck)
    return True

  attempts = 0
  while deck[-1].rank == Rank.Nine:
    random.shuffle(deck)
    attempts += 1
    if attempts >= 3:
      return False

  return True

def calc_score(player, bid_winner = None, bid = None, double_score = False):
  factor = 2 if double_score else 1

  def calc_bolts():
    if player.points != 0:
      return 0

    bolts = 1 * factor
    player.bolts += bolts
    if player.bolts >= 3:
      player.score -= 120
      player.bolts -= 3
    return bolts
    

  def calc_score_normal(bid):
    trump_scores = sum(trump_points[suit] for suit in player.selected_trumps)
    if bid:
      is_win = bid <= player.points + trump_scores
      score = (1 if is_win else -1) * factor * bid
      if is_win:
        player.wins += 1
    else:
      score = round(player.points / 5) * 5 * factor + trump_scores

    player.score += score
    if player.score in [555, -555]:
      player.score = 5
    return score

  def do_calc():
    if player.on_barrel:
      assert player.score == 880
      if player == bid_winner:
        if bid < 125:
          score = -120
          player.score += score
          return score
        else:
          return calc_score_normal(bid)
      else:
        return 0
    else:
      player_bid = bid if player == bid_winner else None
      return calc_score_normal(player_bid)

  score = do_calc()
  bolts = calc_bolts()
  return score, bolts

def init_player(p):
  card_game.init_player(p)
  p.points = 0
  p.score = 0
  p.wins = 0
  p.bolts = 0
  p.on_barrel = False
  p.barrel_fails = 0

def put_on_barrel(p):
  p.on_barrel = True
  p.score = 880
  p.barrel_parties = 0

def handle_barrel(players):
  def fall(p):
    p.on_barrel = False
    p.barrel_parties = 0
    p.barrel_fails += 1
    if p.barrel_fails >= 3:
      p.score = 5

  for p in players:
    if p.on_barrel:
      if p.score < 880:
        fall(p)
      else:
        assert p.score == 880
        p.barrel_parties += 1
        if p.barrel_parties >= 3:
          p.score -= 120
          fall(p)
    elif p.score >= 880 and p.barrel_fails < 3:
      put_on_barrel(p)

  if len([p for p in players if p.on_barrel]) >= 3:
    for p in players:
      p.score -= 120
      fall(p)

def score_message(players):
  def get_msg(p):
    if p.on_barrel:
      msg = f"🔴{p.barrel_parties}🛢️{p.barrel_fails}"
    else:
      msg = f"{p.score}({p.points})"
    if p.bolts:
      msg += f" 🔩{p.bolts}"
    return f"{p.name}: {msg}"

  return ", ".join(get_msg(p) for p in players)

