"""Tracks information associated with 1 position. Need one instance per position."""
from ExitRules import *
from barTools import epoch2human

class Position:
    """This is where you bring all your exit rules together into 1 class """
    def __init__(self, ticker, entryTime, entryPrice, isBull, minTime=120, maxTime=3600*9):
        self.ticker = ticker
        self.entryTime = entryTime
        self.entryPrice = entryPrice
        self.isBull = isBull
        self.enableMinPositionTime = True       # Do not enable other closes until minimum time has been reached.
        self.enableMaxPositionTime = False      # Close a position because it has been in market for X time.
        self.enableEndOfDayExit = True          # Close a position because we're near the end of the trading day.
        self.enableChase = True                 # Close a position that went the right way.
        self.enablePoop = True                  # Close position for shenanigans.

        # Enable Entrance Rules, keyed by ticker:
        self.enableMinTime2Open = False         # Minimum time a prior position must be closed before new position can be opened

        # Rules, keyed by ticker:
        self.minPositionTime = MinimumTime(entranceTime=entryTime, minTime=minTime)
        self.timeLimiter = TimeLimit(entranceTime=entryTime, timeLimit=maxTime)
        self.endOfDayExit = EndOfDay()
        self.priceChaser = DontCatchUp(entryPrice=entryPrice, isBull=isBull, threshPercent1=0.3, threshPercent2=0.7, \
                                       trailPercent=1, fastRatio=2.2)
        self.poopDetector = PoopinAround(entryPrice=entryPrice, entryTime=entryTime, isBull=isBull)
        self.exitReason = ""
        self.exitTime = None

    def exitedYet(self):
        return self.exitTime is not None and self.exitTime > 0

    def update(self, epoch, price):
        if self.enableChase:
            if self.priceChaser(price=price):
                self.exitReason = "Price Chase Is Over"
                self.exitTime = epoch
                return True
        if self.enablePoop:
            if self.poopDetector(epoch=epoch, price=price):
                self.exitReason = "Poop Detected"
                self.exitTime = epoch
                return True
        if self.enableEndOfDayExit:
            humanThing = epoch2human(epoch)
            if self.endOfDayExit(hour=humanThing.hour, minute=humanThing.minute):
                self.exitReason = "Time to go home"
                self.exitTime = epoch
                return True
        if self.enableMaxPositionTime:
            if self.timeLimiter(now=epoch):
                self.exitReason = "Arrested for Loitering"
                self.exitTime = epoch
                return True
        return False
