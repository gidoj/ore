'''Simple Completer class
    
    - may change implementation later  to deal with module specific
      completion tasks (multiple completion rules in a single completer
      instance)
'''

class OreCompleter(object):

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if (state == 0):
            if (text):
                self.matches = [m for m in self.options if m.startswith(text)]
            else:
                # if no text, then return everything
                self.matches = self.options

        try:
            return self.matches[state]
        except IndexError:
            return None
