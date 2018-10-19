from psycopg2 import *
from ibapi.common import BarData
import getpass
from credentials import credentials

def barTableName(whichTable):
    assert(whichTable=="5_sec" or whichTable=="15_min" or whichTable=="daily")
    return "bars_" + whichTable

def connect2IbData(credentialDict=None):
    """IMPORTANT: You must create credentials.py, which must contain a dict named credentials.
    You should add credentials.py to .gitignore because you don't want to push your login info
    to the repo where everybody can see it. Alternatively you can pass in another dictionary
    with the same name."""
    if credentialDict is None:
        # In this case, use default credentials:
        return connect(host=credentials["host"],
                       database=credentials["database"],
                       user=credentials["username"],
                       password=credentials["password"])
    else:
        # In this case, use credentials that were passed in:
        return connect(host=credentialDict["host"],
                           database=credentialDict["database"],
                           user=credentialDict["username"],
                           password=credentialDict["password"])


def mkBarLen(barLenStr):
    if barLenStr == "1 day":
        return 3600*7.5
    if barLenStr == "1 hour":
        return 3600
    if barLenStr == "15 min":
        return 60*15
    if barLenStr == "5 min":
        return 60*5
    if barLenStr == "1 min":
        return 60
    if barLenStr == "5 sec":
        return 5
    if barLenStr == "tick":
        return 0
    raise ValueError("Unrecognized bar length: " + str(barLenStr))

def insertOneBar(connection, bar:BarData, eTime=None, ticker=None, whichTable="bars_5_sec"):
    assert(hasattr(bar, 'epoch') or hasattr(bar, 'eTime') or eTime is not None)
    assert(hasattr(bar, 'ticker') or isinstance(ticker, str))

    oneCmd = "INSERT INTO " + whichTable + " (ticker, epoch, open, close, high, low, volume) VALUES ("

    if hasattr(bar, 'ticker'):
        oneCmd += "'" + bar.ticker.upper() + "', "
    else:
        oneCmd += "'" + ticker.upper() + "', "

    if hasattr(bar, 'epoch'):
        oneCmd += str(bar.epoch) + ', '
    elif hasattr(bar, 'eTime'):
        oneCmd += str(bar.eTime) + ', '
    else:
        oneCmd += str(eTime) + ', '

    oneCmd += str(bar.open) + ', '
    oneCmd += str(bar.close) + ', '
    oneCmd += str(bar.high) + ', '
    oneCmd += str(bar.low) + ', '
    oneCmd += str(bar.volume) + ');'
    connection.cursor().execute(oneCmd)
    connection.commit()

# def updateOneBar(connection, bar:BarData, kind, eTime=None, ticker=None):
#     """UPDATE bars SET bid_open = 21 WHERE ticker='AAPL' and epoch=12092;
#        UPDATE bars SET bid_close = 21, bid_high = 89 WHERE ticker='AAPL';"""
#     assert(hasattr(bar, 'epoch') or hasattr(bar, 'eTime') or eTime is not None)
#     assert(hasattr(bar, 'ticker') or isinstance(ticker, str))
#     assert(kind=="bid" or kind=="ask")
#
#     if hasattr(bar, 'ticker'):
#         ticker = bar.ticker.upper()
#
#     if hasattr(bar, 'epoch'):
#         epoch = bar.epoch
#     elif hasattr(bar, 'eTime'):
#         epoch = bar.eTime
#
#     if kind=="ask":
#         oneCmd = "UPDATE bars SET ask_open=" + str(bar.open) + ", ask_close=" + str(bar.close) +\
#             ", ask_high=" + str(bar.high) + ", ask_low=" + str(bar.low) + " WHERE TICKER='" + ticker + "' and " + \
#             " epoch=" + str(epoch) + ";"
#     else:
#         oneCmd = "UPDATE bars SET bid_open=" + str(bar.open) + ", bid_close=" + str(bar.close) +\
#             ", bid_high=" + str(bar.high) + ", bid_low=" + str(bar.low) + " WHERE TICKER='" + ticker + "' and " + \
#             " epoch=" + str(epoch) + ";"
#     print(oneCmd)
#     connection.cursor().execute(oneCmd)
#     connection.commit()

def easyQueryDemo():
    connection = connect2IbData()
    curs = connection.cursor()
    curs.execute("""SELECT * FROM bars;""")
    rows = curs.fetchall()
    for m in rows:
        print(m)

def queryOneTicker(ticker, minEpoch):
    connection = connect2IbData()
    curs = connection.cursor()
    curs.execute("""SELECT ticker, epoch, bid_high, bid_low, bid_close FROM bars WHERE ticker='""" + ticker.upper() + """' and epoch > """ + str(minEpoch) + ";")
    return curs.fetchall()

def easyInsertDemo():
    connection = connect2IbData()
    oneBar = BarData()
    oneBar.open = 100.15
    oneBar.close = 100.25
    oneBar.high = 100.55
    oneBar.low = 99.99
    oneBar.volume = 1000000
    setattr(oneBar, 'epoch', 12097)
    setattr(oneBar, 'ticker', 'AAPL')
    insertOneBar(connection, oneBar)

if __name__=="__main__":
    easyInsertDemo()
    # easyQueryDemo()
    queryOneTicker('AAPL', 12091)



























