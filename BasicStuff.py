"""Contains things will be helpful to all modules."""

from abc import ABCMeta


class BasicSuper:
    """This class is designed to force all child classes to be iterators."""
    def __init__(self, localStorageConnection, barSource, **kwargs):
        self.localStorageConnection = localStorageConnection
        self.curs = self.localStorageConnection.cursor()
        self.tickers = []
        self.epochs = []
        self.barSource = barSource
        self.numSamplesForValidity=1000
        self.numSamplesProcessed=0
        self.allInjectedThings=[]
        self.done = False

    def ditch_attr(self, some_attr):
        """Returns True if some_attr was removed from self; False otherwise."""
        if hasattr(self, some_attr):
            delattr(self, some_attr)
            return True
        return False

    def is_anything_done(self):
        """Retrieves """
        if self.done:
            return True
        for m in self.allInjectedThings:
            if m.done:
                return True
        return False

    def process1sample(self):
        self.numSamplesProcessed += 1

    def isValid(self):
        return self.numSamplesProcessed >= self.numSamplesForValidity

    def inject_a_thing(self, something):
        self.allInjectedThings.append(something)

    def add_ticker(self, ticker):
        for thing in self.allInjectedThings:
            if hasattr(thing, "add_ticker"):
                thing.add_ticker(ticker)


