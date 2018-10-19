from BasicStuff import BasicSuper
from numpy import mean
import numpy as np
from LocalBarSource import LocalBarSource
from TechnicalIndicator import TechnicalIndicator
from easyPostgresConnection import connect2IbData
from ibapi.common import BarData

class SimpleMovingAverage(TechnicalIndicator):
    """For vec, pass in BarSource.someListOfPrices. It is important that vec
    be a list of prices, not a list of bars."""
    def __init__(self, localStorageConnection, barSource:LocalBarSource, period, vec):
        super().__init__(localStorageConnection, barSource=barSource)
        self.period = period
        self.vec = vec

    def __call__(self, *args, **kwargs):
        ticker = kwargs["ticker"]
        return mean(self.vec[ticker][-self.period:])

def testSimpleMovingAverage01():
    conn = connect2IbData()
    barSource = LocalBarSource(conn)
    uut = SimpleMovingAverage(conn, barSource, 15, barSource.closes_05_sec)
    stupidBar = BarData() # all fields are 0 by default
    stupidBar.close = 17
    stupidBar.open = 0
    stupidBar.high = 0
    stupidBar.low = 0
    setattr(stupidBar, "ticker", "AAPL")
    setattr(stupidBar, "timeframe", "5 sec")
    for m in range(100):
        barSource.replaceBar(stupidBar)
    for m in range(10):
        barSource.replaceBar(stupidBar)
        print(uut(ticker='AAPL'))
    print("Length of vector: ", len(barSource.closes_05_sec["AAPL"]))

def testSimpleMovingAverage02():
    conn = connect2IbData()
    barSource = LocalBarSource(conn)
    uut = SimpleMovingAverage(conn, barSource, 15, barSource.closes_05_sec)
    stupidBar = BarData() # all fields are 0 by default
    stupidBar.close = 17
    stupidBar.open = 0
    stupidBar.high = 0
    stupidBar.low = 0
    setattr(stupidBar, "ticker", "AAPL")
    setattr(stupidBar, "timeframe", "5 sec")
    for m in range(100):
        barSource.replaceBar(stupidBar)
    for m in range(10):
        barSource.replaceBar(stupidBar)
        print(uut(ticker='AAPL'))
    print("Length of vector: ", len(barSource.closes_05_sec["AAPL"]))

def fourplaces(x):
    return "%04f" % x

def locatePercentGoal(numel, goalPercent=10, tol=1E-6, initDecayRate=0.9, maxAttempts=1000, printStuff=False):
    """Returns a decay rate that will make the earliest element goalPercent as
    influential as the latest element."""
    changeRate=0.08
    changeRateChangeRate=0.02
    decayRate=initDecayRate
    attempts=0
    try:
        goalRatio = goalPercent / 100
    except:
        print("Exception")
    for m in range(maxAttempts):
        y = decayRate ** numel
        if goalRatio - tol < y < goalRatio + tol:
            return decayRate
        elif y < goalRatio:
            decayRate *= (1 + changeRate)
        elif y > goalRatio:
            decayRate *= (1 - changeRate)
        changeRate = changeRate * (1-changeRateChangeRate)
        t = "    "
        if printStuff:
            print(fourplaces(y), t, fourplaces(goalRatio-tol), t, fourplaces(goalRatio+tol), t, fourplaces(decayRate), t, fourplaces(changeRate), t, m)
    return decayRate


def emaWeightingFunction(numel, goalPercent=10, printStuff=False):
    decayRate = locatePercentGoal(numel, goalPercent, printStuff=printStuff)
    y = [1]
    for m in range(1, numel):
        y.insert(0, y[0]*decayRate)
    if printStuff:
        print("\n\n")
        print(y)
        print("\n\n")
    s = sum(y)
    if printStuff:
        print(s)
    z = []
    for m in y:
        z.append(m / s)
    if printStuff:
        print("\n\n")
        print(z)
        print("\n\n")
    return z
    # return np.asarray(y)

class ExponentialMovingAverage(TechnicalIndicator):
    def __init__(self, localStorageConnection, barSource:LocalBarSource, period, vec):
        """Make sure vec is a dictionary of lists keyed by ticker in an injected dependency, such as
        BarSourceInst.closes_05_sec. That way __call__ accesses vec["ticker"], which is a list."""
        super().__init__(localStorageConnection, barSource=barSource)
        self.period = period
        self.weights = emaWeightingFunction(period, goalPercent=8)
        self.vec = vec

    def __call__(self, *args, **kwargs):
        ticker = kwargs['ticker']
        prices = np.asarray(self.vec[ticker][-self.period:])
        return np.dot(prices, self.weights)

def testExponentialMovingAverage01():
    conn = connect2IbData()
    barSource = LocalBarSource(conn)
    uut = ExponentialMovingAverage(conn, barSource, 15, barSource.closes_05_sec)
    stupidBar = BarData() # all fields are 0 by default
    stupidBar.close = 0
    stupidBar.open = 0
    stupidBar.high = 0
    stupidBar.low = 0
    setattr(stupidBar, "ticker", "AAPL")
    setattr(stupidBar, "timeframe", "5 sec")
    for m in range(100):
        barSource.replaceBar(stupidBar)
    for m in range(10):
        stupidBar.close += 1
        barSource.replaceBar(stupidBar)
        print(stupidBar.close, "    ", uut(ticker='AAPL'))
    print("Length of vector: ", len(barSource.closes_05_sec["AAPL"]))


if __name__=="__main__":
    testExponentialMovingAverage01()

















