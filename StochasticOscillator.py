from BasicStuff import BasicSuper
from numpy import mean
import numpy as np
from LocalBarSource import LocalBarSource
from TechnicalIndicator import TechnicalIndicator
from MovingAverages import ExponentialMovingAverage
from GoodBar import GoodBar
from easyPostgresConnection import connect2IbData

class StochasticOscillator(TechnicalIndicator):
    """OK to pass in None for vec in this one, since it isn't used."""
    def __init__(self, localStorageConnection, barSource:LocalBarSource, k_period, d_period, decayRate=None):
        """Make sure vec is a dictionary of lists keyed by ticker in an injected dependency, such as
        BarSourceInst.closes_05_sec. That way __call__ accesses vec["ticker"], which is a list."""
        super().__init__(localStorageConnection, barSource=barSource)
        self.k_period = k_period
        self.k_vec = {}
        self.d_averager = ExponentialMovingAverage(localStorageConnection, barSource, d_period, self.k_vec)
        self.loadTickers()

    def loadTickers(self):
        for ticker in self.barSource.lows_05_sec.keys():
            self.k_vec[ticker]=[0.5]*self.k_period

    def __call__(self, *args, **kwargs):
        """Returns a tuple (divisionWorked, result)"""
        ticker = kwargs["ticker"]
        if "d" in kwargs.keys() and kwargs["d"] == True:
            return (True, self.d_averager(ticker=ticker))
        else:
            lowestLow = min(self.barSource.lows_05_sec[ticker][-self.k_period:])
            highestHigh = max(self.barSource.highs_05_sec[ticker][-self.k_period:])
            latestClose = self.barSource.closes_05_sec[ticker][-1]
            # print("%0.4f    %0.4f    %0.4f"%(lowestLow, highestHigh, latestClose))
            try:
                k = (latestClose - lowestLow) / (highestHigh - lowestLow)
                if len(self.k_vec[ticker]) >= self.k_period:
                    del(self.k_vec[ticker][0])
                self.k_vec[ticker].append(k if k > 1E-3 else 1E-3)
                return (True, k)
            except ZeroDivisionError:
                return (False, None)

    def get_k(self, ticker):
        """It's better to use __call__ with only the ticker parameter."""
        return self.__call__(ticker=ticker)

    def get_d(self, ticker):
        """It's better to just use __call__ as in the example below:"""
        return self.__call__(ticker=ticker, d=True)

def testStochasticOscillator01():
    conn = connect2IbData()
    barSource = LocalBarSource(conn)
    uut = StochasticOscillator(conn, barSource, 20, 10, vec=None)
    stupidBar = GoodBar(ticker="TEST", timeframe="5 sec")
    stupidBar.high = 110
    stupidBar.low = 90
    stupidBar.close= 100
    ticker = stupidBar.ticker
    for m in range(20):
        barSource.replaceBar(stupidBar)
    stupidBar.close = 90
    for m in range(20):
        barSource.replaceBar(stupidBar)
        success, k = uut(ticker=ticker, d=False)
        if success:
            throwaway, d = uut(ticker=ticker, d=True)
            print("      Min:  ", min(barSource.lows_05_sec[ticker][-20:]), \
                  "      Max:  ", max(barSource.highs_05_sec[ticker][-20:]), \
                  "      K:   %0.4f"%k,\
                  "      D:   %0.4f"%d)
        else:
            print("Narrowly avoided division by zero. That was a close one!")
        stupidBar.close += 2
        if stupidBar.close < stupidBar.low:
            stupidBar.low = stupidBar.close
        elif stupidBar.close > stupidBar.high:
            stupidBar.high = stupidBar.close

    print("\n"*5)
    for m in range(20):
        barSource.replaceBar(stupidBar)
        success, k = uut(ticker=ticker, d=False)
        if success:
            throwaway, d = uut(ticker=ticker, d=True)
            print("      Min:  ", min(barSource.lows_05_sec[ticker][-20:]), \
                  "      Max:  ", max(barSource.highs_05_sec[ticker][-20:]), \
                  "      K:   %0.4f"%k,\
                  "      D:   %0.4f"%d)
        else:
            print("Narrowly avoided division by zero. That was a close one!")
        stupidBar.close -= 3
        if stupidBar.close < stupidBar.low:
            stupidBar.low = stupidBar.close
        elif stupidBar.close > stupidBar.high:
            stupidBar.high = stupidBar.close


def testStochasticOscillator02():
    conn = connect2IbData()
    barSource = LocalBarSource(conn)
    uut = StochasticOscillator(conn, barSource, 20, 10, vec=None)
    stupidBar1 = GoodBar(ticker="AAPL", timeframe="5 sec")
    stupidBar1.high = 110
    stupidBar1.low = 90
    stupidBar1.close= 100

    stupidBar2 = GoodBar(ticker="BA", timeframe="5 sec")
    stupidBar2.high = 300
    stupidBar2.low = 260
    stupidBar2.close = 280

    ticker1 = stupidBar1.ticker
    ticker2 = stupidBar2.ticker

    for m in range(20):
        barSource.replaceBar(stupidBar1)
        barSource.replaceBar(stupidBar2)
    stupidBar1.close = 90
    stupidBar2.close = 300
    for m in range(20):
        barSource.replaceBar(stupidBar1)
        barSource.replaceBar(stupidBar2)
        success1, k1 = uut(ticker=ticker1, d=False)
        success2, k2 = uut(ticker=ticker2, d=False)

        if success1:
            throwaway, d1 = uut(ticker=ticker1, d=True)
            print("1      Min:  %03d" % min(barSource.lows_05_sec[ticker1][-20:]), \
                  "      Max:  %03d" % max(barSource.highs_05_sec[ticker1][-20:]), \
                  "    Close:  %03d" % barSource.closes_05_sec[ticker1][-1],\
                  "      K:   %0.4f" % k1, \
                  "      D:   %0.4f" % d1)
        else:
            print("Narrowly avoided division by zero. That was a close one!")


        if success2:
            throwaway, d2 = uut(ticker=ticker2, d=True)
            print("2      Min:  %03d" % min(barSource.lows_05_sec[ticker2][-20:]), \
                  "      Max:  %03d" % max(barSource.highs_05_sec[ticker2][-20:]), \
                  "    Close:  %03d" % barSource.closes_05_sec[ticker2][-1], \
                  "      K:   %0.4f" % k2, \
                  "      D:   %0.4f" % d2)
        else:
            print("Narrowly avoided division by zero. That was a close one!")

        stupidBar1.close += 1
        stupidBar2.close -= 1


if __name__=="__main__":
    testStochasticOscillator02()




















