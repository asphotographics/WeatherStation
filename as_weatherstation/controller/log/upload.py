#!/usr/bin/python
# encoding=utf-8

"""
********************************************************************************
Controller Weather Station Log Upload
********************************************************************************

This script manages the uploading of logs to an FTP server. It is most useful
for a remote weather station logger.

Typical I/O controllers in this project use as_weatherstation.read.*
and as_weatherstation.write.* modules. These groups of modules are tuned more
for reading and writing samples. While the FTP processes can be considered
I/O processes, they never deal with individual samples so it seems simpler
to use the as_weatherstation.app and ftputil modules directly:
as_weatherstation.app for local files and ftputil for remote files.
We lose a layer of abstraction, but the file methods in app and ftputil
are robust and easy to reuse.

If the FTP server is only a temporary storage place, then the related controller
as_weatherstation.controller.log.download executed on a central processing
computer can download logs for further processing (DB insertion,
archiving, etc.)

You probably don't want to run both UPLOAD and DOWNLOAD on the same computer:
you will download files you peviously uploaded.

This script can be executed periodicly, e.g., daily, via cron or launchd. It
can also be daemonized with init or launchd, by setting the
AS_CONTROLLER_LOG_DOWNLOAD.count instance variable to 0 (zero) thus running
an infinite loop.

The main method gets a list of log files to upload, connects to the FTP server,
uploads each file, and then moves each to [data]/uploaded/. The gc (garbage
collect) method can optionally be used to remove older uploaded files.

Successful file uploads are logged to [data]/messages.txt

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
- Add gc (garbage collect) method to optionally remove older uploaded files.
  
- Add lock file to FTP server so other pocesses (especially, download), don't
  mess with our unfinished uploads. Hopefully FTP server file system processes
  are atomic, but you never know.


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

import as_weatherstation.controller.abstract as mod_ws_controller_abstract

import as_weatherstation.app as mod_ws_app


# For debugging
from pprint import pprint


"""
Plan:
1) Define a list of stations to deal with
2) For each station...
3) get a list of pending log files
4) get an FTP connection
5) for each log file...
6) upload to FTP server
7) move to [data]/uploaded/
8) log action to message log
"""


class AS_CONTROLLER_LOG_UPLOAD(mod_ws_controller_abstract.AS_CONTROLLER_ABSTRACT):
    """ FTP Upload Controller """

    def __init__(self):
        """ Call super().__init__() and set object attributes """

        super(AS_CONTROLLER_LOG_UPLOAD, self).__init__()

        # Attribute representing ftputil.FTPHost object after self.connect() is called.
        self.ftp = None

        self.count = 1 # Number of loops to run. Zero = forever (e.g., if running as a daemon).
        self.interval = 3600 # Number of seconds to wait between loops.
        self.waitForNetworkInterval = 30 # Seconds to wait between network connection checks.
        self.waitForNetworkTimout = 0 # Never timeout network check



    def preaction(self, *args, **kargs):
        """ @brief Wait for a network connection before proceeding. """

        if (self.waitForNetworkInterval):
            self.waitForNetwork(self.waitForNetworkInterval, self.waitForNetworkTimout)



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


        for sLabel in self.sLabels:

            # Get the station log files.
            # Only bother with backup files (not active, imported, or anything else).
            logFiles = self.app.listLogFiles(self.app.stations[sLabel].id, mod_ws_app.LOGFILE_BACKUP)

            if logFiles[mod_ws_app.LOGFILE_BACKUP]:
                # Log execution message
                self.message_logger.info(
                    'Beginning FTP upload of %d files for %s.',
                    len(logFiles[mod_ws_app.LOGFILE_BACKUP]),
                    sLabel
                    )
            else:
                # Only for debugging purposes
                self.message_logger.debug('No files to upload for %s.' % sLabel)
                continue


            # We delay connecting until we have something to upload
            if not self.ftp:
                #t = sTime()
                # Connect to the server and cd to the storage path
                self.connect(self.app.ftp['path'])
                #print 'connect', sTime()-t


            # Try to upload the files.
            for logFile in logFiles[mod_ws_app.LOGFILE_BACKUP]:

                # Compress the file first to speed things up.
                if not self.app.isGZipped(logFile):
                    logFile = self.app.gZipFile(logFile, keepOriginal=False)

                # Do the upload.
                fileName = os.path.basename(logFile) 
                try:
                    t = sTime()
                    uploaded = self.ftp.upload_if_newer(logFile, fileName)
                    eTime = sTime()-t
                except mod_ftperror.FTPError as e:
                    self.error_logger.error(e)
                    # Go on to the next file
                    continue

                if not uploaded:
                    # If file already exists on server and is newer log a warning.
                    # you might want to check the error messages occasionaly,
                    # Otherwise, data folder might get clogged up with files.
                    self.error_logger.warn(
                        "'%s' already exists on FTP server at '%s'. Not uploading.",
                        fileName,
                        self.app.ftp['path']
                        )

                # Move file to 'uploaded' folder
                try:
                    moved = self.app.moveLogFileToUploaded(logFile)
                except e:
                    moved = False
                    self.message_logger.error(e)

                if moved:
                    # Log completion message.
                    self.message_logger.info(
                        "Uploaded '%s' to 'ftp://%s%s' in %.4f seconds",
                        fileName,
                        self.app.ftp['host'],
                        self.app.ftp['path'],
                        eTime
                        )


            # done for sLabel in self.sLabels

        if self.ftp:
            self.disconnect()



    def connect(self, path=''):
        """
        @brief Connect to the FTP server using self.app.ftp connection info.

        If raises an error if self.app.ftp['host'] is not configured.
        Logs and raises an error if connect attempt fails. If connection
        is successful, then self.ftp will be a ftputil.FTPHost object.

        @param path optional str - If not empty then we will attempt to cd
            to path after connecting. We will also automatically run the
            ftputil time synchronization method.
        """

        if isinstance(self.ftp, mod_ftphost.FTPHost):
            raise ValueError('%s.ftp is already a ftputil.FTPHost instance. Use disconnect() before connecting again.' % type(self).__name__)

        self.ftp = None

        # Raise an error if FTP not configured
        if not self.app.ftp['host']:
            raise AttributeError("No FTP server defined in %s.ftp['host']" % type(self.app).__name__)

        # Try to connect to the FTP server    
        try:
            self.ftp = mod_ftphost.FTPHost(self.app.ftp['host'], self.app.ftp['username'], self.app.ftp['password'])
        except mod_ftperror.FTPError as e:
            self.error_logger.error(e)
            raise e

        if path:
            try:
                self.cwd(path)
                self.ftp.synchronize_times()
            except mod_ftperror.FTPError as e:
                self.error_logger.error(e)
                raise e



    def disconnect(self):
        """ Close the FTP connection and destroy the self.ftp FTPHost object """

        try:
            self.ftp.close()
        except:
            pass

        self.ftp = None



    def cwd(self, path, makeDirs=True):
        """
        List files in path on server.

        @param path optional str - Directory to list. If empty, use current working directory.

        @return list - File names in directory.
        """
        try:
            self.ftp.chdir(path)
        except mod_ftperror.FTPerror as e:
            if makeDirs:
                try:
                    self.ftp.mkdirs(path)
                    self.cwd(path, makeDirs=False)
                except mod_ftperror.FTPerror as e2:
                    self.error_logger.error(e)
                    self.error_logger.error(e2)
                    raise e2
            else:
                raise e



    def listdir(self, path=''):
        """
        Change working directory on the server.

        @param path str - server directory path
        """
        if not path:
            path = self.ftp.curdir

        try:
            return self.ftp.listdir(self.ftp.curdir)
        except mod_ftperror.ParseError as e:
            self.error_logger.error(e)
            raise e


    
    def getRemoteLock(self, timeout=10):
        # TODO
        """
        make UUID hash
        stat lock file
        if not exists, upload lockfile
            wait 1 second, and then get lockfile
            if it matches the UUID then return
        if exists, download
            if contents match UUID then return true
            else, wait and check again with zero timeout
        """
        return



    def releaseRemoteLock():
        # TODO
        """
        If UUID no set return
        Download lock file
        Check contents against UUID
        If they match, then delete file
        """


    def __exit__(self):
        """ For use by the with statement. Clean up FTP connection. """

        self.disconnect()



    def sigHandler(self, sigNum, stackFrame):
        """
        Handle run-time signals. Overrides parent method.

        Call our __exit__() method and then call super().sigHandler().

        @param sigNum int - Number of the signal. See `man signal`
        @param stackFrame frame object - info about the code that first caught the signal
        """

        self.__exit__()
        super(AS_CONTROLLER_LOG_UPLOAD, self).sigHandler(sigNum, stackFrame)



