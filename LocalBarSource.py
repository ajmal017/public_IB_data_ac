from ibapi.common import BarData
from barTools import epoch2human
from barTools import human2epoch
from easyPostgresConnection import connect2IbData
from easyPostgresConnection import barTableName
from BasicStuff import BasicSuper
from GoodBar import GoodBar
from delim import EOL
from delim import DELIM
from delim import END_QUERY
from numpy import random

ONE_MINUTE = 60
EIGHT_HOURS = 3600*8 # 8 hrs measured in seconds
TWENTY_FOUR_HOURS = 3600*24
DECEMBER_31_2075 = human2epoch("2075-12-31 23:59:59")
JANUARY_01_1990 = human2epoch("1990-01-01 00:00:00")

def sanctifyWhichTable(whichTable, useHyphens=False):
    """Forces whichTable into a nice soft Procrustean bed."""
    if whichTable == "05 sec" or whichTable == "5 sec":
        if useHyphens:
            return "5_sec"
        else:
            return "5 sec"
    elif whichTable == "15 min":
        if useHyphens:
            whichTable = "15_min"
        else:
            whichTable = "15 min"
    elif whichTable == "daily":
        return "daily"
    else:
        raise ValueError("Unrecognized table name")
        return None

def getEarliestEpoch(curs, ticker, whichTable, minEpoch=JANUARY_01_1990):
    """Returns the earliest epoch available for a ticker."""
    if whichTable == "05 sec":
        whichTable = "5_sec"
    elif whichTable == "15 min":
        whichTable = "15_min"
    elif whichTable == "daily":
        pass
    else:
        raise ValueError("Unrecognized table name")
    cmd = "SELECT epoch FROM bars_" + whichTable + " WHERE ticker='" + ticker + "' AND"
    cmd += " epoch>" + str(minEpoch) + " "
    cmd += " ORDER BY epoch LIMIT 1;"
    curs.execute(cmd)
    results = curs.fetchall()
    if len(results) > 0:
        return results[0][0]
    return -1

def getNextHigherEpoch(curs, ticker, whichTable, minEpoch):
    """Returns the next higher epoch available for a ticker."""
    if whichTable == "05 sec":
        whichTable = "5_sec"
    elif whichTable == "15 min":
        whichTable = "15_min"
    elif whichTable == "daily":
        pass
    else:
        raise ValueError("Unrecognized table name")
    cmd = "SELECT epoch FROM bars_" + whichTable + " WHERE ticker='" + ticker
    cmd += "' AND epoch>" + str(minEpoch)
    cmd += " ORDER BY epoch LIMIT 5;"
    curs.execute(cmd)
    results = curs.fetchall()
    if len(results) > 4:
        return results[4][0]
    return -1

def getBarsWithMinimumEpoch(curs, ticker, whichTable, epoch):
    """Use this for historical."""
    if whichTable == "05 sec":
        whichTable = "5_sec"
    elif whichTable == "15 min":
        whichTable = "15_min"
    elif whichTable == "daily":
        pass
    else:
        raise ValueError("Unrecognized table name")
    cmd = "SELECT epoch, open, close, high, low, volume FROM bars_" + whichTable + " WHERE ticker='" + ticker + "' AND "
    cmd += "epoch>" + str(epoch) + " "
    cmd += "ORDER BY epoch;"
    curs.execute(cmd)
    results = curs.fetchall()
    return results

def getBarWithExactEpoch(curs, ticker, whichTable, epoch):
    """Use this for real time."""
    if whichTable == "05 sec":
        whichTable = "5_sec"
    elif whichTable == "15 min":
        whichTable = "15_min"
    elif whichTable == "daily":
        pass
    else:
        raise ValueError("Unrecognized table name")
    cmd = "SELECT epoch, open, close, high, low, volume FROM bars_" + whichTable + " WHERE ticker='" + ticker + "' AND "
    cmd += "epoch=" + str(epoch) + " "
    cmd += "ORDER BY epoch;"
    curs.execute(cmd)
    results = curs.fetchall()
    return results

class LocalBarSource(BasicSuper):
    def __init__(self, localStorageConnection, minEpoch=0, addDummyData=False):
        super().__init__(localStorageConnection, barSource=self)
        self.curs           = localStorageConnection.cursor()
        self.minEpoch       = {}
        self.tickers        = []
        self.bars_daily     = {}
        self.bars_15_min    = {}
        self.bars_05_sec    = {}
        self.defaultMinEpoch_05_sec = 0
        self.defaultMinEpoch_15_min = 0
        self.defaultMinEpoch_daily = 0
        self.desired_num_daily      = 250
        self.desired_num_15_min     = 100
        self.desired_num_05_sec     = 2160  # 3 hrs by default

        self.closes_daily   = {}
        self.highs_05_sec   = {}
        self.lows_05_sec    = {}
        self.closes_05_sec  = {}
        self.highs_15_min   = {}
        self.lows_15_min    = {}
        self.closes_15_min  = {}
        self.addDummyData = addDummyData

        # Initialize Data Structures:
        self.discoverTickers()
        self.initializeTickers()
        self.loadLocallyStored()

    def discoverTickers(self, minEpoch=0, maxEpoch=DECEMBER_31_2075):
        """Extracts bottommost epoch from data_subscriptions table, and appends tickers
        to a list until epoch decreases more than 10 seconds. I used to have it so that
        algorithm terminates as soon as epoch changes, but that is brittle because
        data reqs can span multiple seconds. So there's a tolerance.
        This assumes that records are in order of epoch, which seems reasonable since time
        increases monotonically... at least... for mere mortals. MUAHAHAHAHAHA!!!"""
        # self.tickers = ["JPM", "KO", "LOW", "MCD", "MMM", "KO", "LOW", "JNJ", "AAPL", "PFE", \
        #                 "GS", "HPQ", "SBUX", "MSFT", "BA", "BAC"]
        cmd = "SELECT DISTINCT ticker FROM bars_5_sec WHERE ticker != '__XYZ';"
        self.curs.execute(cmd)
        for row in self.curs.fetchall():
            oneTicker = row[0]
            self.tickers.append(oneTicker)
        if self.addDummyData:
            self.tickers.append("__XYZ")

    def initializeTickers(self):
        """Call this after ticker discovery to set up the dictionaries keyed by ticker."""
        for ticker in self.tickers:
            self.addTicker(ticker)

    def loadLocallyStored(self):
        """Initializes vectors with data from database"""
        self.loadHistorical("daily")
        self.loadHistorical("15 min")
        self.loadHistorical("05 sec")

    def addTicker(self, ticker):
        self.bars_daily[ticker]     = []
        self.bars_15_min[ticker]    = []
        self.bars_05_sec[ticker]    = []
        self.minEpoch[ticker]       = {}
        self.minEpoch[ticker]["05 sec"] = getEarliestEpoch(self.curs, ticker, "05 sec")
        self.minEpoch[ticker]["15 min"] = getEarliestEpoch(self.curs, ticker, "15 min")
        self.minEpoch[ticker]["daily"] = getEarliestEpoch(self.curs, ticker, "daily")
        self.closes_daily[ticker]   = []
        self.highs_05_sec[ticker]   = []
        self.lows_05_sec[ticker]    = []
        self.closes_05_sec[ticker]  = []
        self.highs_15_min[ticker]   = []
        self.lows_15_min[ticker]    = []
        self.closes_15_min[ticker]  = []

        # Epoch trackers:
        self.nowDaily = None
        self.now15Min = None
        self.now05Sec = None
        self.prevHr = 4

    def getBars(self, ticker, timeframe, numel):
        """Returns a list of bars numel elements back from now."""
        if timeframe == "5" or timeframe == "05 sec" or timeframe == "5 sec":
            return self.bars_05_sec[ticker][-numel:]
        elif timeframe == "15" or timeframe == "15 min":
            return self.bars_15_min[ticker][-numel:]
        elif timeframe == "daily":
            return self.bars_daily[ticker][-numel:]
        else:
            raise ValueError("Unrecognized timeframe.")

    def getCloses(self, ticker, timeframe, numel):
        """Returns a list of bars numel elements back from now."""
        if timeframe == "5" or timeframe == "05 sec" or timeframe == "5 sec":
            return self.closes_05_sec[ticker][-numel:]
        elif timeframe == "15" or timeframe == "15 min":
            return self.closes_15_min[ticker][-numel:]
        elif timeframe == "daily":
            return self.closes_daily[ticker][-numel:]
        else:
            raise ValueError("Unrecognized timeframe.")

    def getHighs(self, ticker, timeframe, numel):
        """Returns a list of bars numel elements back from now."""
        if timeframe == "5" or timeframe == "05 sec" or timeframe == "5 sec":
            return self.highs_05_sec[ticker][-numel:]
        elif timeframe == "15" or timeframe == "15 min":
            return self.highs_15_min[ticker][-numel:]
        elif timeframe == "daily":
            raise ValueError("We only store bars and closes for daily. You'll have to use bars.")
        else:
            raise ValueError("Unrecognized timeframe.")

    def getLows(self, ticker, timeframe, numel):
        """Returns a list of bars numel elements back from now."""
        if timeframe == "5" or timeframe == "05 sec" or timeframe == "5 sec":
            return self.lows_05_sec[ticker][-numel:]
        elif timeframe == "15" or timeframe == "15 min":
            return self.lows_15_min[ticker][-numel:]
        elif timeframe == "daily":
            raise ValueError("We only store bars and closes for daily. You'll have to use bars.")
        else:
            raise ValueError("Unrecognized timeframe.")

    def addBar(self, bar):
        """Use this one until vectors are the length you want"""
        ticker = bar.ticker
        timeframe = bar.timeframe
        assert(timeframe == "05 sec" or timeframe == "15 min" or timeframe == "daily")
        if timeframe == "05 sec":
            self.bars_05_sec[ticker].append(bar)
            self.closes_05_sec[ticker].append(bar.close)
            self.highs_05_sec[ticker].append(bar.high)
            self.lows_05_sec[ticker].append(bar.low)

        elif timeframe == "15 min":
            self.bars_15_min[ticker].append(bar)
            self.closes_15_min[ticker].append(bar.close)
            self.highs_15_min[ticker].append(bar.high)
            self.lows_15_min[ticker].append(bar.low)

        else:
            self.bars_daily[ticker].append(bar)
            self.closes_daily[ticker].append(bar.close)

    def replaceBar(self, bar):
        """Use this one once vectors are the right size."""
        ticker = bar.ticker
        timeframe = bar.timeframe
        assert(timeframe == "05 sec" or timeframe == "15 min" or timeframe == "daily")
        if timeframe == "05 sec":
            del(self.bars_05_sec[ticker][0])
            del(self.closes_05_sec[ticker][0])
            del(self.lows_05_sec[ticker][0])
            del(self.highs_05_sec[ticker][0])
            self.bars_05_sec[ticker].append(bar)
            self.closes_05_sec[ticker].append(bar.close)
            self.highs_05_sec[ticker].append(bar.high)
            self.lows_05_sec[ticker].append(bar.low)

        elif timeframe == "15 min":
            del(self.bars_15_min[ticker][0])
            del(self.closes_15_min[ticker][0])
            del(self.highs_15_min[ticker][0])
            del(self.lows_15_min[ticker][0])
            self.bars_15_min[ticker].append(bar)
            self.closes_15_min[ticker].append(bar.close)
            self.highs_15_min[ticker].append(bar.high)
            self.lows_15_min[ticker].append(bar.low)

        else:
            del(self.bars_daily[ticker][0])
            del(self.closes_daily[ticker][0])
            self.bars_daily[ticker].append(bar)
            self.closes_daily[ticker].append(bar.close)

    def locateStartingEpoch(self, minEpoch=0):
        """Returns epoch of earliest daily bar. The top 50 results should all have the same epoch,
        so we return the 25th one in case the very top of the list is a corner case."""
        cmd = "SELECT epoch FROM bars_daily WHERE epoch>" + str(minEpoch) + " SORT BY epoch;"
        self.curs.execute(cmd)
        return self.curs.fetchall()[25][0]

    def initializeEpochs(self, minEpoch=0):
        """Run this before using this bar source in historical mode."""
        self.nowDaily = self.locateStartingEpoch(minEpoch=minEpoch)
        self.advanceNownessToNextDay(advanceDaily=False)

    def advanceNowness(self):
        """Advances epochs for all 3 bar sizes. Moves this object's idea of 'now' forward by 1 bar."""
        self.now05Sec += 5
        timeObj = epoch2human(self.now05Sec)
        if timeObj.minute in [0, 15, 30, 45] and timeObj.second == 0:
            self.now15Min += 60*15
        self.prevHr = timeObj.hour

    def needToAdvanceToNextDay(self, someEpoch):
        """Call this to test whether you need to advance to the next day."""
        now = epoch2human(self.now05Sec)
        return now.hour < 12 and self.prevHr > 12

    def advanceNownessToNextDay(self, advanceDaily=True):
        """Call this at the end of a historical day to figure out what epochs to search for at
        the start of the next day. Useful for both initializing state of realtime system and
        historical tests. advanceDaily is provided as a parameter to reuse this function for
        state initialization."""
        if advanceDaily:
            self.advanceDaily()
        for ticker in self.tickers:
            tmpEpoch = getNextHigherEpoch(self.curs, ticker, whichTable="15 min", minEpoch=self.nowDaily)
            if tmpEpoch > 0:
                self.now15Min = tmpEpoch
                break
        for ticker in self.tickers:
            tmpEpoch = getNextHigherEpoch(self.curs, ticker, whichTable="05 sec", minEpoch=self.nowDaily)
            if tmpEpoch > 0:
                self.now05Sec = tmpEpoch
                break

    def advanceDaily(self):
        for ticker in self.tickers:
            tmpEpoch = getNextHigherEpoch(self.curs, ticker, whichTable="daily", minEpoch=self.now05Sec)
            if tmpEpoch > 0:
                self.nowDaily = tmpEpoch

    def waitForRealtimeUpdate(self, thresh1=35, thresh2=42):
        """Call this to nap until new realtime bars are available."""
        assert(thresh2 >= thresh1)
        attempts = 0
        while True:
            cmd = "SELECT COUNT(*) FROM bars_5_sec WHERE epoch=" + str(self.now05Sec) + ";"
            self.curs.execute(cmd)
            result = self.curs.fetchall()[0][0]
            attempts += 1
            if result >= thresh2:
                return
            elif result >= thresh1:
                sleep(random.uniform(0.01, 0.1))
            else:
                sleep(random.uniform(0.5, 1))

    def absorbRealtimeBars(self, whichTable):
        """This should be called after waitForRealtimeUpdate(). This command
        queries for a specific epoch which all bars just added should have.
        All bars found are added/updated into the appropriate vector."""
        assert(whichTable == "05 sec" or whichTable == "15 min" or whichTable == "daily")
        for ticker in self.tickers:
            tupleList = getBarWithExactEpoch(self.curs,
                                            ticker,
                                            whichTable=whichTable,
                                            epoch=self.minEpoch[ticker]["05 sec"])
            self.putTuplesInLists(ticker, tupleList, whichTable=whichTable)

    def loadHistorical(self, whichTable):
        """This function can be used for initializing 5 sec vectors as well as updating.
        If vectors are too short, more items will be added to vectors. If vectors
        are long enough, items will be replaced."""
        assert(whichTable == "05 sec" or whichTable == "15 min" or whichTable == "daily")
        for ticker in self.tickers:
            tupleList = getBarsWithMinimumEpoch(self.curs,
                                            ticker,
                                            whichTable=whichTable,
                                            epoch=self.minEpoch[ticker]["05 sec"])
            self.putTuplesInLists(ticker, tupleList, whichTable=whichTable)

    def putTuplesInLists(self, ticker, tupleList, whichTable):
        """Takes a list of tuples from a postgresql query and stores them in lists."""
        for barTuple in tupleList:
            epoch = barTuple[0]
            oneBar = BarData()
            setattr(oneBar, "epoch", epoch)
            setattr(oneBar, "ticker", ticker)
            setattr(oneBar, "timeframe", whichTable) # This is how we pass whichTable to self.replaceBar()
            oneBar.date = epoch2human(epoch)
            oneBar.open = barTuple[1]
            oneBar.close = barTuple[2]
            oneBar.high = barTuple[3]
            oneBar.low = barTuple[4]
            oneBar.volume = barTuple[5]
            if whichTable == "05 sec":
                if len(self.bars_05_sec[ticker]) >= self.desired_num_05_sec:
                    self.replaceBar(oneBar)
                else:
                    self.addBar(oneBar)
            elif whichTable == "15 min":
                if len(self.bars_15_min[ticker]) >= self.desired_num_15_min:
                    self.replaceBar(oneBar)
                else:
                    self.addBar(oneBar)
            else:
                if len(self.bars_daily[ticker]) >= self.desired_num_daily:
                    self.replaceBar(oneBar)
                else:
                    self.addBar(oneBar)
            self.minEpoch[ticker][whichTable] = epoch + 5
        print(ticker, "    ", whichTable, "    Length of tuple list: ", len(tupleList))
        if whichTable == "05 sec":
            lengthNum = len(self.closes_05_sec[ticker])
        elif whichTable == "15 min":
            lengthNum = len(self.closes_15_min[ticker])
        else:
            lengthNum = len(self.closes_daily[ticker])
        print(ticker, "    ", whichTable, "    Length of vector: ", lengthNum)

def testLocalBarSource():
    conn = connect2IbData()
    uut = LocalBarSource(localStorageConnection=conn)
    print("Using the following tickers:")
    for ticker in uut.tickers:
        print(ticker)

def showOrderedOutput():
    """Shows that we are using the ORDER BY epoch statement correctly."""
    conn = connect2IbData()
    uut = LocalBarSource(localStorageConnection=conn, addDummyData=True)
    for bar in uut.bars_05_sec["__XYZ"]:
        print("%d    %03.2f" % (bar.epoch, bar.open))

def testGetCloses():
    conn = connect2IbData()
    uut = LocalBarSource(localStorageConnection=conn, addDummyData=True)
    print("Here are a bunch of prices:")
    #getCloses(self, ticker, timeframe, numel):
    for m in uut.getCloses("__XYZ", "05 sec", 30):
        print(m)

def testGetBars():
    conn = connect2IbData()
    uut = LocalBarSource(localStorageConnection=conn, addDummyData=True)
    print("Here are a bunch of prices:")
    for m in uut.getBars("__XYZ", "05 sec", 30):
        print(m.open, "    ", m.low)

def testWaitForRealtimeUpdate():
    conn = connect2IbData()
    uut = LocalBarSource(localStorageConnection=conn, addDummyData=True)
    uut.now05Sec = 100130
    uut.waitForRealtimeUpdate(1, 1)

if __name__=="__main__":
    testWaitForRealtimeUpdate()
























