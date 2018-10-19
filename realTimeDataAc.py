#!/usr/bin/env python
"""This is the real time wrapper for an algorithmic trading system based on the ideas of Shawn Keller.
Author: Jim Strieter
Date:   12/25/2017
Where:  Scottsdale, AZ
Copyright 2017 James J. Strieter"""

from ibapi.common import *
from ibapi.order_condition import *
from rtWrapper import CustomWrapper
from cmdLineParser import cmdLineParseObj
from contractDump import *
from easyPostgresConnection import connect2IbData
from easyPostgresConnection import insertOneBar
# from easyPostgresConnection import updateOneBar
import time
from easyPostgresConnection import connect2IbData

class epoch2human:
    def __init__(self, time0):
        """time0 is an integer representing epoch time - seconds since midnight Jan 1, 1970."""
        timeStr = time.strftime("%Y%m%d, %H:%M:%S", time.localtime(time0))
        # print(timeStr)
        self.epochTime      = time0
        self.timeStr        = timeStr
        self.year           = int(timeStr[:4])
        self.month          = int(timeStr[4:6])
        self.day            = int(timeStr[6:8])
        self.hour           = int(timeStr[10:12])
        self.minute         = int(timeStr[13:15])
        self.second         = int(timeStr[16:18])

    def __str__(self):
        return self.timeStr

class MyTradingApp(CustomWrapper):
    def __init__(self, parseObj=None):
        super().__init__()

        print("ParseObj is: ", str(parseObj))
        print("\n\n", parseObj.initOrderId, "\n\n")

        # For Testing:
        if parseObj is not None:
            self.forceTicker            = parseObj.forceTicker
            self.forceLongTermUp        = parseObj.forceLongTermUp
            self.forceShortTermUp       = parseObj.forceShortTermUp
            self.forceLongTermDown      = parseObj.forceLongTermDown
            self.forceShortTermDown     = parseObj.forceShortTermDown
            self.forceBubbleUpDaily     = parseObj.forceBubbleUpDaily
            self.forceBubbleDownDaily   = parseObj.forceBubbleDownDaily
            self.forceCallTrigDaily     = parseObj.forceCallTrigDaily
            self.forcePutTrigDaily      = parseObj.forcePutTrigDaily
            self.forceCallTrig15        = parseObj.forceCallTrig15
            self.forcePutTrig15         = parseObj.forcePutTrig15
            self.nudgeCallTrig15        = parseObj.nudgeCallTrig15
            self.nudgePutTrig15         = parseObj.nudgePutTrig15
            self.nudgeCallTrigDaily     = parseObj.nudgeCallTrigDaily
            self.nudgePutTrigDaily      = parseObj.nudgePutTrigDaily
            self.firstTickerOnly        = parseObj.firstTickerOnly
            self.first3TickersOnly      = parseObj.first3TickersOnly
            self.first10TickersOnly     = parseObj.first10TickersOnly
            self.plotEveryTimestep      = parseObj.plotEveryTimestep
            self.plotName               = parseObj.plotName
            self.disableTws             = parseObj.disableTws
            self.barSourceFile          = parseObj.barSourceFile
            self.useTestHarness         = parseObj.useTestHarness
            self.testBuyCall            = parseObj.testBuyCall
            self.testBuyPut             = parseObj.testBuyPut
            self.testSellCall           = parseObj.testSellCall
            self.testSellPut            = parseObj.testSellPut
            self.accountNum             = parseObj.account
            self.ignoreAccount          = parseObj.ignoreAccount
            self.initOrderId            = parseObj.initOrderId
            self.useInitOrderId         = True
        else:
            self.initOrderId = -1
            self.useInitOrderId         = False

        if self.testBuyCall or self.testSellCall or self.testBuyPut or self.testSellPut:
            # If all we're doing is forcing 1 order, no need for a lot of data
            self.getAllStockData = False
        else:
            self.getAllStockData = True


        # Trading Engines, Data Repos, tickers, Contracts & Such
        # Note: some of the IB callbacks in this class use the variable reqId to refer to what I call a data Id.
        self.dailyRepo = {}  # Reference data repo by data Id
        self.fifteenRepo = {}  # Key by data Id

        self.fiveSecHighs   = {}
        self.fiveSecLows    = {}
        self.fiveSecCloses  = {}
        self.fiveSecKs      = {}
        self.fiveSecDs      = {}
        self.fiveSecHistoricalDone = {}
        self.fiveSecEpochs = {}

        self.fifteenHighs = {}
        self.fifteenLows = {}
        self.fifteenCloses = {}

        self.dailyHighs = {}
        self.dailyLows = {}
        self.dailyCloses = {}  # Closing prices for purpose of calculating moving averages

        self.dailyBubbleDown = {}  # Dictionary of bools. This should never be a vector.
        self.dailyBubbleUp = {}  # Dictionary of bools. This should never be a vector.
        self.dailyStoch = {}
        self.fifteenStoch = {}
        self.dailyTrend = {}  # key by data id
        self.fifteenTrend = {}
        self.ticker2dataId = {}  # Look up data Id by ticker
        self.underConst = {}  # Bar under construction, keyed by dataId
        self.underlyingContract = {}  # Look up underlying contract by data Id
        self.dataIds = []  # Keep a list of all our data Ids (same as reqId's)
        self.tickers = {}  # Look up ticker by data Id
        self.changeLogFiles = {}  # Reference change log filenames by data Id
        self.dailyHistoricalDone = {}  # Track whether historicalDataEnd() has been called by reqId
        self.fifteenMinHistoricalDone = {}  # Track whether historicalDataEnd() has been called by reqId
        self.reqId2Order = {}           # Look up order id by reqId
        self.oId2Contract = {}          # Look up orders that were placed by order Id
        self.tradeThisTicker = {}

        # Map order Ids to/from tickers & reqIds       Each Entry Should Be A           Because
        self.entranceOrderId_to_reqId = {}          #       scalar                    many-to-one
        self.trailStopOrderId_to_reqId = {}         #       scalar                    many-to-one
        self.takeProfitOrderId_to_reqId = {}        #       scalar                    many-to-one
        self.reqId_to_entranceOrderId = {}          #        list                     one-to-many
        self.reqId_to_trailStopOrderId = {}         #        list                     one-to-many
        self.reqId_to_takeProfitOrderId = {}        #        list                     one-to-many

        # Map Order Ids to the order OBJECT:
        self.entranceOrderId_to_OBJECT = {}         #       scalar                    one-to-one
        self.trailStopOrderId_to_OBJECT = {}        #       scalar                    one-to-one
        self.takeProfitOrderId_to_OBJECT = {}       #       scalar                    one-to-one

        # Map reqIds to order OBJECT:
        self.reqId_to_entrance_OBJECT = {}          #        list                     one-to-many
        self.reqId_to_trailStop_OBJECT = {}         #        list                     one-to-many
        self.reqId_to_takeProfit_OBJECT = {}        #        list                     one-to-many
        self.recordedDataSubscriptionInPostgres = {}
        self.postgresConn = connect2IbData()
        self.localStorageConnection = connect2IbData()
        self.curs = self.localStorageConnection.cursor()

        self.chooseStocks()


    def allDailyHistoricalDone(self):
        y = True
        for m in self.dataIds:
            y = y and self.dailyHistoricalDone[m]
        return y


    def all15MinHistoricalDone(self):
        y = True
        for m in self.dataIds:
            y = y and self.fifteenMinHistoricalDone[m]
        if y == False:
            pass
        return y


    def all5SecHistoricalDone(self):
        y = True
        for m in self.dataIds:
            y = y and self.fiveSecHistoricalDone[m]
        if y == False:
            pass
        return y


    def chooseStocksHelper(self, ticker, undContract):
        self.newReqId()
        reqId = self.latestReqId()

        self.dailyRepo[reqId]       = []
        self.fifteenRepo[reqId]     = []
        self.dailyTrend[reqId]      = []
        self.fifteenTrend[reqId]    = []
        self.fiveSecHistoricalDone[reqId] = False
        self.fiveSecEpochs[reqId]   = []

        self.fifteenHighs[reqId]    = []
        self.fifteenLows[reqId]     = []
        self.fifteenCloses[reqId]   = []

        self.dailyHighs[reqId]      = []
        self.dailyLows[reqId]       = []
        self.dailyCloses[reqId]     = []

        self.reqId_to_entranceOrderId[reqId] = []
        self.reqId_to_trailStopOrderId[reqId] = []
        self.reqId_to_takeProfitOrderId[reqId] = []

        self.reqId_to_entrance_OBJECT[reqId] = []
        self.reqId_to_takeProfit_OBJECT[reqId] = []
        self.reqId_to_trailStop_OBJECT[reqId] = []

        self.dailyBubbleDown[reqId]     = False
        self.dailyBubbleUp[reqId]       = False
        self.underConst[reqId]          = None
        self.ticker2dataId[ticker]      = reqId
        self.underlyingContract[reqId]  = undContract
        self.tickers[reqId]             = ticker
        self.dailyHistoricalDone[reqId] = False
        self.fifteenMinHistoricalDone[reqId] = False
        self.reqId2Order[reqId]         = []
        self.tradeThisTicker[reqId]     = True
        self.recordedDataSubscriptionInPostgres[reqId] = False


    def chooseStocks(self):
        # self.chooseStocksHelper("SPY", spy())
        if self.getAllStockData:
            # self.chooseStocksHelper('CAT', usStock_cat()) # No security definition has been found
            self.chooseStocksHelper('AAPL', usStock_aapl())
            self.chooseStocksHelper('ABX', usStock_abx())
            self.chooseStocksHelper('AMD', usStock_amd())
            self.chooseStocksHelper('AXP', usStock_axp())
            self.chooseStocksHelper('BA', usStock_ba())
            self.chooseStocksHelper('BABA', usStock_baba())
            self.chooseStocksHelper('BAC', usStock_bac())
            self.chooseStocksHelper('BB', usStock_bb())
            self.chooseStocksHelper('CHK', usStock_chk())
            self.chooseStocksHelper('CSCO', usStock_csco())
            self.chooseStocksHelper('CVX', usStock_cvx())
            self.chooseStocksHelper('DIS', usStock_dis())
            self.chooseStocksHelper('DWDP', usStock_dwdp())
            self.chooseStocksHelper('FB', usStock_fb())
            self.chooseStocksHelper('JNJ', usStock_jnj())
            self.chooseStocksHelper('MU', usStock_mu())
            self.chooseStocksHelper('NFLX', usStock_nflx())
            self.chooseStocksHelper('NKE', usStock_nke())
            self.chooseStocksHelper('NVDA', usStock_nvda())
            self.chooseStocksHelper('PFE', usStock_pfe())
            self.chooseStocksHelper('PG', usStock_pg())
            self.chooseStocksHelper('FCX', usStock_fcx())
            self.chooseStocksHelper('GE', usStock_ge())
            self.chooseStocksHelper('GS', usStock_gs())
            self.chooseStocksHelper('HD', usStock_hd())
            self.chooseStocksHelper('HPQ', usStock_hpq())
            self.chooseStocksHelper('IBM', usStock_ibm())
            self.chooseStocksHelper('INTC', usStock_intc())
            self.chooseStocksHelper('JPM', usStock_jpm())
            self.chooseStocksHelper('KO', usStock_ko())
            self.chooseStocksHelper('LOW', usStock_low())
            self.chooseStocksHelper('MCD', usStock_mcd())
            self.chooseStocksHelper('MMM', usStock_mmm())
            self.chooseStocksHelper('MRK', usStock_mrk())
            self.chooseStocksHelper('MSFT', usStock_msft())
            self.chooseStocksHelper('SBUX', usStock_sbux())
            self.chooseStocksHelper('SLB', usStock_slb())
            self.chooseStocksHelper('SNAP', usStock_snap())
            self.chooseStocksHelper('TSLA', usStock_tsla())
            self.chooseStocksHelper('TWTR', usStock_twtr())
            self.chooseStocksHelper('TXN', usStock_txn())
            self.chooseStocksHelper('UNH', usStock_unh())
            self.chooseStocksHelper('UTX', usStock_utx())
            self.chooseStocksHelper('V', usStock_v())
            self.chooseStocksHelper('VZ', usStock_vz())
            self.chooseStocksHelper('WMT', usStock_wmt())
            self.chooseStocksHelper('XOM', usStock_xom())


    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        print("Invoked customShtuff.nextValidId()")
        self.nextValidOrderId = orderId
        if not self.started:
            self.start()
        return orderId


    def start(self):
        """Try moving this to rtWrapper.py"""
        print("*****************************************************************************************************")
        print("******************************************* Running start *******************************************")
        print("*****************************************************************************************************")
        print("self.started: ", self.started)

        if self.started:
            return

        # Normal stuff goes here:
        self.started = True

        if self.globalCancelOnly:
            print("Executing GlobalCancel only")
            self.reqGlobalCancel()
        else:
            self.realTimeBars_req()
            print("Executing requests ... finished")


    def realTimeBars_req(self):
        """Iterates through all the reqId's we created earlier and sends the contract associated with each
        to TWS."""
        for m in self.dataIds:
            print("Requesting Data Id: ", m)
            self.reqRealTimeBars( m, self.underlyingContract[m], 5, "MIDPOINT", False, [] )


    # <realtimebar> Search for this to go straight here :)
    def realtimeBar(self, reqId:TickerId, time:int, open:float, high:float, low:float, close:float, volume:int, wap:float, count:int, testMode=False):
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        bar = BarData()
        bar.close = close
        bar.open = open
        bar.high = high
        bar.low = low
        bar.date = epoch2human(time)
        setattr(bar, 'epoch', time)
        ticker = self.tickers[reqId]
        setattr(bar, 'ticker', ticker)
        insertOneBar(self.postgresConn, bar, time, self.tickers[reqId])
        print("Received 5 bar for ", self.tickers[reqId], " at time ", str(time))

        if not self.recordedDataSubscriptionInPostgres[reqId]:
            # Send a record to postgres:
            # insert into data_subscriptions (epoch, ticker, five_sec, ticks) values (205, 'ABC', true, false);
            cmd = "INSERT INTO data_subscriptions (epoch, ticker, five_sec, ticks)"
            cmd += "VALUES (" + str(time) + ", '" + ticker.upper() + "', true, false);"
            self.curs.execute(cmd)
            self.recordedDataSubscriptionInPostgres[reqId] = True


def main():
    cmdLineParser = cmdLineParseObj()
    args = cmdLineParser.parse_args()
    print("Using args", args)
    from ibapi import utils
    from ibapi.order import Order
    Order.__setattr__ = utils.setattr_log
    from ibapi.contract import Contract, UnderComp
    Contract.__setattr__ = utils.setattr_log
    UnderComp.__setattr__ = utils.setattr_log
    from ibapi.tag_value import TagValue
    TagValue.__setattr__ = utils.setattr_log
    TimeCondition.__setattr__ = utils.setattr_log
    ExecutionCondition.__setattr__ = utils.setattr_log
    MarginCondition.__setattr__ = utils.setattr_log
    PriceCondition.__setattr__ = utils.setattr_log
    PercentChangeCondition.__setattr__ = utils.setattr_log
    VolumeCondition.__setattr__ = utils.setattr_log

    try:
        app = MyTradingApp(cmdLineParser.parse_args())
        if args.global_cancel:
            app.globalCancelOnly = True
        # ! [connect]
        app.connect("127.0.0.1", args.port, clientId=0)
        print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),
                                                      app.twsConnectionTime()))
        # ! [connect]

        app.run()
        app.nextValidId(1) # nextValidId

    except:
        raise
    finally:
        app.dumpTestCoverageSituation()
        app.dumpReqAnsErrSituation()

        # Print Trades to Screen:
        print("\n"*20)

if __name__ == "__main__":
    main()

