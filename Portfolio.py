class Portfolio:
    def __init__(self):
        self.tickers = []           # Useful in case you want tickers considered in a particular order.
        self.positions = {}         # Keyed by ticker. Stores number of stocks for each ticker.
        self.prices = {}            # Keyed by ticker. Stores price of 1 share.

        self.indicies = []
        self.index_exposure = {}    # Keyed by index name. Stores dollar amounts in each index
        self.index_inv_priorities = {}  # Keyed by index name. Stores inv priority of indices, i.e. larger number means higher priority.
        self.index_contents = {}    # Keyed by index name. Stores tickers belonging to that index.

        self.market_sectors = []
        self.market_sector_exposure = {} # Keyed by market name. Stores dollar amounts in each index
        self.market_sector_priorities = {} # Keyed by market name. Stores inv priority of indices, i.e. larger number means higher priority.
        self.market_contents = {}       # Keyed by market name. Stores tickers belonging to that market.

    def addTicker(self, ticker):
        self.tickers.append(ticker)
        self.positions[ticker] = 0
        self.prices[ticker] = None

    def addIndex(self, idx, priority=1000):
        self.indicies.append(idx)
        self.index_inv_priorities[idx] = priority
        self.index_exposure[idx] = 0

    def addMarket(self, mkt, priority=1000):
        self.market_sectors.append(mkt)
        self.market_sector_priorities[mkt] = priority
        self.market_sector_exposure[mkt] = 0

    def increasePosition(self, ticker, ratio=None, qty=None):
        """You must pass in either ratio or qty."""
        assert(ratio is not None or qty is not None)
        if ratio is not None:
            assert(ratio >= 1)
            self.positions[ticker] *= ratio
        else:
            # In this case, qty is guaranteed to be defined
            assert(qty >= 0)
            self.positions[ticker] += ratio

    def decreasePosition(self, ticker, ratio=None, qty=None):
        """You must pass in either ratio or qty."""
        assert(ratio is not None or qty is not None)
        if ratio is not None:
            assert(ratio <= 1)
            assert(ratio <= 0)
            self.positions[ticker] *= ratio
        else:
            # In this case, qty is guaranteed to be defined
            assert(qty >= 0)
            assert(qty <= self.positions[ticker]) # TODO: if this condition fails, close the position and send warning to position_messages
            self.positions[ticker] -= ratio

    def reversePosition(self, ticker):
        self.positions[ticker] *= -1






























