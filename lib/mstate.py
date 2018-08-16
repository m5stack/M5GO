import utime, gc

class MState():
  def __init__(self, start=None, loop=None, end=None):
    self.on_start = start
    self.on_loop = loop
    self.on_end = end
    self.context = {}

  def start(self):
    if self.on_start:
      self.on_start(self.context)

  def loop(self):
    if self.on_loop:
      self.on_loop(self.context)

  def end(self):
    if self.on_end:
      self.on_end(self.context)
      gc.collect()


class MStateManager():
  def __init__(self):
    self.state = None
    self.prev_state = ''
    self.next_state = None
    self.mtask = {}

  def start(self, state):
    self.state = state
    self.mtask[self.state].start()

  def stop(self):
    self.mtask[self.state].end()
    self.state = None

  def register(self, state, mtask):
    self.mtask[state] = mtask
    self.mtask[state].context['mstate'] = self

  def unregister(self, state):
    self.mtask.pop(state)

  def nextState(self, state=None):
    if state:
      self.next_state = state
    else:
      return self.next_state

  def change(self, state):
    print('[%d] '%utime.ticks_ms() + 'State change: '+ self.state + ' ===> '+ state)
    self.mtask[self.state].end()
    self.prev_state = self.state
    self.state = state
    self.mtask[self.state].start()

  def run(self):
    if self.state:
      self.mtask[self.state].loop()
      return True
    else:
      return False