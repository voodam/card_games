def rotate(l, start_element):
  i = l.index(start_element)
  l[:] = l[i:] + l[:i]

def chunks(l, chunks_number):
  length = len(l)
  assert length % chunks_number == 0, f"{length} % {chunks_number} != 0"
  chunk_size = length // chunks_number
  return [l[i:i + chunk_size] for i in range(0, length, chunk_size)]

def get(l, idx, default = None):
  try: return l[idx]
  except IndexError: return default

def make(v):
  if not isinstance(v, list): v = [v]
  return v

def remove_if_exists(l, v):
  if v in l: l.remove(v)

