from BasicStuff import BasicSuper
from numpy import mean
from LocalBarSource import LocalBarSource

class TechnicalIndicator(BasicSuper):
    def __init__(self, localStorageConnection, barSource:LocalBarSource):
        super().__init__(localStorageConnection, barSource=barSource)
        self.childIndicators = []
        self.terminationCondition=None

    def injectIndicator(self, someInd): #TechnicalIndicator):
        # assert(isinstance(someInd, TechnicalIndicator))
        self.childIndicators.append(someInd)

    def __call__(self, *args, **kwargs):
        """Get the latest bars, do any state updating, and return an indicator value."""
        pass

    def __iter__(self):
        return self

    def __next__(self):
        if self.terminationCondition is not None:
            pass




