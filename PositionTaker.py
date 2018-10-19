from BasicStuff import BasicSuper
from easyPostgresConnection import connect2IbData
from LocalBarSource import LocalBarSource
from TradeExecutor import TradeExecutor
from Predictor import Predictor
from Portfolio import Portfolio
from ExitRules import *
from Position import Position
from hashTools import __CURRENT_GIT_HASH__
from warnings import warn

__DEFAULT_DOLLAR_AMOUNT__ = 1000

def shift_left(some_list, some_thing):
    """Shifts a vector to the left"""
    del(some_list[0])
    some_list.append(some_thing)
    return some_list

def insertOneDesire(epoch, ticker, positionTaker, filename, gitHash, beLong, beShort, numShares, comments=None):
    delim = ", "
    cmd = "INSERT INTO desired_positions (epoch, ticker, position_taker, filename, githash, be_long, be_short, "
    cmd += "num_shares"
    if comments is None:
        cmd += ") VALUES ("
    else:
        cmd += ", comments) VALUES ("
    cmd += str(epoch) + delim
    cmd += str(ticker) + delim
    cmd += str(positionTaker) + delim
    cmd += str(filename) + delim
    cmd += str(gitHash) + delim
    cmd += ("t" if beLong else "f") + delim
    cmd += ("t" if beShort else "f")
    cmd += delim + comments if comments is not None else ""
    cmd += ");"
    return cmd

def beLong(numShares):
    return numShares > 0

def beShort(numShares):
    return numShares < 0

class PositionTaker(BasicSuper):
    def __init__(self, localStorageConnection, barSource):
        super().__init__(localStorageConnection, barSource)
        self.keepGoing = True
        self.newData = False
        self.enableOpen = True
        self.enableClose = True
        self.enableReversal = False
        self.enableContrarian = False
        self.desired_shares = {}
        self.actual_shares = {}
        self.portfolio = Portfolio()
        self.loserDetector = LowestPerformer()
        self.positionTakerName = "PositionTaker"
        self.positions = {}

    def addTicker(self, ticker):
        """Meant to be called by EventLoop"""
        self.desired_shares[ticker] = []
        self.actual_shares[ticker] = []
        self.positions[ticker] = None

    def openPosition(self, ticker, isBull, dollar_amt=__DEFAULT_DOLLAR_AMOUNT__):
        """Meant to be called internally"""
        price = self.barSource.closes_05_sec[ticker][-1]
        try:
            numShares = dollar_amt / price
            if not isBull:
                numShares *= -1
            # Handle the timeseries part:
            self.desired_shares[ticker].append(numShares)
            # Handle the position modeling part:
            epoch = self.localStorageConnection.bars_05_sec[ticker][-1].epoch
            price = self.localStorageConnection.closes_05_sec[ticker][-1]
            self.positions[ticker] = Position(ticker, entryTime=epoch, entryPrice=price, isBull=isBull)
        except ZeroDivisionError:
            warn("Somehow a 0 snuck into barSource.closes_05_sec[][-1]")
            self.leaveItAlone(ticker)

    def closePosition(self, ticker):
        """Meant to be called internally"""
        # Handle the timeseries part:
        self.desired_shares[ticker].append(0)
        # Handle the position modeling part:
        self.positions[ticker] = None

    def increasePosition(self, ticker, ratio=0.5):
        """Meant to be called internally"""
        assert(ratio >= 0)
        # Timeseries Part:
        newNumShares = int(self.desired_shares[ticker][-1] * (1 + ratio))
        self.desired_shares[ticker].append(newNumShares)
        # There is no position modeling part for this.

    def decreasePosition(self, ticker, ratio=0.5):
        """Meant to be called internally"""
        assert(ratio >= 0)
        # Timeseries Part:
        newNumShares = int(self.desired_shares[ticker][-1] * (1 - ratio))
        self.desired_shares[ticker].append(newNumShares)
        # There is no position modeling part for this.

    def leaveItAlone(self, ticker):
        """Call this when you want to leave it the f*** alone"""
        self.desired_shares[ticker].append(self.desired_shares[ticker][-1])
        # There is no position modeling part for this.

    def reversePosition(self, ticker):
        """Meant to be called internally"""
        # Timeseries Part:
        self.desired_shares[ticker].append(self.desired_shares[ticker][-1] * -1)
        # Position Modeling Part:
        oldDirection = self.positions[ticker].isBull
        self.positions[ticker] = Position()
        epoch = self.localStorageConnection.bars_05_sec[ticker][-1].epoch
        price = self.localStorageConnection.closes_05_sec[ticker][-1]
        self.positions[ticker] = Position(ticker, entryTime=epoch, entryPrice=price, isBull=not oldDirection)

    def sendAnyChanges(self, ticker):
        """Sends a new row to postgres if number of desired shares has changed."""
        new = self.desired_shares[ticker][-1]
        prev = self.desired_shares[ticker][-2]
        if new != prev:
            oneBar = self.barSource.bars_05_sec[ticker][-1]
            cmd = insertOneDesire(epoch=oneBar.epoch,
                                  ticker=ticker,
                                  positionTaker=self.positionTakerName,
                                  filename=__file__,
                                  gitHash=__CURRENT_GIT_HASH__,
                                  beLong=beLong(new),
                                  beShort=beShort(new),
                                  numShares=new)
            self.localStorageConnection.cursor.execute(cmd)
            self.localStorageConnection.commit()

    def process1sample(self):
        super().process1sample()

def testPositionTaker():
    conn = connect2IbData()
    bs = LocalBarSource(conn)
    uut = PositionTaker(conn, bs)
    for ticker in uut.barSource.tickers:
        print(ticker)
        print(uut.barSource.closes_daily[ticker][-5:])

if __name__=="__main__":
    pass

"""
Cycle through all tickers
Look for triggers on all tickers
Scan through positions that have been in the market for a minimum length of time.
Update any PTs
Update any SLs
Close whatever ought to be closed
    Hit PT/SL
    Poopin Around
    
If there are new triggers:
    Check that any previous positions on those stocks have been closed for minimum length of time.
    Throw a beauty contest. 
        Decide how attractive new triggers are
        Decide how attractive existing positions are
        For now that could be as simple as closing 1 lowest performer for each new trigger.
        Divide account evenly among most attractive stocks, up to 5.
"""
















