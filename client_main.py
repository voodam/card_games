import socket
import argparse
from player_io import EvtType
import player_io
from util_sock import send_event, listen_events

parser = argparse.ArgumentParser(description="Socket client")
player_io.add_socket_args(parser)
args = parser.parse_args()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
  s.connect((args.host, args.port))
  name = input("Enter name: ")
  send_event(s, EvtType.ENTER, name)
  io = player_io.CardConsoleIO()

  while True:
    for evt_type, payload in listen_events(s, list(EvtType)):
      if evt_type == EvtType.SELECT_YESNO:
        yesno = io.select_yesno(payload)
        send_event(s, EvtType.SELECT_YESNO_RESPONSE, yesno)
      elif evt_type == EvtType.SELECT_BID:
        bid = io.select_bid(**payload)
        send_event(s, EvtType.SELECT_BID_RESPONSE, bid)
      elif evt_type == EvtType.SELECT_CARD:
        card = io.select_card(payload)
        send_event(s, EvtType.SELECT_CARD_RESPONSE, card)
      elif evt_type == EvtType.SELECT_SUIT:
        suit = io.select_suit(payload)
        send_event(s, EvtType.SELECT_SUIT_RESPONSE, suit)
      else:
        io.send_event(evt_type, payload)

