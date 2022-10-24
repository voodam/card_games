import fcntl
import os
import socket
import errno
import json

import lib.util as util
from lib.fp import id

def is_port_in_use(port):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    return s.connect_ex(("localhost", port)) == 0

def is_socket_alive(conn):
  if conn.fileno() < 0:
    return False

  flags = fcntl.fcntl(conn, fcntl.F_GETFL)
  is_blocking = flags & os.O_NONBLOCK
  if is_blocking:
    conn.setblocking(False)

  try:
    data = conn.recv(1024)
    if not data:
      return False
  except socket.error as e:
    code = e.args[0]
    if code in (errno.EAGAIN, errno.EWOULDBLOCK):
      return True
    else:
      raise e
  finally:
    if is_blocking:
      conn.setblocking(True)

def send_event(conn, evt_type, payload = None):
  event = {
    "evt_type": evt_type,
    "payload": payload
  }
  bytes = str.encode(util.json_dumps(event) + "\n")
  conn.sendall(bytes)

def listen_events(conn, evt_types):
  assert len(evt_types) >= 1
  evt_from_json = getattr(evt_types[0].__class__, "from_json", id)

  def result(j):
    event = json.loads(j)
    evt_type = evt_from_json(event["evt_type"])
    assert evt_type in evt_types
    payload_from_json = getattr(evt_type, "payload_from_json", id)
    payload = payload_from_json(event.get("payload"))
    return evt_type, payload

  data = conn.recv(4096)
  if not data:
    raise ConnectionError()
  jsons = data.decode().strip().split("\n")
  return map(result, jsons)

def listen_event(conn, evt_type):
  [_, payload], = listen_events(conn, [evt_type])
  return payload

