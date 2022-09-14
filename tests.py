import shlex
import subprocess
import time
import argparse
from playing_cards import Rank, Suit, get as c
import card_game
import gaming
import goat
import thousand as t

parser = argparse.ArgumentParser(description="Unit and integration tests")
parser.add_argument("--no-integration", dest="integration", action="store_false", help="Team start scores")
args = parser.parse_args()

goat = goat.Goat()
# туз другой масти не бьет
assert goat.hitting_card([c("♦K"), c("♠A")], Suit("♣"), ) == c("♦K")
# туз козырь бьет другую масть
assert goat.hitting_card([c("♦K"), c("♠A")], Suit("♠")) == c("♠A")
# десятка бьет короля
assert goat.hitting_card([c("♦K"), c("♦10")], Suit("♣")) == c("♦10")
# семерка козырь бъет валет
assert goat.hitting_card([c("♦7"), c("♣J")], Suit("♦")) == c("♦7")
# туз не бьет валет той же масти
assert goat.hitting_card([c("♦J"), c("♦A")], Suit("♦")) == c("♦J")
assert goat.hitting_card([c("♦J"), c("♦A")], Suit("♠")) == c("♦J")
# валет бьет туз той же масти
assert goat.hitting_card([c("♦A"), c("♦J")], Suit("♦")) == c("♦J")
assert goat.hitting_card([c("♦A"), c("♦J")], Suit("♠")) == c("♦J")
# восемь бьет семь
assert goat.hitting_card([c("♦7"), c("♦8")], Suit("♠")) == c("♦8")

player_cards = [c("♥8"), c("♠10")]
# первая положенная карта может быть любой
assert goat.allowed_cards(player_cards, [], Suit("♥")) == player_cards
# если положили козырь, но его нет, то можно класть любую
assert goat.allowed_cards(player_cards, [c("♦K")], Suit("♦")) == player_cards
# если положили валет, но козырей нет, то можно класть карту той же масти
assert goat.allowed_cards(player_cards, [c("♠J")], Suit("♦")) == player_cards
# если положили козырь, то нужно класть козырь
assert goat.allowed_cards(player_cards, [c("♥K")], Suit("♥")) == [c("♥8")]
# если масти нет, то можно класть любую
assert goat.allowed_cards(player_cards, [c("♣K")], Suit("♥")) == player_cards

player_cards = [c("♥8"), c("♠J")]
# если положили козырь, то нужно класть валет
assert goat.allowed_cards(player_cards, [c("♦K")], Suit("♦")) == [c("♠J")]
# если положили масть, то нужно класть ее, а не валет
player_cards = [c("♠8"), c("♠J")]
assert goat.allowed_cards(player_cards, [c("♠K")], Suit("♦")) == [c("♠8")]
assert goat.allowed_cards(player_cards, [c("♠K")], Suit("♠")) == player_cards

thousand = t.Thousand()
p = gaming.Player("")
t.init_player(p)
p.cards = [c("♥K"), c("♥Q"), c("♦K"), c("♦Q"), c("♣K"), c("♣Q"), c("♠K"), c("♠Q")]
assert thousand.allowed_trumps(p) == set()
p.cards = [c("♥K"), c("♥Q"), c("♦K"), c("♦Q"), c("♣K"), c("♣Q")]
assert thousand.allowed_trumps(p) == {Suit("♥"), Suit("♦"), Suit("♣")}
p.cards = [c("♥K"), c("♥Q"), c("♣K"), c("♣Q")]
assert thousand.allowed_trumps(p) == {Suit("♥"), Suit("♣")}
p.cards = [c("♠Q"), c("♦K"), c("♠A"), c("♥10")]
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

p1 = gaming.Player("")
p2 = gaming.Player("")
p3 = gaming.Player("")
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

if args.integration:
  command = f"python3 goat_main.py --cpu-players={goat.players_number}"
  server = subprocess.Popen(shlex.split(command), stdout=subprocess.DEVNULL)
  time.sleep(2)
  server.kill()

  command = f"python3 thousand_main.py --cpu-players={thousand.players_number}"
  server = subprocess.Popen(shlex.split(command), stdout=subprocess.DEVNULL)
  time.sleep(10)
  server.kill()

