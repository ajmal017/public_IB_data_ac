#!/usr/bin/env python
import collections
import inspect

import logging
import time
import os.path

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.utils import iswrapper

# types
from ibapi.common import *
from ibapi.order import *
from ibapi.order_state import *
from ibapi.ticktype import *
from ContractSamples import ContractSamples
from OrderSamples import OrderSamples
from ibapi.contract import *
from barTools import human2epoch
from barTools import epoch2human
from easyPostgresConnection import connect2IbData
from easyPostgresConnection import insertOneBar
from contractDump import *
from historicalFetcher_15_min import getLatestEpoch

def durationYr(n):
    """Returns a duration string for historical data request."""
    return str(n) + " Y"


def durationSec(n):
    """Returns a duration string for historical data request."""
    return str(n) + " S"


def durationDay(n):
    """Returns a duration string for historical data request."""
    return str(n) + " D"


def durationWk(n):
    """Returns a duration string for historical data request."""
    return str(n) + " W"


def durationMo(n):
    """Returns a duration string for historical data request."""
    return str(n) + " M"


def sizeSec(n):
    """Returns a valid bar size"""
    assert (n == 5 or n == 10 or n == 15 or n == 30 or n == 60)
    return str(n) + " secs"


def sizeMin(n):
    """Returns a valid bar size"""
    assert (n == 1 or n == 5 or n == 10 or n == 15 or n == 30)
    if n == 1:
        return "1 min"
    return str(n) + " mins"


def sizeHr(n=1):
    """Returns a valid bar size"""
    assert (n == 1 or n == 2 or n == 4)
    if n == 1:
        return "1 hour"
    if n == 2:
        return "2 hours"
    return "4 hours"


def sizeDay():
    """Returns a valid bar size"""
    return "1 day"


def endTime(y, mo, d, hr=0, mi=0, s=0):
    return str(y) + ("%02d" % mo) + ("%02d" % d) + ' ' + ("%02d" % hr) + \
           ':' + ("%02d" % mi) + ':' + ("%02d" % s)


def SetupLogger():
    if not os.path.exists("log"):
        os.makedirs("log")

    time.strftime("pyibapi.%Y%m%d_%H%M%S.log")

    recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'

    timefmt = '%y%m%d_%H:%M:%S'

    # logging.basicConfig( level=logging.DEBUG,
    #                    format=recfmt, datefmt=timefmt)
    logging.basicConfig(filename=time.strftime("log/pyibapi.%y%m%d_%H%M%S.log"),
                        filemode="w",
                        level=logging.INFO,
                        format=recfmt, datefmt=timefmt)
    logger = logging.getLogger()
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logger.addHandler(console)


def printWhenExecuting(fn):
    def fn2(self):
        print("   doing", fn.__name__)
        fn(self)
        print("   done w/", fn.__name__)

    return fn2


def printinstance(inst: Object):
    attrs = vars(inst)
    print(', '.join("%s: %s" % item for item in attrs.items()))


class Activity(Object):
    def __init__(self, reqMsgId, ansMsgId, ansEndMsgId, reqId):
        self.reqMsdId = reqMsgId
        self.ansMsgId = ansMsgId
        self.ansEndMsgId = ansEndMsgId
        self.reqId = reqId


class RequestMgr(Object):
    def __init__(self):
        # I will keep this simple even if slower for now: only one list of
        # requests finding will be done by linear search
        self.requests = []

    def addReq(self, req):
        self.requests.append(req)

    def receivedMsg(self, msg):
        pass


# ! [socket_declare]
class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)
        # ! [socket_declare]

        # how many times a method is called to see test coverage
        self.clntMeth2callCount = collections.defaultdict(int)
        self.clntMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nReq = collections.defaultdict(int)
        self.setupDetectReqId()

    def countReqId(self, methName, fn):
        def countReqId_(*args, **kwargs):
            self.clntMeth2callCount[methName] += 1
            idx = self.clntMeth2reqIdIdx[methName]
            if idx >= 0:
                sign = -1 if 'cancel' in methName else 1
                self.reqId2nReq[sign * args[idx]] += 1
            return fn(*args, **kwargs)

        return countReqId_

    def setupDetectReqId(self):

        methods = inspect.getmembers(EClient, inspect.isfunction)
        for (methName, meth) in methods:
            if methName != "send_msg":
                # don't screw up the nice automated logging in the send_msg()
                self.clntMeth2callCount[methName] = 0
                # logging.debug("meth %s", name)
                sig = inspect.signature(meth)
                for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                    (paramName, param) = pnameNparam
                    if paramName == "reqId":
                        self.clntMeth2reqIdIdx[methName] = idx

                setattr(TestClient, methName, self.countReqId(methName, meth))

                # print("TestClient.clntMeth2reqIdIdx", self.clntMeth2reqIdIdx)


# ! [ewrapperimpl]
class TestWrapper(wrapper.EWrapper):
    # ! [ewrapperimpl]
    def __init__(self):
        wrapper.EWrapper.__init__(self)

        self.wrapMeth2callCount = collections.defaultdict(int)
        self.wrapMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nAns = collections.defaultdict(int)
        self.setupDetectWrapperReqId()
        self.postgresConnection = connect2IbData()
        self.postgresCursor = self.postgresConnection.cursor()

    def countWrapReqId(self, methName, fn):
        def countWrapReqId_(*args, **kwargs):
            self.wrapMeth2callCount[methName] += 1
            idx = self.wrapMeth2reqIdIdx[methName]
            if idx >= 0:
                self.reqId2nAns[args[idx]] += 1
            return fn(*args, **kwargs)

        return countWrapReqId_

    def setupDetectWrapperReqId(self):

        methods = inspect.getmembers(wrapper.EWrapper, inspect.isfunction)
        for (methName, meth) in methods:
            self.wrapMeth2callCount[methName] = 0
            # logging.debug("meth %s", name)
            sig = inspect.signature(meth)
            for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                (paramName, param) = pnameNparam
                # we want to count the errors as 'error' not 'answer'
                if 'error' not in methName and paramName == "reqId":
                    self.wrapMeth2reqIdIdx[methName] = idx

            setattr(TestWrapper, methName, self.countWrapReqId(methName, meth))


def USStock():
    contract = Contract()
    contract.symbol = "IBKR"
    contract.secType = "STK"
    contract.currency = "USD"
    # In the API side, NASDAQ is always defined as ISLAND in the exchange field
    contract.exchange = "ISLAND"
    return contract


class dataReq:
    def __init__(self):
        self.isUnderlying = False
        self.isOption = False
        self.ticker = ''
        self.contract = []  # Put an instance of Contract in here
        self.reqId = -1

        # Options Only:
        self.expYr = -1
        self.expMo = -1
        self.expDay = -1
        self.right = ""  # Choose Call or Put
        self.strike = -1


class TestApp(TestWrapper, TestClient):
    def __init__(self, fHandle=None):
        """fHandle is a file handle"""
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)
        self.nKeybInt = 0
        self.started = False
        self.nextValidOrderId = None
        self.permId2ord = {}
        self.reqId2nErr = collections.defaultdict(int)
        self.globalCancelOnly = False
        self.simplePlaceOid = None
        self.resultsFile = fHandle
        self.deleteThisFlag = True
        self.dataIds = []  # Place to store reqId's
        self.tickers = {}  # Retrieve ticker by dataId
        self.underlyingContract = {}  # Retrieve underlying contract by dataId
        self.reqIdDone = {}
        self.minEpochs = {}
        self.chooseStocks()

    def newReqId(self):
        """Generates a new req Id for data."""
        if len(self.dataIds) == 0:
            self.dataIds.append(3001)
        else:
            self.dataIds.append(self.dataIds[-1] + 1)
        return self.dataIds[-1]

    def latestReqId(self):
        return self.dataIds[-1]

    def chooseStocksHelper(self, ticker, undContract):
        """Like chooseStocksHelper(), but easier to say."""
        self.newReqId()
        self.underlyingContract[self.latestReqId()] = undContract
        self.tickers[self.latestReqId()] = ticker
        self.reqIdDone[self.latestReqId()] = False
        self.minEpochs[ticker] = getLatestEpoch(self.postgresCursor, ticker, "bars_daily")

    def chooseStocks(self):
        self.chooseStocksHelper('AAPL', usStock_aapl())
        self.chooseStocksHelper('ABX', usStock_abx())
        self.chooseStocksHelper('AMD', usStock_amd())
        self.chooseStocksHelper('AXP', usStock_axp())
        self.chooseStocksHelper('BA', usStock_ba())
        self.chooseStocksHelper('BABA', usStock_baba())
        self.chooseStocksHelper('BAC', usStock_bac())
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

    def connectAck(self):
        if self.async:
            self.startApi()

    @iswrapper
    # ! [nextvalidid]
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        self.start()

    def start(self):
        print("Running start()")
        if self.started:
            return
        self.historicalDataRequests_req()
        print("Executing requests ... finished")

    def keyboardInterrupt(self):
        self.nKeybInt += 1
        if self.nKeybInt == 1:
            self.stop()
        else:
            print("Finishing test")
            self.done = True

    def stop(self):
        print("Executing cancels")
        # self.realTimeBars_cancel()
        self.historicalDataRequests_cancel()
        print("Executing cancels ... finished")

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        super().error(reqId, errorCode, errorString)
        print("Error. Id: ", reqId, " Code: ", errorCode, " Msg: ", errorString)

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order,
                  orderState: OrderState):
        # *************** I'm guessing this checks *****************
        # ************ for open orders, but that's just a guess ***********
        super().openOrder(orderId, contract, order, orderState)
        print("OpenOrder. ID:", orderId, contract.symbol, contract.secType,
              "@", contract.exchange, ":", order.action, order.orderType,
              order.totalQuantity, orderState.status)
        order.contract = contract
        self.permId2ord[order.permId] = order

    def openOrderEnd(self):
        super().openOrderEnd()
        print("OpenOrderEnd")
        logging.debug("Received %d openOrders", len(self.permId2ord))

    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str):
        super().orderStatus(orderId, status, filled, remaining,
                            avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld)
        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
              "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
              "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
              lastFillPrice, "ClientId:", clientId, "WhyHeld:", whyHeld)

    def realTimeBars_req(self):
        return
        # self.reqRealTimeBars(3101, ContractSamples.USStockAtSmart(), 5, "MIDPOINT", True, [])
        # self.reqRealTimeBars(3001, ContractSamples.EurGbpFx(), 5, "MIDPOINT", True, [])

    def realtimeBar(self, reqId: TickerId, time: int, open: float, high: float, low: float, close: float, volume: int,
                    wap: float, count: int):
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        print("RealTimeBars. ", reqId, ": time ", time, ", open: ", open, ", high: ", high, ", low: ", low, ", close: ",
              close, ", volume: ", volume, ", wap: ", wap, ", count: ", count)

    @printWhenExecuting
    def realTimeBars_cancel(self):
        # Canceling real time bars
        # ! [cancelrealtimebars]
        self.cancelRealTimeBars(3101)
        self.cancelRealTimeBars(3001)
        # ! [cancelrealtimebars]

    @printWhenExecuting
    def historicalDataRequests_req(self, numDays=365):
        """Search for any of the following line to get here:
        the data request <<dataReq>>"""
        assert (isinstance(numDays, int))
        print(self.dataIds)
        for m in self.dataIds:
            print("Requesting data for ", self.tickers[m], ", reqId: ", m)
            self.reqHistoricalData(m, self.underlyingContract[m], "", durationMo(12), sizeDay(), "MIDPOINT", 1, 1, False, [])

    @printWhenExecuting
    def historicalDataRequests_cancel(self):
        return
        # ACTION: Uncomment and test the following:
        # for m in self.dataIds:
        #     # ACTION: Check whether historicalEnd has been called!
        #     self.cancelHistoricalData(m)

    @iswrapper
    # ! [headTimestamp]
    def headTimestamp(self, reqId: int, headTimestamp: str):
        print("HeadTimestamp: ", reqId, " ", headTimestamp)

    # ! [headTimestamp]

    @iswrapper
    # ! [historicaldata]
    def historicalData(self, reqId: int, bar: BarData):
        print("********HistoricalData******** ", reqId, " Date:", bar.date)
        epoch = human2epoch(bar.date)
        setattr(bar, "epoch", epoch)
        ticker = self.tickers[reqId]
        if epoch > self.minEpochs[ticker]:
            insertOneBar(self.postgresConnection, bar, epoch, ticker, whichTable="bars_daily")

    @iswrapper
    # ! [historicaldataend]
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd ", reqId, "from", start, "to", end)
        self.reqIdDone[reqId] = True
        if sum(self.reqIdDone) == len(self.reqIdDone):
            self.done = True

    # ! [historicaldataend]

    @iswrapper
    # ! [historicalDataUpdate]
    def historicalDataUpdate(self, reqId: int, bar: BarData):
        print("HistoricalDataUpdate. ", reqId, " Date:", bar.date, "Open:", bar.open,
              "High:", bar.high, "Low:", bar.low, "Close:", bar.close, "Volume:", bar.volume,
              "Count:", bar.barCount, "WAP:", bar.average)

    # ! [historicalDataUpdate]

    @printWhenExecuting
    def optionsOperations_req(self):
        # *************** THIS COULD COME IN HANDY *****************
        # ! [reqsecdefoptparams]
        self.reqSecDefOptParams(0, "IBM", "", "STK", 8314)
        # ! [reqsecdefoptparams]

        # Calculating implied volatility
        # ! [calculateimpliedvolatility]
        self.calculateImpliedVolatility(5001, ContractSamples.OptionAtBOX(), 5, 85, [])
        # ! [calculateimpliedvolatility]

        # Calculating option's price
        # ! [calculateoptionprice]
        self.calculateOptionPrice(5002, ContractSamples.OptionAtBOX(), 0.22, 85, [])
        # ! [calculateoptionprice]

        # Exercising options
        # ! [exercise_options]
        self.exerciseOptions(5003, ContractSamples.OptionWithTradingClass(), 1,
                             1, self.account, 1)
        # ! [exercise_options]

    @printWhenExecuting
    def optionsOperations_cancel(self):
        # Canceling implied volatility
        self.cancelCalculateImpliedVolatility(5001)
        # Canceling option's price calculation
        self.cancelCalculateOptionPrice(5002)

    @iswrapper
    # ! [tickoptioncomputation]
    def tickOptionComputation(self, reqId: TickerId, tickType: TickType,
                              impliedVol: float, delta: float, optPrice: float, pvDividend: float,
                              gamma: float, vega: float, theta: float, undPrice: float):
        super().tickOptionComputation(reqId, tickType, impliedVol, delta,
                                      optPrice, pvDividend, gamma, vega, theta, undPrice)
        print("TickOptionComputation. TickerId:", reqId, "tickType:", tickType,
              "ImpliedVolatility:", impliedVol, "Delta:", delta, "OptionPrice:",
              optPrice, "pvDividend:", pvDividend, "Gamma: ", gamma, "Vega:", vega,
              "Theta:", theta, "UnderlyingPrice:", undPrice)

    # ! [tickoptioncomputation]

    @iswrapper
    # ! [symbolSamples]
    # *************** WHAT DOES THIS DO? *****************
    def symbolSamples(self, reqId: int,
                      contractDescriptions: ListOfContractDescription):
        super().symbolSamples(reqId, contractDescriptions)
        print("Symbol Samples. Request Id: ", reqId)

        for contractDescription in contractDescriptions:
            derivSecTypes = ""
            for derivSecType in contractDescription.derivativeSecTypes:
                derivSecTypes += derivSecType
                derivSecTypes += " "
            print("Contract: conId:%s, symbol:%s, secType:%s primExchange:%s, currency:%s, derivativeSecTypes:%s" % (
                contractDescription.contract.conId,
                contractDescription.contract.symbol,
                contractDescription.contract.secType,
                contractDescription.contract.primaryExchange,
                contractDescription.contract.currency, derivSecTypes))

    # ! [symbolSamples]

    @iswrapper
    # ! [smartcomponents]
    # *************** WHAT DOES THIS DO? *****************
    def smartComponents(self, reqId: int, map: SmartComponentMap):
        super().smartComponents(reqId, map)
        print("smartComponents: ")
        for exch in map:
            print(exch.bitNumber, ", Exchange Name: ", exch.exchange, ", Letter: ", exch.exchangeLetter)

    # ! [smartcomponents]

    @iswrapper
    # ! [tickReqParams]
    # *************** WHAT DOES THIS DO? *****************
    def tickReqParams(self, tickerId: int, minTick: float, bboExchange: str, snapshotPermissions: int):
        super().tickReqParams(tickerId, minTick, bboExchange, snapshotPermissions)
        print("tickReqParams: ", tickerId, " minTick: ", minTick, " bboExchange: ", bboExchange,
              " snapshotPermissions: ", snapshotPermissions)

    # ! [tickReqParams]

    def ocaSample(self):
        """One Cancels All. This could come in handy when I'm not picky
        about the particular strike, but care more that I get one of several
        strikes at a reasonable price. For instance place multiple limit orders
        when I only want 1."""
        ocaOrders = [OrderSamples.LimitOrder("BUY", 1, 10), OrderSamples.LimitOrder("BUY", 1, 11),
                     OrderSamples.LimitOrder("BUY", 1, 12)]
        OrderSamples.OneCancelsAll("TestOCA_" + self.nextValidOrderId, ocaOrders, 2)
        for o in ocaOrders:
            self.placeOrder(self.nextOrderId(), ContractSamples.USStock(), o)


def getPort(tradeLive=False):
    if tradeLive:
        return 7496
    return 7497


def main():
    # try:
    #     f = open('./tempData.json', 'w')
    #     f.write(makeJsonEntry(giveHead('5 min', 25)))
    #     f.write(jsonEolSammich(startNewUpdate('historical')))
    #     app = TestApp(f)
    app = TestApp('./data/spy/tempData.json')
    app.connect("127.0.0.1", getPort(), clientId=0)
    print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),
                                                  app.twsConnectionTime()))
    app.run()
    # except:
    #     raise
    # finally:
    #     f.close()


if __name__ == "__main__":
    main()

















