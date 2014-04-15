#!/usr/bin/python
# encoding=utf-8

import as_weatherstation.controller.abstract as mod_ws_controller_abstract

import as_weatherstation.app as mod_ws_app
import as_nws.app as mod_nws_app
import as_weatherstation.netatmo.error as mod_ws_netatmo_error

import as_weatherstation.log.weather as mod_ws_log_weather
import as_weatherstation.log.timestamp as mod_ws_log_timestamp

import as_weatherstation.read.netatmo as mod_ws_read_netatmo
import as_weatherstation.write.log as mod_ws_write_log



"""
********************************************************************************
Controller Netatmo Archive
********************************************************************************

Archive Netatmo measurements to local log files using the lnetamo
api wrapper.

You can define multiple Netatmo devices and modules as long as you have
administrative access to the those devices.

Logs are set aside each day. Old logs have a timestamp appended to their name.

The time of the last sample received for each station is recorded in a
local file as well. The script uses this timestamp to pick-up where it left off
on subsequent runs.

An error log may appear in the data folder. This file will contain ERRORS and
WARNINGS regarding script execution. The error log will be rotated when it
approaches 1 MB in size. Up to 10 old error logs will be kept, then older logs
will start to be discarded.


********************************************************************************
CONFIGURATION
********************************************************************************
app.cfg
  - basic app config: data directory, DB connection info,
    station IDs and details
	- Netatmo API and user credentials

as_ws.log.config - log configration: rotation times, backup count


********************************************************************************
CHANGELOG
********************************************************************************
v1.0 - script created, as well as as_nws (Netatmo weather station)
       and as_ws (weather station) modules


********************************************************************************
TODO
********************************************************************************
- Add hooks to send latest measurements to OpenWeatherMap


********************************************************************************
IDEAS
********************************************************************************
- change timestamp logger so that it records the full latest measurements
  in the same formate as the log logger

********************************************************************************
"""


"""
Plan:
2) Create Netatmo reader
1) For each Netatmo station...
3) create Netamo writer
4) determin measurement query params (start time, types, etc.)
5) read samples from Netatmo api
6) write samples to station log
"""



class AS_CONTROLLER_NETATMO_ARCHIVE(mod_ws_controller_abstract.AS_CONTROLLER_ABSTRACT):

    def __init__(self):
        
        # Configure the logging classes.
        #
        # Speed things up by turning off some logging features.
        # see https://docs.python.org/2/howto/logging.html#optimization
        import logging
        logging._srcfile = None
        logging.logThreads = 0
        logging.logProcesses = 0

        # Get the Netatmo Weather Station app object
        self.app = mod_nws_app.AS_NWS_APP()

        super(AS_CONTROLLER_NETATMO_ARCHIVE, self).__init__()



    def main(self):

        import time
        from urllib2 import HTTPError

        # Create the read object (this authenticates with the Netatmo API
        # and refreseshes the device list)
        try:
            reader = mod_ws_read_netatmo.AS_WS_READER_NETATMO(self.app)
        except HTTPError, e:
            mod_ws_netatmo_error.NetatmoHTTPErrorHandler(e, self.error_logger)


        # Loop through the configured station list
        for sID in self.app.stations:


            # Alias the station object
            s = self.app.stations[sID]


            # Only look at stations of type Netatmo device or module
            if not s.stype in [mod_ws_app.STYPE_NETATMO_DEVICE, mod_ws_app.STYPE_NETATMO_MODULE]:
                continue


            # Get the station loggers
            log_logger = mod_ws_log_weather.getLogger(s.id)
            timestamp_logger = mod_ws_log_timestamp.getLogger(s.id)


            # Try to get the last run timestamp from...
            #
            # ... the timestampFile
            timestamp = mod_ws_log_timestamp.getLatestTimestamp(s.timestampFile)
            if timestamp is None:
                # ... or the logFile
                timestamp = mod_ws_log_weather.getLatestTimestamp(s.logFile)
                if timestamp is None:
                    # ... or the app config
                    timestamp = time.strptime(self.app.oldestTimestamp, "%Y-%m-%d %H:%M:%S")


            # Check that the configured device/module actually exists	in the Netatmo API
            if s.stype is mod_ws_app.STYPE_NETATMO_DEVICE:
                if not reader.deviceList.stations.has_key(s.deviceID) :
                    self.error_logger.error('Device "%s" is not a valid Netatmo device for the user', s.deviceID)
                    continue
            if s.stype is mod_ws_app.STYPE_NETATMO_MODULE:
                if not (reader.deviceList.stations.has_key(s.deviceID) and reader.deviceList.modules.has_key(s.moduleID)):
                    self.error_logger.error('Module "%s|%s" is not a valid Netatmo device for the user', s.deviceID, s.moduleID)
                    continue


            # Prepare the API params	
            beginTime = int(time.mktime(timestamp)) + 1 # start 1 second after the last run
            params = {
                'deviceID': s.deviceID,
                'moduleID': s.moduleID,
                'scale': 'max',
                'beginTime': beginTime,
                'endTime': None,
                'limit': None
                }
            #pprint(params)


            # Read the samples
            samples = reader.read(params)


            # There could be several reasons why the samples list is empty...
            if len(samples) == 0:

                # ...request error
                if not (reader.rawData['status'] == 'ok'):
                    self.error_logger.error('Netatmo.deviceList.getMeasure failed with status "%s"', reader.rawData['status'])
                    continue

                # empty result	
                if len(reader.rawData['body']) == 0:
                    beginTimeString = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(beginTime))
                    self.error_logger.warn('Netatmo.deviceList.getMeasure returned zero measurements starting at %s for station %d', beginTimeString, s.id)
                    continue


            # Write the samples to the log
            writer = mod_ws_write_log.AS_WS_WRITER_LOG(self.app, log_logger, timestamp_logger)
            writer.write(samples)

            # Reset the samples list for the next run
            reader.resetSamples()

