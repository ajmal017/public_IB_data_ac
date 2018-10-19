#!/usr/bin/env python
"""ACTION: Write a bash script that sends 5-10 combinations of command line arguments in
different orders so we can test this."""

import argparse

DEF_ACTION = "store_true"       # In most cases we want to store a value either way, with a default of False if an option is not passed in.
OPP_ACTION = "store_false"      # Ok to store w/ default True if there's a reason to

def cmdLineParseObj():

    y = argparse.ArgumentParser(description="Automated Trading system based on the ideas of Shawn Keller.")

    y.add_argument("-p", "--port", action="store", type=int,
                               dest="port", default=7497, help="The TCP port to use")

    y.add_argument("-d", "--date", action="store", type=str,
                               dest="dateFilt", default="", help="only return trades that happen on this date")

    y.add_argument("-a", "--account", action="store", type=str, dest="account", default=None, help="Enter your account number")

    y.add_argument("-ia", "--ignoreAccount", action = DEF_ACTION)

    y.add_argument("-C", "--global-cancel", action=DEF_ACTION,
                               dest="global_cancel", default=False,
                               help="whether to trigger a globalCancel req")

    y.add_argument("--forceTicker",             default='None')  # Follow with a ticker name
    y.add_argument("--forceLongTermUp",         action=DEF_ACTION)
    y.add_argument("--forceShortTermUp",        action=DEF_ACTION)
    y.add_argument("--forceLongTermDown",       action=DEF_ACTION)
    y.add_argument("--forceShortTermDown",      action=DEF_ACTION)
    y.add_argument("--forceBubbleUpDaily",      action=DEF_ACTION)
    y.add_argument("--forceBubbleDownDaily",    action=DEF_ACTION)

    # Following force all 4 k/d variables:
    y.add_argument("--forceCallTrigDaily",      action=DEF_ACTION)
    y.add_argument("--forcePutTrigDaily",       action=DEF_ACTION)
    y.add_argument("--forceCallTrig15",         action=DEF_ACTION)
    y.add_argument("--forcePutTrig15",          action=DEF_ACTION)

    # Following set k1 and d2 (or vice versa) but not all 4 k/d variables:
    y.add_argument("--nudgeCallTrig15",         action=DEF_ACTION)
    y.add_argument("--nudgePutTrig15",          action=DEF_ACTION)
    y.add_argument("--nudgeCallTrigDaily",      action=DEF_ACTION)
    y.add_argument("--nudgePutTrigDaily",       action=DEF_ACTION)
    y.add_argument("--firstTickerOnly",         action=DEF_ACTION)
    y.add_argument("--first3TickersOnly",       action=DEF_ACTION)
    y.add_argument("--first10TickersOnly",      action=DEF_ACTION)
    y.add_argument("--plotEveryTimestep",       action=DEF_ACTION)
    y.add_argument("--plotName",                default="plot")
    y.add_argument("--testBuyCall",             action=DEF_ACTION)
    y.add_argument("--testBuyPut",              action=DEF_ACTION)
    y.add_argument("--testSellCall",            action=DEF_ACTION)
    y.add_argument("--testSellPut",             action=DEF_ACTION)
    y.add_argument("--disableTws",              action=DEF_ACTION)
    y.add_argument("--barSourceFile")       # Follow with filename
    y.add_argument("--useTestHarness")      # Follow with test name. Will use the named test harness instead of MyTradingApp.
    y.add_argument("--initOrderId",            action="store", type=int,
                               dest="initOrderId", default=-1, help="Choose the first order ID")
    return y

if __name__=="__main__":
    """Parser Test"""
    dut = cmdLineParseObj()
    print(dut.parse_args())



