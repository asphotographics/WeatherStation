#!/usr/bin/python
# encoding=utf-8

import as_weatherstation.debugfile

import as_weatherstation.controller.abstract as mod_ws_controller_abstract

import as_weatherstation.app as mod_ws_app
import as_pws.app as mod_pws_app

import as_weatherstation.log.weather as mod_ws_log_weather

import as_weatherstation.read.log as mod_ws_read_log
import as_weatherstation.write.textlcd as mod_ws_write_textlcd


"""
********************************************************************************
Controller Phidget Weather Station Display
********************************************************************************

This uses a Phidget TextLCD device to display latest sample information.

This script can be scheduled to run periodically (i.e., with cron).

It reads the last few samples of the stations current log file, calculates
a trend (up, down, steady) for each measurement and rotates this info
out to the TextLCD.

If the TextLCD is not present then the script simply exits.

An error log may appear in the data folder. This file will contain ERRORS and
WARNINGS regarding script execution. The error log will be rotated when it
approaches 1 MB in size. Up to 10 old error logs will be kept, then older logs
will start to be discarded.


********************************************************************************
CONFIGURATION
********************************************************************************
app.cfg
	- basic app config: data directory, DB connection info, station IDs and details
  - PWS configuration (station info, Phidget TextLCD serial number)

as_ws.log.config - log configration: rotation times, backup count


********************************************************************************
CHANGELOG
********************************************************************************
v1.0 - old PWS display.py script created converted to use read/write objects


********************************************************************************
"""


"""
Plan:
2) configure logging
3) create log reader
4) create TextLCD writer
5) read samples latest samples
6) display samples via writer
"""


class AS_CONTROLLER_PWS_DISPLAY(mod_ws_controller_abstract.AS_CONTROLLER_ABSTRACT):

    def __init__(self):
        
        # Configure the logging classes.
        #
        # Speed things up by turning off some logging features.
        # see https://docs.python.org/2/howto/logging.html#optimization
        import logging
        logging._srcfile = None
        logging.logThreads = 0
        logging.logProcesses = 0

        # Get the Phidget Weather Station app object
        self.app = mod_pws_app.AS_PWS_APP()

        super(AS_CONTROLLER_PWS_DISPLAY, self).__init__()



    def main(self, sLabel=None, count=2):

        self.sLabel = sLabel

        import time
        from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException


        # TODO Create writer with attach and detach event handlers

        # Create the PWS reader
        # Create the TextLCD writer
        try:
            reader = mod_ws_read_log.AS_WS_READER_LOG(self.app, self.sLabel)
            writer = mod_ws_write_textlcd.AS_WS_WRITER_TEXTLCD(self.app)
        except PhidgetException as e:
            if e.code == PhidgetErrorCodes.EPHIDGET_TIMEOUT:
                # Since the TextLCD is not always going to be attached, don’t
                # freak out if it is not present.
                self.error_logger.warn('PhidgetException %d: %s', e.code, e.details)
            else:
                self.error_logger.error('PhidgetException %d: %s', e.code, e.details)
                raise
        except ValueError as e:
            self.error_logger.error(e)
            raise


        self.go = True
        i = 1

        print 'count %d' % count
        while self.go:

            # Wait a few seconds before checking attached status again
            try:
                writer.textLCD.textLCD.waitForAttach(10)
            except PhidgetException as e:
                if e.code == PhidgetErrorCodes.EPHIDGET_TIMEOUT:
                    pass
                    # Since the TextLCD is not always going to be attached, don’t
                    # freak out if it is not present.
                else:
                    self.error_logger.error('PhidgetException %d: %s', e.code, e.details)
                    raise


            # Check attached status and sleep if not attached
            while writer.textLCD.textLCD.isAttached() and self.go:

                print 'i %d' % count

                # TODO display samples over the reader.station.intervalSensorLog

                # Read samples and display
                try:
                    reader.read(lines=6)
                    writer.write(reader.samples, 15)
                    #TODO have method to write lines again without computing samples
                except (ValueError, TypeError) as e:
                    self.error_logger.error(e)
                    raise

                i = i+1
                if count > 0 and i > count:
                    self.go = False

        writer.textLCD.textLCD.closePhidget()

        time.sleep(3)

