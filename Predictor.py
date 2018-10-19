from BasicStuff import BasicSuper
from LocalBarSource import LocalBarSource
# from TechnicalIndicator import TechnicalIndicator

class Predictor(BasicSuper):
    def __init__(self, localStorageConnection, barSource:LocalBarSource, outputRule):
        super().__init__(localStorageConnection, barSource=barSource)
        self.childPredictors = []
        self.indicators = []
        self.outputRule = outputRule
        self.iterTerminationRule = None

    def addPredictor(self, somePredictor):
        self.childPredictors.append(somePredictor)

    def addIndicator(self, someInd):
        self.indicators.append(someInd)

    def processOneBar(self):
        raise NotImplementedError()

    def long(self):
        """Call this to test whether stock might be going up."""
        raise NotImplementedError()

    def short(self):
        """Call this to test whether stock might be going down."""
        raise NotImplementedError()

    def __iter__(self):
        return self

    def __next__(self):
        if self.iterTerminationRule is not None:
            pass

class DummyPredictor(Predictor):
    """This implementation of Predictor returns alternating True/False regardless of whether you call long or short."""
    def __init__(self, localStorageConnection, barSource:LocalBarSource, outputRule):
        super().__init__(localStorageConnection, barSource=barSource, outputRule=outputRule)
        self.state = False

    def processOneBar(self):
        """Prevents you from getting the not implemented error."""
        pass

    def long(self):
        self.state = not self.state
        return self.state

    def short(self):
        return self.long()