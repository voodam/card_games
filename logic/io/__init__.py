import sys
import socket
import atexit
import shlex
import subprocess
from subprocess import DEVNULL
import random
import json
import re
import logging
from enum import Flag, Enum, auto

from lib.util import colored, TextColor
from lib.fp import noop
from lib.socket import send_event, listen_event
import lib.socket
from logic.game import Player
from logic.cards import Card, Suit
from logic.game.chess import ChessPiece

class IOMode(Flag):
  CONSOLE = auto()
  SOCKET = auto()
  # It doesn't make sence to specify this mode, use WEBSOCKET instead
  WEBSOCKET_ONLY = auto()
  WEBSOCKET = SOCKET | WEBSOCKET_ONLY
  ALL = CONSOLE | WEBSOCKET

  def __str__(self):
    return self.name

class EvtType(Enum):
  # cards to client
  TEXT = auto()
  TRICK = auto()
  DEAL = auto()
  TRUMP = auto()
  CARD = auto()
  SELECT_YESNO = auto()
  SELECT_BID = auto()
  SELECT_CARD = auto()
  SELECT_SUIT = auto()
  # cards to server
  ENTER = auto()
  SELECT_YESNO_RESPONSE = auto()
  SELECT_BID_RESPONSE = auto()
  SELECT_CARD_RESPONSE = auto()
  SELECT_SUIT_RESPONSE = auto()

  # field to client
  FIELD_PLACE = auto()
  FIELD_REMOVE = auto()
  SELECT_FIELD_MOVE = auto()
  SELECT_PROMOTION = auto()
  # field to server
  SELECT_FIELD_MOVE_RESPONSE = auto()
  SELECT_PROMOTION_RESPONSE = auto()

  def __str__(self):
    return self.name

  def to_json(self):
    return self.name

  def from_json(name):
    return EvtType[name]

  def payload_from_json(self, payload):
    """Specify here every event that have payload parts that should be deserialized to objects."""
    card = Card.from_json
    suit = Suit.from_json
    player = Player.from_json
    chess_piece = ChessPiece.from_json

    if self == EvtType.SELECT_CARD_RESPONSE:
      return card(payload)
    elif self in (EvtType.TRUMP, EvtType.SELECT_SUIT_RESPONSE):
      return suit(payload)
    elif self in (EvtType.DEAL, EvtType.SELECT_CARD):
      return map(card, payload)
    elif self == EvtType.SELECT_SUIT:
      return map(suit, payload)
    elif self == EvtType.CARD:
      return {
        "card": card(payload["card"]),
        "from": player(payload["from"])
      }
    elif self == EvtType.SELECT_PROMOTION:
      return map(chess_piece, payload)
    elif self == EvtType.SELECT_PROMOTION_RESPONSE:
      return chess_piece(payload)
    return payload

class SocketIO:
  def __init__(self, player, conn, server, all_socket_ios, 
               after_reconnect = noop):
    self.player = player
    self.conn = conn
    self.server = server
    self.all_socket_ios = all_socket_ios
    self.after_reconnect = after_reconnect

  def __del__(self):
    self.conn.close()

  def send_event(self, evt_type, payload = None):
    try:
      send_event(self.conn, evt_type, payload)
    except ConnectionError:
      self._reconnect()
      self.send_event(evt_type, payload)

  def select_yesno(self, message):
    try:
      send_event(self.conn, EvtType.SELECT_YESNO, message)
      boolean = listen_event(self.conn, EvtType.SELECT_YESNO_RESPONSE)
      assert isinstance(boolean, bool)
      return boolean
    except ConnectionError:
      self._reconnect()
      return self.select_yesno(message)

  def _select(self, options, req_event, resp_event):
    try:
      send_event(self.conn, req_event, options)
      option = listen_event(self.conn, resp_event)
      assert option in options
      return option
    except ConnectionError:
      self._reconnect()
      return self._select(options, req_event, resp_event)

  def _reconnect(self):
    # We need to reconnect all disconnected players at once,
    # because frontend can have > 1 player on a screen.
    dead_ios = {}
    for io in self.all_socket_ios:
      if not lib.socket.is_socket_alive(self.conn):
        logging.info(f"Player {io.player} lost connection, waiting for reconnect")
        io.conn.close()
        dead_ios[io.player.name] = io

    reconnected_ios = []
    while dead_ios:
      conn, _ = self.server.accept()
      player_name = listen_event(conn, EvtType.ENTER)
      if player_name in dead_ios:
        io = dead_ios.pop(player_name)
        io.conn = conn
        reconnected_ios.append(io)
        logging.info(f"Player {player_name} reconnected")
      else:
        conn.close()
        logging.warning(f"Unknown player {player_name}, close connection")

    for io in reconnected_ios:
      io.after_reconnect(io)

class ConsoleIO:
  def _select(self, options):
    from simple_term_menu import TerminalMenu
    menu = TerminalMenu(str(o) for o in options)
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
    payload = re.sub("[♥♦]", lambda m: colored(m.group(), TextColor.Red), payload)
    print(payload)

def send_event_all(players, evt_type, payload = None):
  for p in players:
    p.io.send_event(evt_type, payload)

def send_text_all(players, text):
  send_event_all(players, EvtType.TEXT, text)

class CardSocketIO(SocketIO):
  def select_card(self, cards):
    return self._select(cards, EvtType.SELECT_CARD, EvtType.SELECT_CARD_RESPONSE)

  def select_suit(self, suits):
    return self._select(suits, EvtType.SELECT_SUIT, EvtType.SELECT_SUIT_RESPONSE)

  def select_bid(self, min_bid, max_bid, step, can_skip, message):
    payload = {
      "min_bid": min_bid,
      "max_bid": max_bid,
      "step": step,
      "can_skip": can_skip,
      "message": message
    }
    try:
      send_event(self.conn, EvtType.SELECT_BID, payload)
      bid = listen_event(self.conn, EvtType.SELECT_BID_RESPONSE)
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
  def __init__(self, player):
    CardConsoleIO.__init__(self)
    self.player = player

  def _select(self, options):
    return random.choice(options)

  def send_event(self, evt_type, payload = None):
    print(f"[{self.player}, {evt_type}] ", end="" if payload else "\n")
    ConsoleIO.send_event(self, evt_type, payload)

class FieldSocketIO(SocketIO):  
  def select_move(self):
    try:
      send_event(self.conn, EvtType.SELECT_FIELD_MOVE)
      return listen_event(self.conn, EvtType.SELECT_FIELD_MOVE_RESPONSE)
    except ConnectionError:
      self._reconnect()
      return self.select_move()

  def place(self, coords, unit):
    self.send_event(EvtType.FIELD_PLACE, {"coords": coords, "unit": unit})

  def remove(self, coords):
    self.send_event(EvtType.FIELD_REMOVE, coords)

  def select_promotion(self, unit_types):
    return self._select(unit_types, EvtType.SELECT_PROMOTION, EvtType.SELECT_PROMOTION_RESPONSE)

def add_socket_args(arg_parser):
  arg_parser.add_argument("--host", type=str, nargs="?", default="127.0.0.1", help="Server host")
  arg_parser.add_argument("--port", type=int, nargs="?", default=8888, help="Server TCP port")  

def add_cli_args(arg_parser):
  arg_parser.add_argument("--io-mode", type=lambda s: IOMode[s], choices=list(IOMode), default=IOMode.WEBSOCKET, help="Which communication is used by players")
  arg_parser.add_argument("--cpu-players", type=int, nargs="?", default=0, help="CPU players amount")
  add_socket_args(arg_parser)
  arg_parser.add_argument("--websocket-port", type=int, nargs="?", default=8080, help="Websocket port (used by websocat for TCP-WS bridge)")
  arg_parser.add_argument("--frontend-port", type=int, nargs="?", default=8000, help="HTTP server port (for static pages)")

class GameType(Enum):
  CARD = (CardSocketIO, CardConsoleIO, CardRandomIO)
  FIELD = (FieldSocketIO, None, None)

def new_players(players_number, io_mode, cpu_players, host, port, websocket_port, frontend_port, 
                game_type = GameType.CARD, after_reconnect = lambda io: io.send_event(EvtType.DEAL, io.player.cards), **_):
  socket_io_cls, console_io_cls, random_io_cls = game_type.value
  players = []
  def add_player(p, io):
    p.io = io
    players.append(p)

  def socket_enter():
    try:
      conn, _ = server.accept()
      name = listen_event(conn, EvtType.ENTER)
      return conn, name
    except ConnectionError:
      conn.close()
      return socket_enter()

  for i in range(cpu_players):
    player = Player(f"CPU{i+1}")
    add_player(player, random_io_cls(player))

  if io_mode & IOMode.CONSOLE and len(players) < players_number:
    name = input("Enter name: ")
    player = Player(name)
    add_player(player, console_io_cls())

  if len(players) < players_number:
    if io_mode & IOMode.WEBSOCKET_ONLY:
      assert websocket_port
      assert frontend_port
      assert not lib.socket.is_port_in_use(websocket_port), f"Port {websocket_port} in use"
      assert not lib.socket.is_port_in_use(frontend_port), f"Port {frontend_port} in use"

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
        conn, name = socket_enter()
        player = Player(name)
        io = socket_io_cls(player, conn, server, ios, after_reconnect)
        ios.append(io)
        add_player(player, io)

  assert len(players) == players_number, "Wrong players number"
  return players

