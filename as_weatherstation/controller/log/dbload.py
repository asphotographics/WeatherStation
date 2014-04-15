#!/usr/bin/python
# encoding=utf-8

import logging

import as_weatherstation.controller.abstract as mod_ws_controller_abstract

import as_weatherstation.app as mod_ws_app

import as_weatherstation.read.log as mod_ws_read_log
import as_weatherstation.write.db as mod_ws_write_db


"""
********************************************************************************
Controller Log DB Load
********************************************************************************

This loads weather measurement data from log files and writes it to the database.

This script can be scheduled to run daily (i.e., with cron).

It reads all the backup log files in the log directory for each configured
station.

Backup log file names look like "log_station_[id].txt.2014-04-08_07-19-01".

This script does not load active log files (like "log_station_[id].txt") because
those may be in use by some other process. Active log files are backed up each
day, or may be backed up on demand with controller_log_rotate.py

After the log data is inserted into the database, the backup log files are
gzip'ed and moved to the data/log/imported/ directory.

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
v1.0 - old PWS data_load.py script converted to use read/write objects


********************************************************************************
"""


"""
Plan:
1) create reader
2) create writer
3) get a list of sample files to load
4) read samples files
5) insert samples into DB
6) archive sample files
"""



class AS_CONTROLLER_LOG_DBLOAD(mod_ws_controller_abstract.AS_CONTROLLER_ABSTRACT):

    def __init__(self):
        
        # Configure the logging classes.
        #
        # Speed things up by turning off some logging features.
        # see https://docs.python.org/2/howto/logging.html#optimization
        logging._srcfile = None
        logging.logThreads = 0
        logging.logProcesses = 0

        super(AS_CONTROLLER_LOG_DBLOAD, self).__init__()



    def main(self):

        for sLabel in self.app.stations:
            self.loadStationData(sLabel)



    def loadStationData(self, sLabel):

        # Get a lost of log backup files. These are the old log
        # files that have been rotated out, but that have not
        # yet been imported.
        files = self.app.listLogFiles(self.app.stations[sLabel].id, mod_ws_app.LOGFILE_BACKUP)

        for logFile in files[mod_ws_app.LOGFILE_BACKUP]:
            self.loadStationLog(sLabel, logFile)
            self.app.moveLogFileToImported(logFile, True)



    def loadStationLog(self, sLabel, logFile):

        try:
            # Create the PWS reader
            # and read the samples
            reader = mod_ws_read_log.AS_WS_READER_LOG(self.app, sLabel)
            reader.read(log=logFile)
            # Create the DB writer
            # and insert the samples
            writer = mod_ws_write_db.AS_WS_WRITER_DB(self.app, sLabel)
            writer.write(reader.samples)
        except (ValueError, TypeError, AttributeError) as e:
            self.error_logger.error(e)
            raise
