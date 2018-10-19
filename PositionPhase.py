class PositionPhase:
    def __init__(self):
        self.phase = 1
        self.numberOfPhases=6

    def advance(self):
        if self.phase < self.numberOfPhases:
            self.phase += 1
            return True
        else:
            return False

    def __str__(self):
        if self.phase == 1:
            return "Limiting Loss"
        if self.phase == 2:
            return "Lock In Small Profit"
        if self.phase == 3:
            return "Lock In Med Profit"
        if self.phase == 4:
            return "Maximizing Profit"
        if self.phase == 5:
            return "Trying to Exit"
        if self.phase == 6:
            return "Exit Successful"
