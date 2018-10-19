from easyPostgresConnection import connect2IbData
from BasicStuff import BasicSuper
import time

class NewBarDetector(BasicSuper):
    def __init__(self, localStorageConnection, barSource, **kwargs):
        super().__init__(localStorageConnection, barSource, **kwargs)
        self.newBarAvailable = {}
        self.lastAvailableEpoch = {}
        self.numBarsReturned = {}
        self.mostRecentlyAcquiredEpoch = {}

        if "naptime" in kwargs.keys():
            self.naptime = kwargs["naptime"]
        else:
            self.naptime = 1


    def add_ticker(self, ticker):
        self.newBarAvailable[ticker] = False
        self.lastAvailableEpoch[ticker] = 0
        self.numBarsReturned[ticker] = 0
        self.mostRecentlyAcquiredEpoch[ticker] = []


    def test_for_new_bars(self, ticker):
        """Tests for new bars once. Intended to be called by EventLoop."""
        latestEpoch = self.lastAvailableEpoch[ticker]
        cmd = "SELECT epoch FROM bars_5_sec WHERE epoch > " + str(latestEpoch) + ";"
        self.curs.execute(cmd)
        results = self.curs.fetchall()
        if len(results) > 0:
            self.newBarAvailable[ticker] = True
            self.lastAvailableEpoch[ticker] = results[-1]
            self.numBarsReturned[ticker] = len(results)
            self.mostRecentlyAcquiredEpoch[ticker] = results
        else:
            self.newBarAvailable[ticker] = False
            self.lastAvailableEpoch[ticker] = None
            self.numBarsReturned[ticker] = 0
            self.mostRecentlyAcquiredEpoch[ticker] = []




























