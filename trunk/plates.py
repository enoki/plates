import Tkinter
import math
import re

def number_as_word(number):
  return { 1 : 'one', 2 : 'two' }[number]

def plural_ending(number):
  if number == 1:
    return ''
  else:
    return 's'

class MessageError(Exception):
  def __init__(self, message):
    self.message = message

  def __str__(self):
    return self.message

class LogicError(MessageError):
  def __init__(self, message):
    MessageError.__init__(self, message)

class NeedMoreValuesError(LogicError):
  def __init__(self, num_needed):
    LogicError.__init__(self,
        "Need at least %s value%s!" % (number_as_word(num_needed), \
                                       plural_ending(num_needed)))

class SyntaxError(MessageError):
  def __init__(self, message):
    MessageError.__init__(self, message)

class AtomNotFoundError(SyntaxError):
  def __init__(self, atom):
    SyntaxError.__init__(self, "Command or variable %s not found!" % atom)

class Preprocessor:
  def __init__(self):
    self.comment_regex = re.compile(r'#.*')

  def preprocess(self, atom):
    atom = self.comments_stripped(atom)
    atom = atom.strip()
    return atom

  def comments_stripped(self, atom):
    return self.comment_regex.sub('', atom)

class Parser:
  def __init__(self):
    self.log = []
    self.stack = []

    self.operators = {
        '+' : self.add,
        '-' : self.subtract,
        '*' : self.multiply,
        '/' : self.divide,
        '^' : self.power,
        }

    self.commands = {
        'drop' : self.pop_one,
        'swap' : self.swap,
        'dup' : self.dup,
        'clear' : self.clear,
        'negate' : self.negate,
        }

    self.variables = {
        'pi' : math.pi,
        'e' : math.e
        }

    self.pp = Preprocessor()

  def stack_trace(self):
    " Returns a string describing the stack. "
    trace = "| <Stack> |  Log  |\n\n"
    number = 0

    for value in self.stack:
      trace += str(number)
      trace += ":\t\t\t"
      trace += str(value)
      trace += "\n"
      number += 1

    return trace

  def log_trace(self):
    " Returns a string describing the log. "
    log = "|  Stack  | <Log> |\n\n"
    number = 0

    for action in self.log:
      log += str(number)
      log += ":\t\t\t"
      log += str(action)
      log += "\n"
      number += 1

    return log

  def parse(self, atom):
    value = None

    atom = self.pp.preprocess(atom)

    if atom in self.operators:
      value = self.operators[atom]()

    elif atom in self.commands:
      self.commands[atom]()

    elif atom in self.variables:
      value = self.variables[atom]

    elif len(atom) <= 0:
      self.repeat_last()
      return

    else:
      try:
        value = float(atom)
      except ValueError, e:
        raise AtomNotFoundError(atom)

    if value is not None:
      self.push(value)

    self.log.append(atom)

  def peek_top(self):
    """ Returns the top of the stack.
        Raises an error if the stack is empty. """
    stack = self.stack

    if len(stack) < 1:
      raise NeedMoreValuesError(1)

    return stack[-1]

  def repeat_last(self):
    """ Repeats the last action (i.e. command or operation).
        Raises an error if there are no previous actions. """

    log = self.log

    if len(log) < 1:
      raise NeedMoreValuesError(1)

    self.parse(self.log[-1])

  def pop_one(self):
    " Pops the top value off the stack and returns it. "
    stack = self.stack
  
    if len(stack) < 1:
      raise NeedMoreValuesError(1)

    return stack.pop()

  def pop_two(self):
    "Pops top two off the stack and returns them as (left, right)."
    stack = self.stack

    if len(stack) < 2:
      raise NeedMoreValuesError(2)

    right = stack.pop()
    left = stack.pop()

    return (left, right)

  def swap(self):
    "Swaps the top two values on the stack."
    stack = self.stack

    if len(stack) < 2:
      raise NeedMoreValuesError(2)

    (stack[-1], stack[-2]) = (stack[-2], stack[-1])

  def dup(self):
    value = self.peek_top()
    self.push(value)

  def clear(self):
    self.stack = []

  def push(self, value):
    self.stack.append(value)

  def negate(self):
    value = self.pop_one()
    self.push(-value)

  def add(self):
    (left, right) = self.pop_two()
    return left + right

  def subtract(self):
    (left, right) = self.pop_two()
    return left - right

  def multiply(self):
    (left, right) = self.pop_two()
    return left * right

  def divide(self):
    (left, right) = self.pop_two()
    return left / right

  def power(self):
    (left, right) = self.pop_two()
    return left ** right

class Output(Tkinter.Text):
  def __init__(self, parent):
    Tkinter.Text.__init__(self, parent)
    self.config(state=Tkinter.NORMAL)
    self.config(takefocus=0)

  def report(self, text):
    " Same as tell, but keeps scrolling. "
    self.tell(text)
    self.see_end()

  def tell(self, text):
    self.clear()
    self.say(text)

  def clear(self):
    self.config(state=Tkinter.NORMAL)
    self.delete('1.0', Tkinter.END)
    self.config(state=Tkinter.DISABLED)

  def say(self, text):
    self.config(state=Tkinter.NORMAL)
    self.insert(Tkinter.END, text + "\n")
    self.config(state=Tkinter.DISABLED)

  def see_end(self):
    self.see(Tkinter.END)


class App:
  def __init__(self, parent):
    self.parent = parent

    self.parent.title('Plates')

    self.output = Output(parent)
    self.output.pack()

    self.message = Tkinter.Label(parent)
    self.message.pack()

    self.showing_log = False

    self.entry = Tkinter.Entry(parent)
    self.entry.focus_force()
    self.entry.bind("<Return>", lambda event: self.do_command())
    self.entry.bind("<Tab>", lambda event: self.toggle_log_view())
    self.entry.bind("<Escape>", lambda event: self.quit())
    self.entry.bind("<Control-k>", lambda event: self.do('drop'))
    self.entry.bind("<Control-s>", lambda event: self.do('swap'))
    self.entry.bind("<Control-n>", lambda event: self.do('negate'))
    self.entry.bind("<Up>", lambda event: self.recall_backward())
    self.entry.bind("<Key>", self.on_key_press)
    self.entry.pack()

    self.parser = Parser()

    self.report()

  def do_command(self):
      text = self.entry.get()
      self.do(text)

  def do(self, command):
      self.parse(command)
      self.report()
      self.entry.delete(0, Tkinter.END)

  def parse(self, text):
    try:
      self.parser.parse(text)
    except MessageError, e:
      self.message.config(text=str(e))

  def toggle_log_view(self):
    self.showing_log = not self.showing_log
    self.report()

  def report(self):
    if self.showing_log:
      self.output.report(self.parser.log_trace())
    else:
      self.output.report(self.parser.stack_trace())

  def on_key_press(self, event):
    self.message.config(text='')

  def recall_backward(self):
    if len(self.parser.log) > 0:
      # XXX this is too simplistic
      # how do we recall history from farther back?
      self.entry.delete(0, Tkinter.END)
      self.entry.insert(0, self.parser.log[-1])

  def quit(self):
    self.parent.destroy()

root = Tkinter.Tk()
app = App(root)
root.mainloop()
