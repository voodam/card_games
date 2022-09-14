import sys
import socket
import atexit
import shlex
import subprocess
from subprocess import DEVNULL
import random
import json
import re
import util
from simple_term_menu import TerminalMenu
from enum import Flag, Enum, auto
import playing_cards
import gaming

class IOMode(Flag):
  CONSOLE = auto()
  SOCKET = auto()
  WEBSOCKET_ONLY = auto()
  WEBSOCKET = SOCKET | WEBSOCKET_ONLY
  ALL = CONSOLE | WEBSOCKET

  def __str__(self):
    return self.name

class EvtType(Enum):
  # to client
  TEXT = auto()
  TRICK = auto()
  DEAL = auto()
  TRUMP = auto()
  CARD = auto()
  SELECT_YESNO = auto()
  SELECT_BID = auto()
  SELECT_CARD = auto()
  SELECT_SUIT = auto()
  # to server
  ENTER = auto()
  SELECT_YESNO_RESPONSE = auto()
  SELECT_BID_RESPONSE = auto()
  SELECT_CARD_RESPONSE = auto()
  SELECT_SUIT_RESPONSE = auto()

  def __str__(self):
    return self.name

  def to_json(self):
    return self.name

  def from_json(name):
    return EvtType[name]

class SocketIO:
  def __init__(self, player, conn, server, all_socket_ios, 
               after_reconnect = util.noop):
    self.player = player
    self.conn = conn
    self.server = server
    self.all_socket_ios = all_socket_ios
    self.after_reconnect = after_reconnect

  def send_event(self, evt_type, payload = None):
    try:
      self._do_send_event(evt_type, payload)
    except ConnectionError:
      self._reconnect()
      self.send_event(evt_type, payload)

  def _do_send_event(self, evt_type, payload):
    event = {
      "evt_type": evt_type,
      "payload": payload
    }
    bytes = str.encode(util.json_dumps(event) + "\n")
    self.conn.sendall(bytes)

  def listen_event(conn, evt_type):
    data = conn.recv(4096)
    if not data:
      raise ConnectionError()

    event = json.loads(data.decode())
    assert EvtType.from_json(event["evt_type"]) == evt_type
    return event.get("payload")

  def select_yesno(self, message):
    try:
      self._do_send_event(EvtType.SELECT_YESNO, message)
      boolean = SocketIO.listen_event(self.conn, EvtType.SELECT_YESNO_RESPONSE)
      assert isinstance(boolean, bool)
      return boolean
    except ConnectionError:
      self._reconnect()
      return self.select_yesno(message)

  def _reconnect(self):
    # We need to reconnect all disconnected players at once,
    # because frontend can have > 1 player on a screen.
    dead_ios = {}
    for io in self.all_socket_ios:
      if not util.is_socket_alive(self.conn):
        print(f"Player {io.player} lost connection, waiting for reconnect")
        io.conn.close()
        dead_ios[io.player.name] = io

    reconnected_ios = []
    while dead_ios:
      conn, _ = self.server.accept()
      player_name = SocketIO.listen_event(conn, EvtType.ENTER)
      if player_name in dead_ios:
        io = dead_ios.pop(player_name)
        io.conn = conn
        reconnected_ios.append(io)
        print(f"Player {player_name} reconnected")
      else:
        conn.close()
        print(f"Unknown player {player_name}, close connection")

    for io in reconnected_ios:
      io.after_reconnect(io)

  def __del__(self):
    self.conn.close()

class ConsoleIO:
  def __init__(self, player):
    self.player = player

  def _select(self, options):
    menu = TerminalMenu([str(o) for o in options])
    index = menu.show()
    if index is None: # keyboard interrupt
      sys.exit(0)
    return options[index]

  def select_yesno(self, message):
    print(message)
    return self._select([True, False])
    
  def send_event(self, evt_type, payload = None):
    if not payload:
      return
    if isinstance(payload, dict):
      payload = re.sub("['{},:]", "", str(payload))
    payload = str(payload)
    payload = re.sub("[♥️♦️]", lambda m: util.colored(m.group(), util.TextColor.Red), payload)
    print(payload)

def send_event_all(players, evt_type, payload = None):
  for player in players:
    player.io.send_event(evt_type, payload)

def send_text_all(players, text):
  send_event_all(players, EvtType.TEXT, text)

class CardSocketIO(SocketIO):
  def select_card(self, cards):
    try:
      self._do_send_event(EvtType.SELECT_CARD, cards)
      d = SocketIO.listen_event(self.conn, EvtType.SELECT_CARD_RESPONSE)
      card = playing_cards.Card.from_json(d)
      assert card in cards
      return card
    except ConnectionError:
      self._reconnect()
      return self.select_card(cards)

  def select_suit(self, suits):
    try:
      self._do_send_event(EvtType.SELECT_SUIT, suits)
      d = SocketIO.listen_event(self.conn, EvtType.SELECT_SUIT_RESPONSE)
      suit = playing_cards.Suit.from_json(d)
      assert suit in suits
      return suit
    except ConnectionError:
      self._reconnect()
      return self.select_suit(suits)

  def select_bid(self, min_bid, max_bid, step, can_skip, message):
    payload = {
      "min_bid": min_bid,
      "max_bid": max_bid,
      "step": step,
      "can_skip": can_skip,
      "message": message
    }
    try:
      self._do_send_event(EvtType.SELECT_BID, payload)
      bid = SocketIO.listen_event(self.conn, EvtType.SELECT_BID_RESPONSE)
      if bid is None:
        assert can_skip
        return bid

      assert bid >= min_bid
      assert bid <= max_bid
      assert bid % step == 0
      return bid
    except ConnectionError:
      self._reconnect()
      return self.select_bid(min_bid, max_bid, step, can_skip, message)

class CardConsoleIO(ConsoleIO):
  def select_card(self, cards):
    return self._select(cards)

  def select_suit(self, suits):
    return self._select(tuple(suits))

  def select_bid(self, min_bid, max_bid, step, can_skip, message):
    print(message)
    options = list(range(min_bid, max_bid + step, step))
    if can_skip:
      options.append(None)
    return self._select(options)

class CardRandomIO(CardConsoleIO):
  def _select(self, options):
    return random.choice(options)

  def send_event(self, evt_type, payload = None):
    print(f"[{self.player}, {evt_type}] ", end="" if payload else "\n")
    ConsoleIO.send_event(self, evt_type, payload)

def send_deal(player):
  player.io.send_event(EvtType.DEAL, player.cards)

class GameType(Enum):
  CARD = [CardSocketIO, CardConsoleIO, CardRandomIO]

def add_cli_arguments(arg_parser):
  arg_parser.add_argument("--io-mode", type=lambda s: IOMode[s], choices=list(IOMode), default=IOMode.ALL, help="Which communication is used by players")
  arg_parser.add_argument("--cpu-players", type=int, nargs="?", default=0, help="CPU players amount")
  arg_parser.add_argument("--host", type=str, nargs="?", default="127.0.0.1", help="Server host")
  arg_parser.add_argument("--port", type=int, nargs="?", default=8888, help="Server TCP port")
  arg_parser.add_argument("--websocket-port", type=int, nargs="?", default=8080, help="Websocket port (used by websocat for TCP-WS bridge)")
  arg_parser.add_argument("--frontend-port", type=int, nargs="?", default=8000, help="HTTP server port (for static pages)")

def new_players(players_number, io_mode, cpu_players, host, port, websocket_port, frontend_port, 
                game_type = GameType.CARD, after_reconnect = util.noop, **_):
  socket_io_cls, console_io_cls, random_io_cls = game_type.value
  players = []
  def add_player(p, io):
    p.io = io
    players.append(p)

  for i in range(cpu_players):
    player = gaming.Player(f"CPU{i+1}")
    add_player(player, random_io_cls(player))

  if io_mode & IOMode.CONSOLE and len(players) < players_number:
    print("Enter player name")
    name = input()
    player = gaming.Player(name)
    add_player(player, console_io_cls(player))

  if len(players) < players_number:
    if io_mode & IOMode.WEBSOCKET_ONLY:
      assert websocket_port
      assert frontend_port
      assert not util.is_port_in_use(websocket_port), f"Port {websocket_port} in use"
      assert not util.is_port_in_use(frontend_port), f"Port {frontend_port} in use"

      # websocat is used to up TCP-WebSocket bridge
      command = f"websocat --text ws-l:{host}:{websocket_port} tcp:{host}:{port}"
      websocat = subprocess.Popen(shlex.split(command))
      atexit.register(lambda: websocat.kill())
      command = f"python3 -m http.server {frontend_port} --directory web"
      frontend = subprocess.Popen(shlex.split(command), stdout=DEVNULL, stderr=DEVNULL)
      atexit.register(lambda: frontend.kill())

    if io_mode & IOMode.SOCKET:
      assert host
      assert port

      server = socket.socket()
      server.bind((host, port))
      server.listen()
      atexit.register(lambda: server.close())

      ios = []
      while len(players) < players_number:
        conn, _ = server.accept()
        name = SocketIO.listen_event(conn, EvtType.ENTER)
        player = gaming.Player(name)
        io = socket_io_cls(player, conn, server, ios, after_reconnect)
        ios.append(io)
        add_player(player, io)

  assert len(players) == players_number, "Wrong players number"
  return players

