#!/usr/bin/python
# encoding=utf-8

import as_weatherstation.app as mod_ws_app
import as_weatherstation.config.log as mod_ws_log_config
import as_weatherstation.log.error as mod_ws_log_error

from signal import *



class AS_CONTROLLER_ABSTRACT(object):

    def __init__(self):

        if not ('app' in self.__dict__):
            # Get the Phidget Weather Station app object
            self.app = mod_ws_app.AS_WS_APP()


        # Configure signal handlers for various process signals
        if not ('signals' in self.__dict__):
            import os
            # SIGNINT (interupt) is actually converted by Python to a
            # KeyboardInterrupt exception and handled eplicitly by self.main
            self.signals = [SIGINT, SIGTERM, SIGHUP]
            
        self.setSigHandler(self.signals, self.sigHandler)

        self.configureLogging()



    def main(self):
        """ Wrap everything in a try statement and catch KeyboardInterrupt exceptions. """
        try:
            self._main()
        except KeyboardInterrupt as e:
            import inspect
            callerframerecord = inspect.stack()[1+back] # 0 represents this line
                                                        # 1 represents line at caller
                                                        # 2 represents line at caller's caller
            frame = callerframerecord[0]
            self.sigHandler(2, frame)




    def _main(self):
        """ Main program code goes here. Override in child classes. """
        pass



    def configureLogging(self):
        """ Set up application level logging """
    
        mod_ws_log_config.config(self.app.errorFile, {'stations':self.app.stations, 'wsApp':self.app})
        
        self.error_logger = mod_ws_log_error.getLogger()



    def setSigHandler(self, signals, handler):
        """ Set a signal handler for the given signals (SIG*) """

        # see `man signal` for valid signals
        # Windows has other restrictions:
        # https://docs.python.org/2/library/signal.html#signal.signal
        for sig in signals:
            # Some signals are not supported on Windows which raises an error.
            try:
                signal(sig, handler)
            except ValueError as e:
                continue




    def sigHandler(self, sigNum, stackFrame):
        """ Handle runtime process signals. Override in child classes to do specific clean-up tasks. """

        import sys
        #print "clean me"
        sys.exit(0)

