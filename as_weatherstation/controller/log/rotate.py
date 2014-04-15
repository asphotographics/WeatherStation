#!/usr/bin/python
# encoding=utf-8

import as_weatherstation.controller.abstract as mod_ws_controller_abstract

import as_weatherstation.app as mod_ws_app

import as_weatherstation.log.weather as mod_ws_log_weather


"""
********************************************************************************
Controller Log Rotate
********************************************************************************

This rotates the active log file. You should rotate the logs before doing
things like loading data into the database. But, use caution when rotating
logs while other weather station processes are running — they may currently
by accessing the active log.

For each station the weather logger is insantiated and told to rotate the log.

Backup log file names look like "log_station_[id].txt.2014-04-08_07-19-01".

If the log file is empty (zero bytes) then we don't bother rotating it.

An error log may appear in the data folder. This file will contain ERRORS and
WARNINGS regarding script execution. The error log will be rotated when it
approaches 1 MB in size. Up to 10 old error logs will be kept, then older logs
will start to be discarded.


********************************************************************************
CONFIGURATION
********************************************************************************
app.cfg
    - basic app config: data directory, DB connection info, station IDs and details

as_ws.log.config - log configration: rotation times, backup count


********************************************************************************
CHANGELOG
********************************************************************************
v1.0 - controller created


********************************************************************************
"""


"""
Plan:
1) get a list of stations
2) use station weather logger object to force a file rotation
"""



class AS_CONTROLLER_LOG_ROTATE(mod_ws_controller_abstract.AS_CONTROLLER_ABSTRACT):

    def __init__(self):

        super(AS_CONTROLLER_LOG_ROTATE, self).__init__()



    def main(self):
        """ Rotate logs for each station """

        for sLabel in self.app.stations:
            self.rotateLog(sLabel)



    def rotateLog(self, sLabel):
        """ Use the weather logger object to force a rotation of the log file """

        import os
        from os.path import isfile

        try:
            weather_logger = mod_ws_log_weather.getLogger(self.app.stations[sLabel].id)
            
            # Skip missing files
            if not isfile(weather_logger.handlers[0].baseFilename):
                return
            
            # Skip logs that are zero bytes
            stat = os.stat(weather_logger.handlers[0].baseFilename)
            if stat.st_size == 0:
                return
            
            weather_logger.handlers[0].doRollover()
    
        except Exception as e:
            self.error_logger.error(e)
            raise e
