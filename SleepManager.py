from BasicStuff import BasicSuper
from numpy.random import uniform
from easyPostgresConnection import connect2IbData

def insert_sleep_time_cmd(epoch, sleep_time, time_since_last_bar):
    cmd = "INSERT INTO sleep_time (epoch, sleep_time, time_since_last_bar) VALUES ("
    cmd += str(epoch) + ", "
    cmd += str(sleep_time) + ", "
    cmd += str(time_since_last_bar) + ");"
    return cmd

class SleepManager(BasicSuper):
    def __init__(self, localStorageConnection, barSource, **kwargs):
        super().__init__(localStorageConnection, barSource, **kwargs)
        self.randomize = False
        self.time2sleep = 0                 # milliseconds
        self.timeSinceLastBar = 0           # milliseconds

    def __call__(self, *args, **kwargs):
        """Call this after attempting to find a bar.
        Required Keyword Parameters:
            receivedBar     :   Bool
            barsDone        :   Bool
            epoch           :   Int"""
        if "receivedBar" in kwargs.keys() and kwargs["receivedBar"] == True:
            self.time2sleep = 0
            self.timeSinceLastBar = 0

        elif "barsDone" in kwargs.keys() and kwargs["barsDone"] == True:
            self.time2sleep = 100
            self.timeSinceLastBar = 401

        elif self.timeSinceLastBar > 4900:
            self.time2sleep = 10

        elif self.timeSinceLastBar > 3500:
            self.time2sleep = 100

        elif self.timeSinceLastBar > 900:
            self.time2sleep = int(uniform(800, 990))

        elif self.timeSinceLastBar > 400:
            self.time2sleep = int(uniform(40, 200))

        elif self.timeSinceLastBar > 200:
            self.time2sleep = int(uniform(20, 40))

        elif self.timeSinceLastBar > 100:
            self.time2sleep = int(uniform(10, 20))

        else:
            self.time2sleep = 0
            self.timeSinceLastBar += 1

        self.timeSinceLastBar += self.time2sleep

        epoch = kwargs["epoch"]
        if self.time2sleep > 199:
            # Store naps of about 100 ms and longer:
            cmd = insert_sleep_time_cmd(epoch, self.time2sleep, self.timeSinceLastBar)
            # print(cmd)
            self.curs.execute(cmd)
            self.localStorageConnection.commit()
        return self.time2sleep/1000 # Return result in seconds


def testSleepManager():
    conn = connect2IbData()
    uut = SleepManager(localStorageConnection=conn, barSource=None)
    for m in range(0, 150):
        uut(epoch=m, receivedBar=False, barsDone=False)
    for m in range(200, 250):
        uut(epoch=m, receivedBar=True, barsDone=False)
    uut(epoch=250, receivedBar=True, barsDone = True)
    for m in range(300, 500):
        uut(epoch=m, receivedBar=False, barsDone=False)
    for m in range(600, 650):
        uut(epoch=m, receivedBar=True, barsDone=False)
    uut(epoch=250, receivedBar=True, barsDone = True)
    for m in range(700, 900):
        uut(epoch=m, receivedBar=False, barsDone=False)

if __name__=="__main__":
    testSleepManager()




