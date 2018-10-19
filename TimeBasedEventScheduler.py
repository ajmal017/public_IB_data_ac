"""This file is for handling things that happen at a particular time,
such as enable trading at 9:30 and disable at 3:45 for a NY market."""

enableTradingHrs = {
    # Times are a tuple (hr, min)
    "NYSE_enable"           : (14,30),
    "NYSE_disable"          : (21,00),
    "NASDAQ_enable"         : (14, 30),
    "NASDAQ_disable"        : (21, 00),
    "Singapore_enable"      : (),
    "Singapore_disable"     : (),
    "Shanghai_enable"       : (),
    "Shanghai_disable"      : (),
    "EU_enable"             : (),
    "EU_disable"            : (),
    "London_enable"         : (),
    "London_disable"        : (),
    "HongKong_enable"       : (),
    "HongKong_disable"      : (),
    "Frankfurt_enable"      : (),
    "Frankfurt_disable"     : (),
    "Bombay_enable"         : (),
    "Bombay_disable"        : (),
    "NSE_India_enable"      : (),
    "NSE_India_disable"     : (),
    "Toronto_enable"        : (),
    "Toronto_disable"       : (),
    "Zurich_enable"         : (),
    "Zurich_disable"        : (),
    "Nasdaq_Nordic_enable"  : (),
    "Nasdaq_Nordic_disable" : (),
    "Sydney_enable"         : (),
    "Sydney_disable"        : (),
    "Taipei_enable"         : (),
    "Taipei_disable"        : (),
    "SaoPaulo_enable"       : (),
    "SaoPaulo_disable"      : (),
    "Madrid_enable"         : (),
    "Madrid_disable"        : ()
    }

class TimeBasedEventScheduler:
    def __init__(self):
        pass