"""Need 1 instance of each exit rule for every ticker."""

class ExitRule:
    def __init__(self):
        self.exit = False
        self.exitRuleName=None

    def __call__(self, *args, **kwargs):
        """This has to return bool"""
        raise NotImplementedError("You need to implement this, buddy.")

class EndOfDay(ExitRule):
    def __init__(self):
        """time is a tuple with (hour, minute)"""
        super().__init__()
        self.trig_hour = 15
        self.trig_minute = 45
        self.exitRuleName="End of Day"

    def __call__(self, *args, **kwargs):
        hr = kwargs["hour"]
        minute = kwargs["minute"]
        return (hr == self.trig_hour and minute >= self.trig_minute) or (hr > self.trig_hour)

class HitProfitTarget(ExitRule):
    def __init__(self, entry_price, isBull):
        """isBull = True for long position, false for short position"""
        super().__init__()
        self.exitRuleName="Hit Profit Target"
        self.percent_profit_target = 1
        self.entry_price = entry_price
        self.isBull = isBull

    def __call__(self, *args, **kwargs):
        if self.isBull:
            return (kwargs["price"] >= self.entry_price * (1 + self.percent_profit_target / 100))
        else:
            return (kwargs["price"] <= self.entry_price * (1 - self.percent_profit_target / 100))


class HitLossLimit(ExitRule):
    def __init__(self, entry_price, isBull):
        """isBull = True for long position, false for short position"""
        super().__init__()
        self.exitRuleName="Hit Loss Limit"
        self.loss_limit = 0.8
        self.entry_price = entry_price
        self.isBull = isBull

    def __call__(self, *args, **kwargs):
        if self.isBull:
            return (kwargs["price"] <= self.entry_price * (1 - self.loss_limit/100))
        else:
            return (kwargs["price"] >= self.entry_price * (1 + self.loss_limit / 100))

class Loose2Tight(ExitRule):
    def __init__(self, entryPrice, isBull, threshPercent=0.3, trailPercent=1, fastRatio=2):
        """Exit threshold starts out like a trail stop, but trail % tightens up as price moves
        in the right direction."""
        super().__init__()
        assert(isinstance(isBull, bool))
        assert (threshPercent >= 0)
        assert(fastRatio >= 1)
        self.entryPrice = entryPrice
        self.isBull = isBull
        self.prevPrice = entryPrice
        self.fastRatio = fastRatio
        if isBull:
            self.exitThresh = entryPrice * (1 - trailPercent / 100)
            self.threshPrice = entryPrice * (1 + threshPercent / 100)
        else:
            self.exitThresh = entryPrice * (1 + trailPercent / 100)
            self.threshPrice = entryPrice * (1 - threshPercent / 100)

    def __call__(self, *args, **kwargs):
        if "price" in kwargs.keys():
            price = kwargs["price"]
        else:
            price = args[0]
        if self.isBull:
            if price > self.threshPrice and price > self.prevPrice:
                # increase exitThresh by fastratio
                delta = price - self.prevPrice
                self.exitThresh += delta * self.fastRatio
                self.prevPrice = price
            elif price > self.prevPrice and price > self.prevPrice:
                # increase exitThresh 1:1
                delta = price - self.prevPrice
                self.exitThresh += delta
                self.prevPrice = price
            else:
                # If price went down, do nothing.
                pass

            # Return position close decision:
            return price < self.exitThresh

        else:
            if price < self.threshPrice and price < self.prevPrice:
                # decrease exitThresh by fastRatio
                delta = self.prevPrice - price
                self.exitThresh -= delta * self.fastRatio
                self.prevPrice = price
            elif price < self.prevPrice and price < self.prevPrice:
                # decrease exitThresh 1:1
                delta = self.prevPrice - price
                self.exitThresh -= delta
                self.prevPrice = price
            else:
                # If price went up, do nothing.
                pass

            return price > self.exitThresh

def testLoose2Tight():
    # First test long:
    print("Testing Long")
    price = 100
    uut = Loose2Tight(entryPrice=price, isBull=True, threshPercent=0.5, trailPercent=1, fastRatio=2)
    print("threshPrice    prevPrice    exitThresh    price    result")
    for m in range(120):
        price += 0.05 if m % 2 == 0 else -0.03
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)
    for m in range(40):
        price -= 0.01
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)

    # Now Test Short
    print("\n\n\n\nNow Testing Short")
    price = 100
    uut = Loose2Tight(entryPrice=price, isBull=False, threshPercent=0.5, trailPercent=1, fastRatio=2)
    print("threshPrice    prevPrice    exitThresh    price    result")
    for m in range(120):
        price += -0.05 if m % 2 == 0 else 0.03
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)
    for m in range(40):
        price += 0.01
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)

class DontCatchUp(Loose2Tight):
    """Like Loose2Tight except this one does not catch up with the stock. This one will not return True
    until price has changed direction."""
    def __init__(self, entryPrice, isBull, threshPercent1=0.3, threshPercent2=0.7, trailPercent=1, fastRatio=2):
        super().__init__(entryPrice=entryPrice, isBull=isBull, threshPercent=threshPercent1, \
                         trailPercent=trailPercent, fastRatio=fastRatio)
        if isBull:
            self.secondThreshPrice = entryPrice * (1 + threshPercent2 / 100)
        else:
            self.secondThreshPrice = entryPrice * (1 - threshPercent2 / 100)

    def __call__(self, *args, **kwargs):
        if "price" in kwargs.keys():
            price = kwargs["price"]
        else:
            price = args[0]
        if self.isBull:
            if price > self.secondThreshPrice and price > self.prevPrice:
                # increase exitThresh 1:1
                delta = price - self.prevPrice
                self.exitThresh += delta
                self.prevPrice = price
            elif price > self.threshPrice and price > self.prevPrice:
                # increase exitThresh by fastratio
                delta = price - self.prevPrice
                self.exitThresh += delta * self.fastRatio
                self.prevPrice = price
            elif price > self.prevPrice and price > self.prevPrice:
                # increase exitThresh 1:1
                delta = price - self.prevPrice
                self.exitThresh += delta
                self.prevPrice = price
            else:
                # If price went down, do nothing.
                pass
            # Return position close decision:
            return price < self.exitThresh

        else:
            if price < self.secondThreshPrice and price < self.prevPrice:
                # decrease exitThresh 1:1
                delta = self.prevPrice - price
                self.exitThresh -= delta
                self.prevPrice = price
            elif price < self.threshPrice and price < self.prevPrice:
                # decrease exitThresh by fastRatio
                delta = self.prevPrice - price
                self.exitThresh -= delta * self.fastRatio
                self.prevPrice = price
            elif price < self.prevPrice and price < self.prevPrice:
                # decrease exitThresh 1:1
                delta = self.prevPrice - price
                self.exitThresh -= delta
                self.prevPrice = price
            else:
                # If price went up, do nothing.
                pass
            return price > self.exitThresh

def testDontCatchUp():
    # First test long:
    print("Testing Long")
    price = 100
    uut = DontCatchUp(entryPrice=price, isBull=True, threshPercent1=0.3, threshPercent2=0.7, trailPercent=1, fastRatio=3)
    print("threshPrice    prevPrice    exitThresh    price    result")
    for m in range(100):
        price += 0.10 if m % 2 == 0 else -0.03
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)
    for m in range(50):
        price -= 0.01
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)

    # Now Test Short
    print("\n\n\n\nNow Testing Short")
    price = 100
    uut = DontCatchUp(entryPrice=price, isBull=False, threshPercent1=0.25, threshPercent2=0.7, trailPercent=1, fastRatio=2.8)
    print("threshPrice    prevPrice    exitThresh    price    result")
    for m in range(100):
        price += -0.10 if m % 2 == 0 else 0.03
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)
    for m in range(50):
        price += 0.01
        result = uut(price=price)
        oneStr = "    %03.2f       %03.2f       %03.2f       %03.2f      %1d" % (uut.threshPrice, uut.prevPrice, uut.exitThresh, price, result)
        print(oneStr)

class SoftTrailStop(ExitRule):
    """Put the 2:1 wrong way stuff here"""
    pass

class LowestPerformer(ExitRule):
    """Unlike others, do not necessarily call this every sample.
    Call this when you get a trigger on something else, and you want
    to ditch the lowest performer.

    Also, unlike others, you want 1 instance for all tickers."""
    def __init__(self):
        super().__init__()
        self.exitRuleName = "Lowest Performer"
        self.entryPrices = {} # % profit on competing positions
        self.nowPrices = {}
        self.isBull = {}

    def addTicker(self, ticker, entryPrice, isBull):
        self.entryPrices[ticker] = entryPrice
        self.nowPrices[ticker] = entryPrice
        self.isBull[ticker] = isBull

    def updateTicker(self, ticker, nowPrice):
        self.nowPrices[ticker] = nowPrice

    def __call__(self, *args, **kwargs):
        worstTicker = ""
        worstPayoff = 1E20
        for ticker in self.entryPrices.keys():
            if self.isBull[ticker]:
                onePayoff = self.nowPrices[ticker] - self.entryPrices[ticker]
            else:
                onePayoff = self.entryPrices[ticker] - self.nowPrices[ticker]
            onePercentage = 100 * onePayoff / self.entryPrices[ticker]
            if onePercentage < worstPayoff:
                worstPayoff = onePercentage
                worstTicker = ticker
        return (worstTicker, worstPayoff)

class PoopinAround(ExitRule):
    """If it hasn't moved 1/2 a % in the last 2 hours, ditch it."""
    def __init__(self, entryPrice, entranceTime, isBull):
        super().__init__()
        self.thresh1 = 0.1      # After 1 hr, it should move this much
        self.thresh2 = 0.33     # After 2 hr, it should move this much
        self.thresh3 = 0.67     # After 3 hr, it should move this much
        self.isBull = isBull
        self.entranceTime = entranceTime
        self.entryPrice = entryPrice

    def __call__(self, *args, **kwargs):
        now = kwargs["epoch"]
        price = kwargs["price"]
        if now >= self.entranceTime + 3*3600:
            if self.isBull:
                return price <= self.entryPrice * (1 + self.thresh3 / 100)
            else:
                return price >= self.entryPrice * (1 - self.thresh3 / 100)
        elif now >= self.entranceTime + 2*3600:
            if self.isBull:
                return price <= self.entryPrice * (1 + self.thresh2 / 100)
            else:
                return price >= self.entryPrice * (1 - self.thresh2 / 100)
        elif now >= self.entranceTime + 1*3600:
            if self.isBull:
                return price <= self.entryPrice * (1 + self.thresh1 / 100)
            else:
                return price >= self.entryPrice * (1 - self.thresh1 / 100)
        else:
            return False

class TimeLimit(ExitRule):
    """Returns True if a position has been in the market for longer than timeLimit."""
    def __init__(self, entranceTime, timeLimit):
        super().__init__()
        self.entranceTime = entranceTime
        self.timeLimit = timeLimit

    def __call__(self, *args, **kwargs):
        return kwargs["now"] > self.entranceTime + self.timeLimit

class MinimumTime(ExitRule):
    """Returns True if a position has been in the market for at least minTime.
    Algorithmically this is no difference from TimeLimit, but has names better suited
    for enabling other exit rules. For example, you might want some exit rules to only
    be enabled after a minimum amount of time.

    Note: You can also use this to ensure that a position stays CLOSED for a minimum
    length of time before opening a new position on the same ticker."""
    def __init__(self, entranceTime, minTime):
        super().__init__()
        self.entranceTime = entranceTime
        self.minTime = minTime

    def __call__(self, *args, **kwargs):
        return kwargs["now"] > self.entranceTime + self.minTime

if __name__=="__main__":
    testDontCatchUp()







