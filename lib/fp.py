def noop(*_, **__): pass
def id(v): return v

class Just:
  def __init__(self, v): self.v = v
  def map(self, f): return Just(f(self.v))
  def get(self): return self.v
  def __bool__(self): return bool(self.v)

class NothingCls:
  def map(self, f): return Nothing
  def get(self): return None
  def __bool__(self): return False

Nothing = NothingCls()

def maybe(v):
  return Just(v) if v is not None else Nothing

