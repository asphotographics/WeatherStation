#!/usr/bin/python
# encoding=utf-8

from signal import *
import time

import as_weatherstation.app as mod_ws_app
import as_weatherstation.config.log as mod_ws_log_config
import as_weatherstation.log.error as mod_ws_log_error
import as_weatherstation.log.message as mod_ws_log_message

from as_weatherstation.util import getInterfaces


class AS_CONTROLLER_ERROR(Exception):
    pass
class AS_CONTROLLER_ERROR_TIMEOUT(AS_CONTROLLER_ERROR):
    pass

AS_CONTROLLER_ERROR_ALL = (AS_CONTROLLER_ERROR, AS_CONTROLLER_ERROR_TIMEOUT)

class AS_CONTROLLER_ABSTRACT(object):
    
    iteration = 0 # Count of loops run.
    count = 1 # Number of loops to run. Zero = forever (e.g., if running as a daemon).
    interval = 300 # Number of seconds to wait between loops.

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
        



    def main(self, *args, **kargs):
        """
        @brief Wrap everything in a try statement and catch KeyboardInterrupt exceptions.
        
        Passes along all argeuments to _main(), action(), etc.
        """
        try:
            self._main(*args, **kargs)
        except KeyboardInterrupt as e:
            import inspect
            callerframerecord = inspect.stack()[1+back] # 0 represents this line
                                                        # 1 represents line at caller
                                                        # 2 represents line at caller's caller
            frame = callerframerecord[0]
            self.sigHandler(2, frame)



    def _main(self, *args, **kargs):
        """
        @brief Main program run loop.
        
        Can be overriden in child classes, or child can simply define self.action() and inherit this
        simple run loop. In that case, the caller might still want to change the self.count and
        self.interval arguements.
        
        Children can also define preaction() and postaction() which respectivley get called before
        and after action(), and preloop() and postloop() which respectivley get called before
        the first loop and after the last loop. pre*(), post*(), and action() are passed all
        arguements that were passed to _main().
        
        The the current iteration number is stored in self.iteration

        One can break out of the run loop by setting self.go to False.
        """
        
        
        self.preloop(*args, **kargs)
        
        self.iteration = 1
        self.go = True
        while self.go:
            
            self.preaction(*args, **kargs)
            self.action(*args, **kargs)
            self.postaction(*args, **kargs)
            
            self.iteration += 1
            if self.count > 0 and self.iteration > self.count:
                self.go = False
                break

            if self.interval > 0:
                time.sleep(self.interval)

        self.postloop(*args, **kargs)



    def preloop(self, *args, **kargs):
        """        """
        pass

    def postloop(self, *args, **kargs):
        pass
    
    def preaction(self, *args, **kargs):
        pass

    def action(self, *args, **kargs):
        pass

    def postaction(self, *args, **kargs):
        pass



    def waitForNetwork(self, wait, timeout=0):
        """
        @brief Wait for a network connection before proceeding.
        
        This is available for remote stations that may only occasionaly have network access.
        
        @param wait int - Seconds to wait between network checks.
        @param timeout optional int - If timeout is exceeded then a AS_CONTROLLER_ERROR_TIMEOUT
            will be raised. If zero, then wait forever if neccesary. Else, if wait is less than
            timeout then wait is set to equal timeout.
        """
    
        if timeout and timeout < wait:
            wait = timeout
        
        waited = 0
        while not getInterfaces():
            print wait, timeout, waited
            self.message_logger.info('No apparent network connection available.')
            time.sleep(wait)
            
            waited += wait
            
            if timeout > 0 and waited >= timeout:
                raise AS_CONTROLLER_ERROR_TIMEOUT('Network timeout of %d seconds exceeded.' % timeout)



    def configureLogging(self):
        """ Set up application level logging """
    
        mod_ws_log_config.config(self.app.errorFile, {'stations':self.app.stations, 'wsApp':self.app})
        
        self.error_logger = mod_ws_log_error.getLogger()
        self.message_logger = mod_ws_log_message.getLogger()



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
        """
        Handle runtime process signals. Override in child classes to do specific clean-up tasks.

        @param sigNum int - Number of the signal. See `man signal`
        @param stackFrame frame object - info about the code that first caught the signal
        """

        import sys
        #print "clean me"
        sys.exit(0)



    def __enter__(self):
        """ Called when instantiated by 'with class_() as var' statement """
        return self

    def __exit__(self, type, value, traceback):
        """
        Called when with statement ends. Override in child class to clean
        up resources (i.e, close files, connections, etc.)
        """
        pass
