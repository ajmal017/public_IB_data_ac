from PositionTaker import PositionTaker
import time
from copy import deepcopy
from SleepManager import SleepManager

class EventLoop:
    def __init__(self):
        self.keepGoing = True
        self.posTaker = None
        self.newData = True

    def run(self):
        raise ValueError("Dude: Why is this not overloaded? Seriously!")

    def isThereMore(self):
        raise ValueError("Overload this.")

class HistoricalLoop(EventLoop):
    def __init__(self, totalBars, posTaker:PositionTaker):
        super().__init__()
        self.posTaker = posTaker
        self.minEpoch = None
        self.maxEpoch = None
        self.tickersToScan=[]
        self.barsDone = 0
        self.totalBars = totalBars

    def addTicker(self, ticker):
        assert(isinstance(ticker, str) or isinstance(ticker, list))
        if isinstance(ticker, str):
            self.tickersToScan.append(ticker)
        else:
            self.tickersToScan.extend(ticker)

    def isThereMore(self, **kwargs):
        return self.barsDone < self.totalBars

    def run(self):
        while self.isThereMore():
            self.posTaker.process1sample()


class RealTimeLoop(EventLoop):
    def __init__(self, posTaker:PositionTaker, barGetter, fun2call):
        self.posTaker = posTaker
        self.dataIds = []               # Extract from IB client
        self.tickers = {}               # Extract this from IB client
        self.reqIdServiced = {}         # Keyed by epoch
        self.numDataSubscriptions = 0
        self.fun2call=fun2call
        self.barGetter = barGetter
        self.sleepMgr = SleepManager()

    def copyTickersFromLowerLevel(self, someObj):
        """Copies tickers and reqIds from any object having those two fields."""
        self.tickers = deepcopy(someObj.tickers)
        self.dataIds = deepcopy(someObj.dataIds)

    def addTicker(self, reqId, ticker):
        """Call this once for each ticker in the real time data subscription"""
        self.dataIds.append(reqId)
        self.tickers[reqId]=ticker

    def addEpoch(self, epoch):
        """Call this once for each new batch of 5 s bars."""
        self.reqIdServiced[epoch] = {}
        for reqId in self.dataIds:
            self.reqIdServiced[epoch][reqId] = False

    def pollForNewBars(self):
        for ticker in self.tickers:
            pass

    def run(self):
        while self.posTaker.keepGoing:
            for reqId in self.dataIds:
                oneBar = self.barGetter.useBar(reqId)
                self.barGetter.ibClient.servicedBar[reqId] = True
                if oneBar is None:
                    time.sleep(0.003)
                else:
                    self.fun2call(reqId)
