class CashManagerStub:
    def __init__(self):
        pass


class CashManagerStupid(CashManagerStub):
    """This is a trivial implemention of CashManager."""
    def __init__(self, answer=True):
        self.answer = answer

    def ok2MakeTrade(self, *args):
        return self.answer


class CashManagerSmart(CashManagerStub):
    def __init__(self, localStorageConnection):
        self.localStorageConnection = localStorageConnection

    def ok2MakeTrade(self):
        pass

