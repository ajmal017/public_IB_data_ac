class TradeExecutor:
    def __init__(self, storageConnection, ibClient):
        self.storageConnection = storageConnection
        self.ibClient = ibClient

    def run(self):
        raise ValueError("Overload this!")


class BacktestTradeExecutor(TradeExecutor):
    def __init__(self, storageConnection, ibClient):
        super().__init__(storageConnection, ibClient)


class RealTimeTradeExecutor(TradeExecutor):
    def __init__(self, storageConnection, ibClient):
        super().__init__(storageConnection, ibClient)

