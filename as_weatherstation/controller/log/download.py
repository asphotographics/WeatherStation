#!/usr/bin/python
# encoding=utf-8

"""
********************************************************************************
Controller Weather Station Log Download
********************************************************************************

This script manages the uploading of logs to an FTP server. It is most useful
for running on a central log processing server.

Typical I/O controllers in this project use as_weatherstation.read.*
and as_weatherstation.write.* modules. These groups of modules are tuned more
for reading and writing samples. While the FTP processes can be considered
I/O processes, they never deal with individual samples so it seems simpler
to use the as_weatherstation.app and ftputil modules directly: 
as_weatherstation.app for local files and ftputil for remote files.
We lose a layer of abstraction, but the file methods in app and ftputil
are robust and easy to reuse.

If the FTP server is only a temporary storage place, then the related controller
as_weatherstation.controller.log.upload executed on a remote weather station
computer can upload logs for this script to fetch for further processing
(DB insertion, archiving, etc.)

You probably don't want to run both UPLOAD and DOWNLOAD on the same computer:
you will download files you peviously uploaded.

This script can be executed periodicly, e.g., daily, via cron or launchd. It
can also be daemonized with init or launchd, by setting the
AS_CONTROLLER_LOG_DOWNLOAD.count instance variable to 0 (zero) thus running
an infinite loop.

The main method gets a list of log files to download, connects to the FTP server,
and downloads each file [data]/downloaded/. Downloaded files are then removed
from the FTP server.

Successful file downloads are logged to [data]/messages.txt

An error log may appear in the data folder. This file will contain ERRORS and
WARNINGS regarding script execution. The error log will be rotated when it
approaches 1 MB in size. Up to 10 old error logs will be kept, then older logs
will start to be discarded.


********************************************************************************
CONFIGURATION
********************************************************************************
app.cfg
    - basic app config: data directory, FTP connection info, station IDs and details


********************************************************************************
TODO:
********************************************************************************
- Add lock file to FTP server so we don' accidently download partial files
  being modified by another process (i.e, upload). Hopefully FTP server
  file system processes are atomic, but you never know.

- Add shortcut to move files from uploaded to downloaded if file on FTP is
  the same as a file in uploaded (no sense in having two copies of the file).
  This shouldn’t be happening, because you shouldn’t have a machine running
  both upload and download, but you never know.



********************************************************************************
CHANGELOG
********************************************************************************
v1.0 - controller created

********************************************************************************
"""

import time
import os.path

import ftputil.host as mod_ftphost
import ftputil.error as mod_ftperror

import as_weatherstation.controller.log.upload as mod_ws_controller_log_upload

import as_weatherstation.app as mod_ws_app


# For debugging
from pprint import pprint


"""
Plan:
1) Define a list of stations to deal with
2) For each station...
3) get an FTP connection
4) get a list log files on the server
5) for each log file...
6) download to [data]/downloaded
7) remove from FTP server
8) log action to message log
"""


class AS_CONTROLLER_LOG_DOWNLOAD(mod_ws_controller_log_upload.AS_CONTROLLER_LOG_UPLOAD):
    """ FTP Download Controller. Most functionality is inherited from AS_CONTROLLER_UPLOAD """

    def __init__(self):
        """ Call super().__init__() and set object attributes """

        super(AS_CONTROLLER_LOG_DOWNLOAD, self).__init__()


    def action(self, sLabels=[]):
        """
        @brief Get uploadable log files and upload them to FTP server.

        @parm sLabels list - A list of station labels to deal with. If empty,
            then the logs of all defined stations will be dealt with.
        """

        # Well, I was doing something more complex before. Now this looks wierd.
        sTime = lambda: time.time()


        # Which stations are we dealing with?
        if not sLabels:
            self.sLabels = self.app.stations.keys()
        else:
            self.sLabels = sLabels


        #t = sTime()
        # Connect to the server and cd to the storage path
        self.connect(self.app.ftp['path'])
        #print 'connect', sTime()-t


        # Get remote file list
        remoteFiles = self.listdir()


        for sLabel in self.sLabels:

            # Get a list station log files that have already been downloaded.
            logFiles = self.app.listLogFiles(self.app.stations[sLabel].id, mod_ws_app.LOGFILE_DOWNLOADED)
            
            # List only the remote files for this station
            stationRemoteFiles = self.filterFiles(remoteFiles, sLabel)
            
            if stationRemoteFiles:
                # Log execution message
                self.message_logger.info(
                    'Beginning FTP download of %d files for %s.',
                    len(stationRemoteFiles),
                    sLabel
                    )
            else:
                # Only for debugging purposes
                self.message_logger.debug('No files to download for %s.' % sLabel)
                continue

            # Try to upload the files.
            for remoteFile in stationRemoteFiles:
                
                if remoteFile in logFiles[mod_ws_app.LOGFILE_DOWNLOADED]:
                    # If file already exists in download folder then log a warning.
                    # You might want to check the error messages occasionaly,
                    # Otherwise, FTP might get clogged up with files.
                    self.error_logger.warn(
                        "'%s' already exists in download folder. Will download if newer.",
                        fileName,
                        self.app.ftp['path']
                        )

                # Do the upload and remove the remote file.
                fileName = os.path.basename(remoteFile)
                logFile = self.app.joinPath(self.app.downloadedFolder, fileName)
                try:
                    t = sTime()
                    downloaded = self.ftp.download_if_newer(remoteFile, logFile)
                    eTime = sTime()-t
                    if downloaded:
                        self.ftp.remove(remoteFile)
                except mod_ftperror.FTPError as e:
                    self.error_logger.error(e)
                    # Go on to the next file
                    continue

                if downloaded:
                    # Log completion message.
                    self.message_logger.info(
                        "Downloaded '%s' from 'ftp://%s%s' in %.4f seconds",
                        fileName,
                        self.app.ftp['host'],
                        self.app.ftp['path'],
                        eTime
                        )

            # done for sLabel in self.sLabels

        if self.ftp:
            self.disconnect()



    def filterFiles(self, paths, sLabel=''):
        """
        Loop through a list of file names and return a new list that contains only log files.
        
        @param paths lsit - File names or paths to check.
        
        @return list
        """
        if sLabel:
            sID = self.app.stations[sLabel].id
        else:
            sID = 0
        
        l = []
        for f in paths:
            if self.app.isLogFile(f, sID):
                l.append(f)
        return l


