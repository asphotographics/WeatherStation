#!/usr/bin/python
# encoding=utf-8

import as_weatherstation.controller.abstract as mod_ws_controller_abstract

import as_weatherstation.app as mod_ws_app
import as_pws.app as mod_pws_app

import as_weatherstation.log.weather as mod_ws_log_weather

import as_weatherstation.read.pws as mod_ws_read_pws
import as_weatherstation.write.log as mod_ws_write_log


"""
********************************************************************************
Controller Phidget Weather Station Main
********************************************************************************

This controller executes the main run loop of the Phidget Weather Station.

This script is designed to run continuously and should be started with
initd or launchd. It should run as a daemon and only one instance
should be run at any given time (becuase only one process can access
the Phidget Interface Kit at a time).

After the Phidget InterfaceKit is connected, event callbacks are bound
and the main loop starts.

Analog sensors are polled periodically and an average of several polls is
written to a log.

Events are called when digital sensor values change and we capture these events
in different ways depending on the type of sensor.

Logs are set aside each day. Old logs have a timestamp appended to their name.

An error log may appear in the data folder. This file will contain ERRORS and
WARNINGS regarding script execution. The error log will be rotated when it
approaches 1 MB in size. Up to 10 old error logs will be kept, then older logs
will start to be discarded.


********************************************************************************
CONFIGURATION
********************************************************************************
app.cfg
    - basic app config: data directory, DB connection info, station IDs and details
  - PWS configuration (sensor/input port assignment, rain gauge calibration
        logging/polling intervals)

as_ws.log.config - log configration: rotation times, backup count


********************************************************************************
CHANGELOG
********************************************************************************
v1.0 - old PWS measurer.py script created converted to use read/write objects


********************************************************************************
"""


"""
Plan:
1) create reader
2) create writer
3) enter main run loop...
4) read samples at regular intervals
5) handle input change events
6) aggregate samples
7) log samples
"""


class AS_CONTROLLER_PWS_MAIN(mod_ws_controller_abstract.AS_CONTROLLER_ABSTRACT):

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

        super(AS_CONTROLLER_PWS_MAIN, self).__init__()



    def main(self, sLabel=None):

        self.sLabel = sLabel

        import time
        from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException


        # Create the PWS reader
        try:
            reader = mod_ws_read_pws.AS_WS_READER_PWS(self.app, self.sLabel)
        except PhidgetException as e:
            self.error_logger.error('PhidgetException %d: %s', e.code, e.details)
            raise
        except ValueError as e:
            self.error_logger.error(e)
            raise


        # Get the station logger
        log_logger = mod_ws_log_weather.getLogger(reader.station.id)

        # Create the log writer
        writer = mod_ws_write_log.AS_WS_WRITER_LOG(self.app, log_logger)


        # Main run loop
        self.go = True
        while self.go == True:

            i = 0
            while i < reader.station.intervalSensorLog:

                #print "Sample %d" % ((i+reader.station.intervalSensorSample)/reader.station.intervalSensorSample)

                # Read the samples from the PWS
                try:
                    reader.read()
                except PhidgetException as e:
                    self.error_logger.error('PhidgetException %d: %s', e.code, e.details)
                    raise
                except ValueError as e:
                    self.error_logger.error(e)
                    raise

                time.sleep(reader.station.intervalSensorSample)
                i = i+reader.station.intervalSensorSample

            # Aggregate the samples and write them to the log
            samples = reader.aggregateSamples(reader.flushSamples())
            writer.write(samples)

