'''
Simple logging functions 
'''
VERBOSE_LOGGING = False


def setVerboseLogging(enabled):
    global VERBOSE_LOGGING
    VERBOSE_LOGGING = enabled

def logA(message):
    print (message)

def logV(message):
    if VERBOSE_LOGGING:
        print (message)