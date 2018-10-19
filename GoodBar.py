from ibapi.common import BarData

class GoodBar(BarData):
    def __init__(self, ticker, timeframe, epoch=0):
        super().__init__()
        assert(timeframe == "5 sec" or timeframe == "15 min" or timeframe == "daily")
        setattr(self, "epoch", epoch)
        setattr(self, "timeframe", timeframe)
        setattr(self, "ticker", ticker.upper())
