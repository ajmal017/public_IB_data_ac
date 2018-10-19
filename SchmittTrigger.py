from nor import nor

class ShmittTrigger:
    """Input parameters are in %"""
    def __init__(self, threshLo=20, threshHi=80, tol=1):
        self.roseAbove80 = False
        self.fellUnder80 = False
        self.roseAbove20 = False
        self.fellUnder20 = False
        self.threshLo    = threshLo/100
        self.threshHi    = threshHi/100
        self.tol         = tol/100
        self.someInput   = 0.5
        self.prevInput   = 0.5

    def process(self, someInput):
        self.prevInput = self.someInput     # Remember what input was last time
        self.someInput = someInput          # Save what input is this time
        if nor(self.roseAbove80, self.roseAbove20, self.fellUnder80, self.fellUnder20):
            # If all flags are false:
            pass
            # TODO: Finish this






















