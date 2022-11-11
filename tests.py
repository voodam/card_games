import shlex
import subprocess
import time
import argparse

import logic.game
from logic.cards import Rank, Suit, card
import logic.cards
from logic.cardgame import hitting_card
from logic.field import SegType
import logic.field
from logic.game.goat import Goat
import logic.game.thousand as t
import logic.game.fool as f

parser = argparse.ArgumentParser(description="Unit and integration tests")
parser.add_argument("--no-integration", dest="integration", action="store_false", help="Team start scores")
args = parser.parse_args()

p1 = logic.game.Player("")
p2 = logic.game.Player("")
p3 = logic.game.Player("")
p4 = logic.game.Player("")
# тысяча
widdle = logic.cards.deal([p1, p2, p3], logic.cards.deck_from(Rank.Nine), 7)
assert len(widdle) == 3
for p in (p1, p2, p3):
  assert len(p.cards) == 7
# козел
assert not logic.cards.deal([p1, p2, p3, p4], logic.cards.deck_from(Rank.Seven))
for p in (p1, p2, p3, p4):
  assert len(p.cards) == 8
# дурак
deck = logic.cards.deal([p1, p2, p3], logic.cards.deck_from(Rank.Six), 6)
assert len(deck) == 36 - 3*6
for p in (p1, p2, p3):
  assert len(p.cards) == 6

goat = Goat()
# туз другой масти не бьет
assert hitting_card(goat, [card("♦K"), card("♠A")], Suit("♣")) == card("♦K")
# туз козырь бьет другую масть
assert hitting_card(goat, [card("♦K"), card("♠A")], Suit("♠")) == card("♠A")
# десятка бьет короля
assert hitting_card(goat, [card("♦K"), card("♦10")], Suit("♣")) == card("♦10")
# семерка козырь бъет валет
assert hitting_card(goat, [card("♦7"), card("♣J")], Suit("♦")) == card("♦7")
# туз не бьет валет той же масти
assert hitting_card(goat, [card("♦J"), card("♦A")], Suit("♦")) == card("♦J")
assert hitting_card(goat, [card("♦J"), card("♦A")], Suit("♠")) == card("♦J")
# валет бьет туз той же масти
assert hitting_card(goat, [card("♦A"), card("♦J")], Suit("♦")) == card("♦J")
assert hitting_card(goat, [card("♦A"), card("♦J")], Suit("♠")) == card("♦J")
# восемь бьет семь
assert hitting_card(goat, [card("♦7"), card("♦8")], Suit("♠")) == card("♦8")

player_cards = [card("♥8"), card("♠10")]
# первая положенная карта может быть любой
assert goat.allowed_cards(player_cards, [], Suit("♥")) == player_cards
# если положили козырь, но его нет, то можно класть любую
assert goat.allowed_cards(player_cards, [card("♦K")], Suit("♦")) == player_cards
# если положили валет, но козырей нет, то можно класть карту той же масти
assert goat.allowed_cards(player_cards, [card("♠J")], Suit("♦")) == player_cards
# если положили козырь, то нужно класть козырь
assert goat.allowed_cards(player_cards, [card("♥K")], Suit("♥")) == [card("♥8")]
# если масти нет, то можно класть любую
assert goat.allowed_cards(player_cards, [card("♣K")], Suit("♥")) == player_cards

player_cards = [card("♥8"), card("♠J")]
# если положили козырь, то нужно класть валет
assert goat.allowed_cards(player_cards, [card("♦K")], Suit("♦")) == [card("♠J")]
# если положили масть, то нужно класть ее, а не валет
player_cards = [card("♠8"), card("♠J")]
assert goat.allowed_cards(player_cards, [card("♠K")], Suit("♦")) == [card("♠8")]
assert goat.allowed_cards(player_cards, [card("♠K")], Suit("♠")) == player_cards

thousand = t.Thousand()
p = logic.game.Player("")
t.init_player(p)
p.cards = [card("♥K"), card("♥Q"), card("♦K"), card("♦Q"), card("♣K"), card("♣Q"), card("♠K"), card("♠Q")]
assert thousand.allowed_trumps(p) == set()
p.cards = [card("♥K"), card("♥Q"), card("♦K"), card("♦Q"), card("♣K"), card("♣Q")]
assert thousand.allowed_trumps(p) == {Suit("♥"), Suit("♦"), Suit("♣")}
p.cards = [card("♥K"), card("♥Q"), card("♣K"), card("♣Q")]
assert thousand.allowed_trumps(p) == {Suit("♥"), Suit("♣")}
p.cards = [card("♠Q"), card("♦K"), card("♠A"), card("♥10")]
assert thousand.allowed_trumps(p) == set()

t.init_player(p)
# болт
assert t.calc_score(p) == (0, 1)
assert p.bolts == 1
assert p.score == 0
# третья штанга
assert t.calc_score(p, double_score=True) == (0, 2)
assert p.bolts == 0
assert p.score == -120
# штанга, переполнение
p.bolts = 2
assert t.calc_score(p, double_score=True) == (0, 2)
assert p.bolts == 1
assert p.score == -240
# -170
p.points = 109
p.selected_trumps = set([Suit.Clubs])
assert t.calc_score(p, bid_winner=p, bid=170) == (-170, 0)
assert p.score == -410
# +200
p.points = 100
p.selected_trumps = set([Suit.Hearts])
assert t.calc_score(p, bid_winner=p, bid=200) == (200, 0)
assert p.score == -210
# болт и -120
p.score = 0
p.points = 0
p.bolts = 2
assert t.calc_score(p, bid_winner=p, bid=120) == (-120, 1)
assert p.score == -240
assert p.bolts == 0
# штанга, -240 и самосвал
p.points = 0
assert t.calc_score(p, bid_winner=p, bid=120, double_score=True) == (-240, 2)
assert p.score == -480
assert p.bolts == 2
# на бочке < 125
t.put_on_barrel(p)
p.points = 150
assert t.calc_score(p, bid_winner=p, bid=115) == (-120, 0)
assert p.score == 760
# на бочке < 125 и болт
t.put_on_barrel(p)
p.points = 0
p.bolts = 2
assert t.calc_score(p, bid_winner=p, bid=115) == (-120, 1)
assert p.score == 640
assert p.bolts == 0
# на бочке 125 и набрал, захвалив
t.put_on_barrel(p)
p.points = 45
p.selected_trumps = set([Suit.Diamonds])
assert t.calc_score(p, bid_winner=p, bid=125) == (125, 0)
assert p.score == 1005
# на бочке 150 и не набрал
t.put_on_barrel(p)
p.points = 109
p.selected_trumps = set([Suit.Spades])
assert t.calc_score(p, bid_winner=p, bid=150) == (-150, 0)
assert p.score == 730
p.on_barrel = False
# набрал, захвалив 2 раза
p.score = 0
p.points = 40
p.selected_trumps = set([Suit.Spades, Suit.Clubs])
assert t.calc_score(p, bid_winner=p, bid=140) == (140, 0)
assert p.score == 140
# не брал прикуп и захвалил
p.points = 3
p.selected_trumps = set([Suit.Hearts])
assert t.calc_score(p) == (105, 0)
assert p.score == 245

p1 = logic.game.Player("")
p2 = logic.game.Player("")
p3 = logic.game.Player("")
t.init_player(p1)
t.init_player(p2)
t.init_player(p3)
players = [p1, p2, p3]
# двое не слетают с бочки
t.put_on_barrel(p1)
t.put_on_barrel(p2)
t.handle_barrel(players)
assert p1.on_barrel
assert p2.on_barrel
# трое слетают с бочки
t.put_on_barrel(p3)
t.handle_barrel(players)
assert not p1.on_barrel
assert not p2.on_barrel
assert p1.score == 760
assert p2.score == 760
# если набрал 875, то не на бочку
p1.score = 875
t.handle_barrel(players)
assert not p1.on_barrel
# если набрал 880, то на бочку
p1.score = 880
t.handle_barrel(players)
assert p1.on_barrel
# если набрал 1005, то на бочку
t.init_player(p1)
p1.score = 1005
t.handle_barrel(players)
assert p1.on_barrel
assert p1.score == 880
# с двух бочек не слетает на +5
t.put_on_barrel(p1)
p1.barrel_fails = 1
p1.score = 760
t.handle_barrel(players)
assert not p1.on_barrel
assert p1.score == 760
# с трех бочек слетает на +5
t.put_on_barrel(p1)
p1.score = 760
t.handle_barrel(players)
assert not p1.on_barrel
assert p1.score == 5
# после трех попыток не заходит на бочку
t.init_player(p1)
p1.barrel_fails = 3
p1.score = 900
t.handle_barrel(players)
assert not p1.on_barrel
assert p1.score == 900
# после второй партии не слетел с бочки
t.init_player(p1)
t.put_on_barrel(p1)
t.handle_barrel(players)
t.handle_barrel(players)
assert p1.on_barrel
assert p1.barrel_parties == 2
# после третьей партии слетел с бочки
t.handle_barrel(players)
assert not p1.on_barrel
assert p1.score == 760
assert p1.barrel_parties == 0

fool = f.Fool(players_number=2)
p = logic.game.Player("")

p.cards = [card("♥K"), card("♥Q"), card("♦K"), card("♦Q"), card("♥8"), card("♠J")]
cards = f.TrickCards({card("♣Q"): card("♣K"), card("♣J"): None})
assert f.attacker_cards(p, cards) == [card("♥K"), card("♥Q"), card("♦K"), card("♦Q"), card("♠J")]
cards.add_unbeaten(card("♠10"))
cards.add_unbeaten(card("♠8"))
assert f.attacker_cards(p, cards) == p.cards
cards = f.TrickCards()
assert f.attacker_cards(p, cards) == p.cards
p.cards = []
assert f.attacker_cards(p, cards) == []

p.cards = [card("♦K"), card("♥A"), card("♥10"), card("♣A"), card("♠J"), card("♠6")]
cards = f.TrickCards({card("♣Q"): card("♣K"), card("♠10"): None, card("♥Q"): None})
assert f.defender_cards(fool, p, cards, Suit("♥")) == [card("♥A"), card("♥10"), card("♠J")]
assert f.defender_cards(fool, p, cards, Suit("♣")) == [card("♥A"), card("♣A"), card("♠J")]
assert f.defender_cards(fool, p, cards, Suit("♠")) == [card("♥A"), card("♠J"), card("♠6")]
assert f.defender_cards(fool, p, cards, Suit("♦")) == [card("♦K"), card("♥A"), card("♠J")]
cards = f.TrickCards()
assert f.defender_cards(fool, p, cards, Suit("♥")) == []
p.cards = [card("♦8"), card("♥7"), card("♥9")]
cards = f.TrickCards({card("♣Q"): None, card("♠10"): None, card("♥Q"): None})
assert f.defender_cards(fool, p, cards, Suit("♣")) == []
p.cards = []
assert f.defender_cards(fool, p, cards, Suit("♣")) == []

cards = f.TrickCards({card("♦6"): card("♦7"), card("♦10"): None, card("♦Q"): None, card("♥6"): None, card("♥A"): None})
assert f.beat(fool, card("♦K"), cards, Suit("♣")) == card("♦Q")
assert f.beat(fool, card("♦J"), cards, Suit("♣")) == card("♦10")
assert f.beat(fool, card("♥8"), cards, Suit("♥")) == card("♥6")
assert f.beat(fool, card("♣7"), cards, Suit("♣")) == card("♥A")
cards = f.TrickCards({card("♦10"): None})
try:
  f.beat(fool, card("♣K"), cards, Suit("♥"))
except AssertionError as e:
  assert str(e) == "No cards to beat available"

cards = [card("♦6"), card("♥6"), card("♠6"), card("♣6"), card("♠7"), card("♣7")]
deck = logic.cards.deck_from(Rank.Eight)
new_cards = f.replenish_cards(cards, deck)
assert len(new_cards) == 0
assert len(deck) == 28
cards = [card("♦6"), card("♥6"), card("♠6"), card("♣6"), card("♠7"), card("♣7"), card("♦7"), card("♥7")]
new_cards = f.replenish_cards(cards, deck)
assert len(new_cards) == 0
assert len(deck) == 28
cards = [card("♦6"), card("♥6")]
last_card = deck[-1]
new_cards = f.replenish_cards(cards, deck)
assert len(new_cards) == 4
assert len(deck) == 24
assert last_card == deck[-1]
cards = []
new_cards = f.replenish_cards(cards, deck)
assert len(new_cards) == 6
assert len(deck) == 18
assert last_card == deck[-1]
cards = [card("♠6"), card("♣6")]
deck = [card("♦6"), card("♥6")]
new_cards = f.replenish_cards(cards, deck)
assert len(new_cards) == 2
assert len(deck) == 0
cards = []
deck = []
new_cards = f.replenish_cards(cards, deck)
assert len(new_cards) == 0
assert len(deck) == 0

assert logic.field.get_segment_coords([5, 0], [0, 0]) == ([[1, 0], [2, 0], [3, 0], [4, 0]], SegType.LINE)
assert logic.field.get_segment_coords([3, 5], [5, 5]) == ([[4, 5]], SegType.LINE)
assert logic.field.get_segment_coords([2, 6], [2, 2]) == ([[2, 3], [2, 4], [2, 5]], SegType.LINE)
assert logic.field.get_segment_coords([6, 7], [6, 4]) == ([[6, 5], [6, 6]], SegType.LINE)
assert logic.field.get_segment_coords([4, 4], [8, 8]) == ([[5, 5], [6, 6], [7, 7]], SegType.DIAG)
assert logic.field.get_segment_coords([8, 4], [5, 1]) == ([[6, 2], [7, 3]], SegType.DIAG)
assert logic.field.get_segment_coords([3, 7], [6, 4]) == ([[4, 6], [5, 5]], SegType.DIAG)
assert logic.field.get_segment_coords([6, 7], [6, 7]) == ([], SegType.LINE)
assert logic.field.get_segment_coords([6, 7], [6, 8]) == ([], SegType.LINE)
assert logic.field.get_segment_coords([6, 7], [4, 4]) == ([], SegType.NOT_SEGMENT)

if args.integration:
  games = {
    "goat": (goat.players_number, 5),
    "thousand": (thousand.players_number, 10)
  }

  for game, (players_number, test_duration) in games.items():
    command = f"python3 {game}.py --cpu-players={players_number}"
    server = subprocess.Popen(shlex.split(command), stdout=subprocess.DEVNULL)
    time.sleep(test_duration)
    server.kill()

  command = "python3 fool.py --cpu-players=5 --total-players=5"
  server = subprocess.Popen(shlex.split(command), stdout=subprocess.DEVNULL)
  time.sleep(10)
  server.kill()

