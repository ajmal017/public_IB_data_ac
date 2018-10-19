#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 11:09:18 2017
@author: jstrie
"""

import copy as cp
import time
import os

# Choose NY time:
os.environ['TZ'] = 'US/Eastern'
time.tzset()

DAILY = '1 day'
ONE_HOUR = '1 hour'
FIFTEEN_MIN = '15 min'


def minTo5SecBars(numMin):
    """Converts a duration in minutes to a quantity of 5-second bars.
    There are 60/5 = 12 five second bars in one minute."""
    return minNum * 12

def human2epoch(dateStr):
    """Returns epoch form of a human readable date string.
    dateStr must be in the form '2000-01-01 12:34:00', or YYYY-MM-DD HH:MM:SS"""
    try:
        return int(time.mktime(time.strptime(dateStr, "%Y%m%d  %H:%M:%S")))
    except:
        try:
            return int(time.mktime(time.strptime(dateStr, "%Y-%m-%d %H:%M:%S")))
        except:
            try:
                return int(time.mktime(time.strptime(dateStr, "%Y%m%d")))
            except:
                raise ValueError("Cannot find a usable format for this datestring: " + dateStr)
                return None


class epoch2human:
    def __init__(self, time0):
        """time0 is an integer representing epoch time - seconds since midnight Jan 1, 1970."""
        timeStr = time.strftime("%Y%m%d, %H:%M:%S", time.localtime(time0))
        # print(timeStr)
        self.epochTime      = time0
        self.timeStr        = timeStr
        self.year           = int(timeStr[:4])
        self.month          = int(timeStr[4:6])
        self.day            = int(timeStr[6:8])
        self.hour           = int(timeStr[10:12])
        self.minute         = int(timeStr[13:15])
        self.second         = int(timeStr[16:18])

    def __str__(self):
        return self.timeStr


def testEpoch2Human():
    """Test for the above class"""
    dut = epoch2human(time.localtime(time.time()))
    print(dut.year)
    print(dut.month)
    print(dut.day)
    print(dut.hour)
    print(dut.minute)
    print(dut.second)


def updateBar(underConst, newStuff):
    """Updates an under construction bar object"""
    if newStuff.high > underConst.high:
        underConst.high = newStuff.high

    if newStuff.low < underConst.low:
        underConst.low = newStuff.low

    underConst.close = newStuff.close
    return underConst

def twoDecimals(x):
    """Returns a float w/ 2 decimal places"""
    return int(x*100)/100

