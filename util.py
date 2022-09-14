import fcntl
import os
import json
import socket
import errno
from enum import Enum

def noop(*_, **__):
  pass

def id(v):
  return v

class TextColor(Enum):
  Black = 30
  Red = 31
  Green = 32
  Yellow = 33
  Blue = 34
  Magenta = 35
  Cyan = 36
  White = 37

  def __str__(self):
    return str(self.value)

class TextStyle(Enum):
  Nothing = 0
  Bold = 1
  Weak = 2
  Italic = 3
  Underscore = 4
  Blink = 5
  ReverseColor = 7
  Concealed = 8
  Strike = 9

  def __str__(self):
    return str(self.value)

def colored(text, color, style = TextStyle.Nothing):
  return f"\33[{style};{color}m{text}\33[m"

def make_list(v):
  if not isinstance(v, list):
    v = [v]
  return v

def list_rotate(l, start_element):
  i = l.index(start_element)
  l[:] = l[i:] + l[:i]

def list_chunks(l, chunks_number):
  length = len(l)
  assert length % chunks_number == 0
  chunk_size = length // chunks_number
  return [l[i:i + chunk_size] for i in range(0, length, chunk_size)]

def opposite_in_pair(pair, obj):
  assert len(pair) == 2
  return pair[1] if pair[0] == obj else pair[0]

def json_dumps(obj):
  def f(v):
    if isinstance(v, set):
      return list(v)
    else:
      return v.to_json()

  return json.dumps(obj, default=f)

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
    if code == errno.EAGAIN or code == errno.EWOULDBLOCK:
      return True
    else:
      raise e
  finally:
    if is_blocking:
      conn.setblocking(True)

