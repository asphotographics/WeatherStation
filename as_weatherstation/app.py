#! /usr/bin/python
# coding: utf-8

import os
from collections import OrderedDict
import re
import ConfigParser

import config.app as mod_config_app

# Bitwise measurement types
MEASURE_ABSTRACT = 0
MEASURE_TEMPERATURE = 1
MEASURE_RELATIVE_HUMIDITY = 2
MEASURE_STATION_BAROMETRIC_PRESSURE = 4
MEASURE_PRECIPITATION_WEIGHT = 8
MEASURE_INTERNAL_TEMPERATURE = 16
MEASURE_CO2 = 32
MEASURE_NOISE = 64
MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE = 128
MEASURE_PRECIPITATION = 256


# Station type constants
STYPE_PWS = 'STYPE_PWS'
STYPE_NETATMO_DEVICE = 'STYPE_NETATMO_DEVICE'
STYPE_NETATMO_MODULE = 'STYPE_NETATMO_MODULE'
STYPE_NETATMO_MODULE_INDOOR = 'STYPE_NETATMO_MODULE_INDOOR'
STYPE_NETATMO_MODULE_RAIN_GAUGE = 'STYPE_NETATMO_MODULE_RAIN_GAUGE'

NETATMO_STYPE_LOOKUP = OrderedDict()
NETATMO_STYPE_LOOKUP['NAMain'] = STYPE_NETATMO_DEVICE
NETATMO_STYPE_LOOKUP['NAModule1'] = STYPE_NETATMO_MODULE
NETATMO_STYPE_LOOKUP['NAModule4'] = STYPE_NETATMO_MODULE_INDOOR
NETATMO_STYPE_LOOKUP['NAModule3'] = STYPE_NETATMO_MODULE_RAIN_GAUGE


# Phidget Weather Station IO type constants
PWS_IO_SENSOR = 0
PWS_IO_INPUT = 1
PWS_IO_OUTPUT = 2


# Bitwise logfile types
LOGFILE_CURRENT = 1 # the file that is currently being logged to
LOGFILE_BACKUP = 2 # backup files created by log rotate (have ".[datatime]" appended, possibly GZIPed)
LOGFILE_IMPORTED = 4 # file that has already been imported into the DB (GZIPed)
LOGFILE_UPLOADED = 8 # files that have been uploaded to the FTP server
LOGFILE_DOWNLOADED = 16 # files downloaded from the FTP server
LOGFILE_ALL = 31 # All -- update this if adding new types


DB_MAIN = 1 # main database

class AS_WS_APP(object):
    """Configuration settings for weather station app"""

    def __init__(self):

        import socket
        self.hostname = socket.gethostname()

        if not hasattr(self, '_config'):
            self._config = mod_config_app.getConfig()


        # Log file location
        self._setDataFolder(self._config.get('app', 'dataFolder'))

        self.logFileDatePattern = '(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})'

        """
        Stations
        ***

        StationIDs are unique and assigned in the DB table `as_pws_station`.

        Everystation should have an altitude property so we can do
        station-to-sea-level atmospheric pressure calculations

        It is also nice to set the latitude and longitude properties so we
        can correlate weather data to a geographic location.


        Netatmo
        ***
        Every Netatmo individual module and the host device are each
        considered a "station". We don’t talk to the stations directly (yet).
        Instead we talk to http://api.netatmo.net.

        The DeviceID of the main station is its MAC address (listed by a
        call to http://api.netatmo.net/api/getuser).

        The ModuleID of each attached module is listed in the "devices"
        property of a call to http://api.netatmo.net/api/devicelist


        Phidget Weather Station
        ***
        TODO


        Stations are configured in app.cfg
        """
        self.stations = OrderedDict()
        sList = self._config.options('stations')
        for sLabel in sList :

            sID = self._config.getint('stations', sLabel)
            sSection = "station%d" % sID
            sOptions = self._config.options(sSection)
            options = {}

            # stype is required
            stype = self._config.get(sSection, 'stype')

            sclass = STYPE_CLASS_LOOKUP[stype]

            # Get the option spec for stype
            optionsSpec = sclass.optionsSpec()

            for o in sOptions :
                # Because station options are quite dynamic, we have a helper
                # convert the values to the proper types for us.
                options[o] = mod_config_app.getStationOption(self._config, optionsSpec, sSection, o)

            self.stations[sLabel] = sclass(
                self,
                sLabel,
                sID,
                options
                )


        self.db = {}
        # if a database connection is defined specific to the current host, use it
        # This is more for development than anything else, so you can have a
        # seperate database config for your development environment versus production.
        dbSection = "database_main_%s" % self.hostname.lower()
        if not self._config.has_section(dbSection): dbSection = 'database_main'
        try:
            self.db[DB_MAIN] = AS_DB_CONNECT(
                self._config.get(dbSection, 'host'),
                self._config.get(dbSection, 'user'),
                self._config.get(dbSection, 'password'),
                self._config.get(dbSection, 'database')
                )
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as e:
             self.db[DB_MAIN] = AS_DB_CONNECT('', '', '', '')


        try:
            self.ftp = {
                'host': self._config.get('ftp', 'host'),
                'username': self._config.get('ftp', 'username'),
                'password': self._config.get('ftp', 'password'),
                'path': self._config.get('ftp', 'path')
                }
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as e:
            self.ftp = {'host':'', 'username':'', 'password': '', 'path':''}



        # Dictionary mapping measurement types to their equivelant
        # location in various datasources.
        #
        # This is how we get data from, say a commercial weather station,
        # and map it to our generic database or log file format.
        self.fieldMap = {}

        # Map of columns in the log file.
        #
        # If you append a new column here, update the log formatter
        # in as_nma/config/log.py
        #
        # Do not change the order unless you want to mess up
        # the parsing of older logs. Just append new elements
        # to the end.
        self.fieldMap['log'] = [
            MEASURE_TEMPERATURE,
            MEASURE_RELATIVE_HUMIDITY,
            MEASURE_STATION_BAROMETRIC_PRESSURE,
            MEASURE_PRECIPITATION_WEIGHT,
            MEASURE_INTERNAL_TEMPERATURE,
            MEASURE_CO2,
            MEASURE_NOISE,
            MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE,
            MEASURE_PRECIPITATION
        ]


        # Map of database column names
        #
        # Change these only if you have a good reason for modifying
        # the database schema
        self.fieldMap['db'] = {
            MEASURE_TEMPERATURE: 'fTemperature',
            MEASURE_RELATIVE_HUMIDITY: 'fRelativeHumidity',
            MEASURE_STATION_BAROMETRIC_PRESSURE: 'fStationBarometricPressure',
            MEASURE_PRECIPITATION_WEIGHT: 'fPrecipitationWeight',
            MEASURE_INTERNAL_TEMPERATURE: 'fInternalTemperature',
            MEASURE_CO2: 'fCO2',
            MEASURE_NOISE: 'fNoise',
            MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE: 'fSeaLevelBarometricPressure',
            MEASURE_PRECIPITATION: 'fPrecipitation'
        }

        # Map of Netatmo measurment names available on the main device
        self.fieldMap[STYPE_NETATMO_DEVICE] = {
            MEASURE_TEMPERATURE: 'Temperature',
            MEASURE_RELATIVE_HUMIDITY: 'Humidity',
            MEASURE_STATION_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION_WEIGHT: None,
            MEASURE_INTERNAL_TEMPERATURE: None,
            MEASURE_CO2: 'Co2',
            MEASURE_NOISE: 'Noise',
            MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE: 'Pressure',
            MEASURE_PRECIPITATION: None
        }

        # Map of Netatmo measurement names available on the outdoor module
        self.fieldMap[STYPE_NETATMO_MODULE] = {
            MEASURE_TEMPERATURE: 'Temperature',
            MEASURE_RELATIVE_HUMIDITY: 'Humidity',
            MEASURE_STATION_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION_WEIGHT: None,
            MEASURE_INTERNAL_TEMPERATURE: None,
            MEASURE_CO2: None,
            MEASURE_NOISE: None,
            MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION: None
        }

        # Map of Netatmo measurment names available on an indoor additional module
        self.fieldMap[STYPE_NETATMO_MODULE_INDOOR] = {
            MEASURE_TEMPERATURE: 'Temperature',
            MEASURE_RELATIVE_HUMIDITY: 'Humidity',
            MEASURE_STATION_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION_WEIGHT: None,
            MEASURE_INTERNAL_TEMPERATURE: None,
            MEASURE_CO2: 'Co2',
            MEASURE_NOISE: None,
            MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION: None
        }

        # Map of Netatmo measurment names available on a rain gauge
        self.fieldMap[STYPE_NETATMO_MODULE_RAIN_GAUGE] = {
            MEASURE_TEMPERATURE: None,
            MEASURE_RELATIVE_HUMIDITY: None,
            MEASURE_STATION_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION_WEIGHT: None,
            MEASURE_INTERNAL_TEMPERATURE: None,
            MEASURE_CO2: None,
            MEASURE_NOISE: None,
            MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION: 'Rain'
        }

        # Map of Phidget sensor/input numbers
        self.fieldMap[STYPE_PWS] = {
            MEASURE_TEMPERATURE: [PWS_IO_SENSOR, 'sensorTemp'],
            MEASURE_RELATIVE_HUMIDITY: [PWS_IO_SENSOR, 'sensorRH'],
            MEASURE_STATION_BAROMETRIC_PRESSURE: [PWS_IO_SENSOR, 'sensorBP'],
            MEASURE_PRECIPITATION_WEIGHT: [PWS_IO_SENSOR, 'sensorLoad'],
            MEASURE_INTERNAL_TEMPERATURE: [PWS_IO_SENSOR, 'sensorInternalTemp'],
            MEASURE_CO2: None,
            MEASURE_NOISE: None,
            MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE: None,
            MEASURE_PRECIPITATION: [PWS_IO_INPUT, 'inputRG']
        }



    def _setDataFolder(self, folder):
        """ Set the path to the data folder, which in turn defines paths to all the sub folders and files """
        self.dataFolder = os.path.join(folder, '')

        # Subfolders
        self.logFolder = self.dataFolder + "log/"
        self.importedFolder = self.logFolder + "imported/"
        self.uploadedFolder = self.logFolder + "uploaded/"
        self.downloadedFolder = self.logFolder + "downloaded/"

        self.errorFile = self.dataFolder + "error.txt"

        self.logFileName = "log_station_%d.txt"
        self.logFileNamePattern = "log_station_\d+.txt"

        self.logFile = self.logFolder + self.logFileName
        self.timestampFile = self.logFolder + "latest_station_%d.txt"


        self.subfolders = OrderedDict()
        self.subfolders[LOGFILE_BACKUP] = self.logFolder
        self.subfolders[LOGFILE_IMPORTED] = self.importedFolder
        self.subfolders[LOGFILE_UPLOADED] = self.uploadedFolder
        self.subfolders[LOGFILE_DOWNLOADED] = self.downloadedFolder


    def getLogFile(self, stationID):
        """ Full path to the log file, including its name """
        return self.logFolder + self.getLogFileName(stationID)


    def getLogFileName(self, stationID):
        """ Just the name of the log file, not the full path """
        return self.logFileName % stationID


    def getTimestampFile(self, stationID):
        """ Full path to the timestamp file for the station """
        return self.timestampFile % stationID


    def listLogFiles(self, stationID, lftype=LOGFILE_ALL):
        """ Get a list of log files by class: LOGFILE_CURRENT, LOGFILE_BACKUP,  LOGFILE_IMPORTED, LOGFILE_ALL """

        files = {}

        if lftype & LOGFILE_CURRENT:

            files[LOGFILE_CURRENT] = []
            f = self.getLogFile(stationID)
            if os.path.isfile(f):
                files[LOGFILE_CURRENT].append(f)

        for t in self.subfolders:

            if lftype & t:

                files[t] = []
                allFiles = AS_WS_APP.listDirectoryFiles(self.subfolders[t])
                path = self.joinPath(self.subfolders[t], self.getLogFileName(stationID))  
                regex = re.compile(re.escape('%s.' % path) + self.logFileDatePattern)
                for f in allFiles:
                    if not regex.match(f) is None:
                        files[t].append(f)

        return files



    def isLogFile(self, path, stationID=False):
        """
        Check that a path string contains what looks like a log file name.

        @param path string - Path to check. Can also just be a file name.
        @param stationID - If not False, then check to see if file belongs
            to given station. Otherwise, stationID is a wildcard and any
            station's log file will match.

        @return bool
        """

        if stationID:
            pattern = self.getLogFileName(stationID)
        else:
            pattern = self.logFileNamePattern

        regex = re.compile(pattern)

        return bool(regex.match(path))



    def joinPath(self, *args):
        return os.path.join(*args)



    @staticmethod
    def listDirectoryFiles(directory):
        """ Get a list of files in a direcotry """
        return [ os.path.join(directory,f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory,f)) ]



    def moveLogFileToImported(self, logFile, compress=True):
        """ Move a file to the 'imported' folder with optional gzip compression. Returns new file path. """
        return self.moveFile(logFile, self.importedFolder, compress)

    def moveLogFileToUploaded(self, logFile, compress=True):
        """ Move a file to the 'uploaded' folder with optional gzip compression. Returns new file path. """
        return self.moveFile(logFile, self.uploadedFolder, compress)

    def moveLogFileToDownloaded(self, logFile, compress=True):
        """ Move a file to the 'downloaded' folder with optional gzip compression. Returns new file path. """
        return self.moveFile(logFile, self.downloadedFolder, compress)


    def moveFile(self, aFile, destFolder, compress=True):
        """
        Move a file to folder with optional gzip compression.

        @param aFile string - Path of file to move.
        @param destFolder string - Where to put the file. Directory must exist and be writable.
        @param compress bool - If true file is gzip compressed (if not already) before moving.

        @return string - new file path
        """
        import shutil

        dest = os.path.join(destFolder, os.path.basename(aFile))
        if compress and not self.isGZipped(aFile):
            src = self.gZipFile(aFile, keepOriginal=False)
            return self.moveFile(src, destFolder, False)
        else:
            shutil.move(aFile, dest)
            return dest
            


    def gZipFile(self, aFile, keepOriginal=True):
        """
        Compress a file using gzip.
        
        @param keepOriginal bool - If True, the original file is left in place,
            else it is removed.
        @return str - new gzip'ed file path
        """
        import gzip
        zFile = '%s.gz' % aFile
        f_in = open(aFile, 'rb')
        f_out = gzip.open(zFile, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        if not keepOriginal:
            os.remove(aFile)
        return zFile


    def isGZipped(self, aFile):
        """ Check a file to see if it ends int .gz """
        import re
        return (re.compile('\.gz$').search(aFile) is not None)


    @staticmethod
    def labelToUpperUnderscore(s):
        """
        Static helper method which formats a label as UPPER_CASE_UNDERSCORE_SEPERATED.

        @parm s str - A string. Unicode strings are encoded as utf-8

        @return string
        """

        regex = re.compile(' ')
        if type(s) == unicode:
            s = s.encode('utf-8')
        return regex.sub("_", s.upper())





class AS_WS_STATION_ABSTRACT(object):
    """Generic station details"""

    def __init__(self, wsApp, label, id, options):

        
        self.app = wsApp
        self.label = label
        self.id = id
        for option in options :
            self.__dict__[option] = options[option]


    def getLogFile(self): return self.app.getLogFile(self.id)
    def setLogFile(self, value): raise ValueError('AS_WS_STATION.logFile attribute is read-only')
    def delLogFile(self): raise ValueError('AS_WS_STATION.logFile attribute is read-only')
    logFile = property(getLogFile, setLogFile, delLogFile, None)


    def getTimestampFile(self): return self.app.getTimestampFile(self.id)
    def setTimestampFile(self): raise ValueError('AS_WS_STATION.timestampFile attribute is read-only')
    def delTimestampFile(self): raise ValueError('AS_WS_STATION.timestampFile attribute is read-only')
    timestampFile = property(getTimestampFile, setTimestampFile, delTimestampFile, None)

    @staticmethod
    def optionsSpec():

        # Specify options used by this station type
        # This is used by the config reader and creator to figure out
        # which options are needed and what type to expect.
        #
        # Key is option name.
        # Value is option type or list of types.
        # If option is optional, the set value to something like [None, int].
        options = OrderedDict()
        options['stype'] = str
        options['elevation'] = int

        return options



class AS_WS_STATION_PWS(AS_WS_STATION_ABSTRACT):

    @staticmethod
    def optionsSpec():

        from decimal import Decimal

        options = AS_WS_STATION_ABSTRACT.optionsSpec()
        options['interfaceKitID'] = int
        options['textLCDID'] = [None, int]
        options['intervalSensorSample'] = int
        options['intervalSensorLog'] = int
        options['sensorBP'] = int
        options['sensorInternalTemp'] = int
        options['sensorLoad'] = int
        options['sensorRH'] = int
        options['sensorTemp'] = int
        options['rainGaugeArea'] = Decimal
        options['rainGaugeVolume'] = Decimal
        options['inputRG'] = int
        options['remoteHost'] = [None, str]

        return options




class AS_WS_STATION_NETATMO_DEVICE(AS_WS_STATION_ABSTRACT):

    @staticmethod
    def optionsSpec():

        options = AS_WS_STATION_ABSTRACT.optionsSpec()
        options['deviceID'] = str

        return options



class AS_WS_STATION_NETATMO_MODULE(AS_WS_STATION_NETATMO_DEVICE):

    @staticmethod
    def optionsSpec():

        options = AS_WS_STATION_NETATMO_DEVICE.optionsSpec()
        options['deviceID'] = str
        options['moduleID'] = str

        return options



class AS_WS_STATION_NETATMO_MODULE_INDOOR(AS_WS_STATION_NETATMO_MODULE):
    pass

class AS_WS_STATION_NETATMO_MODULE_RAIN_GAUGE(AS_WS_STATION_NETATMO_MODULE):
    pass


# Station class lookup
STYPE_CLASS_LOOKUP = OrderedDict([
    (STYPE_PWS, AS_WS_STATION_PWS),
    (STYPE_NETATMO_DEVICE, AS_WS_STATION_NETATMO_DEVICE),
    (STYPE_NETATMO_MODULE, AS_WS_STATION_NETATMO_MODULE),
    (STYPE_NETATMO_MODULE_INDOOR, AS_WS_STATION_NETATMO_MODULE_INDOOR),
    (STYPE_NETATMO_MODULE_RAIN_GAUGE, AS_WS_STATION_NETATMO_MODULE_RAIN_GAUGE)
    ])




class AS_WS_SAMPLE(object):
    """Station details"""
    
    def __init__(self, dateTime, measurements={}):

        self.dateTime = dateTime
        self.measurements = {}


    def setMeasurement(self, m):
        if not isinstance(m, AS_WS_MEASUREMENT):
            raise ValueError('sample must be an instance of AS_WS_MEASUREMENT')
        self.measurements[m.mtype] = m


    def delMeasurement(self, mtype):
        self.measurements.pop[mtype, None]


    def getMeasurement(self, mtype):
        if mtype in self.measurements:
            return self.measurements[mtype]
        else:
            return None


    @staticmethod
    def createMeasurement(mtype, value=0):
        """ Static helper """
        if mtype == MEASURE_TEMPERATURE:
            return AS_WS_MEASUREMENT_TEMPERATURE(value)

        elif mtype == MEASURE_RELATIVE_HUMIDITY:
            return AS_WS_MEASUREMENT_RELATIVE_HUMIDITY(value)

        elif mtype == MEASURE_STATION_BAROMETRIC_PRESSURE:
            return AS_WS_MEASUREMENT_STATION_BAROMETRIC_PRESSURE(value)

        elif mtype == MEASURE_PRECIPITATION_WEIGHT:
            return AS_WS_MEASUREMENT_PRECIPITATION_WEIGHT(value)

        elif mtype == MEASURE_INTERNAL_TEMPERATURE:
            return AS_WS_MEASUREMENT_INTERNAL_TEMPERATURE(value)

        elif mtype == MEASURE_CO2:
            return AS_WS_MEASUREMENT_CO2(value)

        elif mtype == MEASURE_NOISE:
            return AS_WS_MEASUREMENT_NOISE(value)

        elif mtype == MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE:
            return AS_WS_MEASUREMENT_SEA_LEVEL_BAROMETRIC_PRESSURE(value)

        elif mtype == MEASURE_PRECIPITATION:
            return AS_WS_MEASUREMENT_PRECIPITATION(value)

        else:
            return AS_WS_MEASUREMENT(MEASURE_ABSTRACT, value)




class AS_WS_MEASUREMENT(object):
    """Abstract Measurement Class"""
    
    def __init__(self, mtype=MEASURE_ABSTRACT, value=0, unit='', dtype='numeric', labelLong='', labelShort=''):

        self.mtype = mtype
        self.dtype = dtype
        self.unit = unit
        self.setValue(value)
        self.labelLong = labelLong
        self.labelShort = labelShort


    def setValue(self, value):

        if type(value) == str:
            try:
                # casting '1.23' to int throws an error
                v = int(value)
            except ValueError:
                from decimal import Decimal
                v = Decimal(value)
        else:
                v = value
        self.__value = v;
        return self.value


    def getValue(self):
        return self.__value

    
    def delValue(self):
        return self.setValue(0)


    def getString(self, r=2):
        v = self.getValue()
        if r > -1:
            try:
                v = round(v, r)
            except TypeError as e:
                pass
        return str(v)


    def getFormattedString(self, r=2):
        return "%s %s" % (self.getString(r), self.unit)
        
    value = property(getValue, setValue, delValue, None)



class AS_WS_MEASUREMENT_TEMPERATURE(AS_WS_MEASUREMENT):
    
    def __init__(self, value):
        super(AS_WS_MEASUREMENT_TEMPERATURE, self).__init__(
            mtype = MEASURE_TEMPERATURE,
            value = value,
            unit = '°C',
            labelLong = 'Temperature',
            labelShort = 'Temp'
            )


class AS_WS_MEASUREMENT_INTERNAL_TEMPERATURE(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_INTERNAL_TEMPERATURE, self).__init__(
            mtype = MEASURE_INTERNAL_TEMPERATURE,
            value = value,
            unit = '°C',
            labelLong = 'Internal Temperature',
            labelShort = 'Int Temp'
            )


class AS_WS_MEASUREMENT_RELATIVE_HUMIDITY(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_RELATIVE_HUMIDITY, self).__init__(
            mtype = MEASURE_RELATIVE_HUMIDITY,
            value = value,
            unit = '%',
            labelLong = 'Relative Humidity',
            labelShort = 'RH'
            )



class AS_WS_MEASUREMENT_STATION_BAROMETRIC_PRESSURE(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_STATION_BAROMETRIC_PRESSURE, self).__init__(
            mtype = MEASURE_STATION_BAROMETRIC_PRESSURE,
            value = value,
            unit = 'hPa',
            labelLong = 'Station Pressure',
            labelShort = 'SBP'
            )

    def getStationPressure(self):
        return self.value

    def getSeaLevelPressure(self, altitude, temp):
        # see http://keisan.casio.com/has10/SpecExec.cgi?id=system/2006/1224575267
        return self.value * (1-((0.0065*altitude)/(temp+0.0065*altitude+273.15)))**-5.257


class AS_WS_MEASUREMENT_SEA_LEVEL_BAROMETRIC_PRESSURE(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_SEA_LEVEL_BAROMETRIC_PRESSURE, self).__init__(
            mtype = MEASURE_SEA_LEVEL_BAROMETRIC_PRESSURE,
            value = value,
            unit = 'hPa',
            labelLong = 'Sea-level Pressure',
            labelShort = 'SLBP'
            )

    def getStationPressure(self, altitude, temp):
        # see http://keisan.casio.com/exec/system/1224562962
        # Convert station temp to sea-level temp
        return self.value / (1-((0.0065*altitude)/(temp+.0065*altitude+273.15)))**-5.257

    def getSeaLevelPressure(self):
        return self.value


class AS_WS_MEASUREMENT_PRECIPITATION_WEIGHT(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_PRECIPITATION_WEIGHT, self).__init__(
            mtype = MEASURE_PRECIPITATION_WEIGHT,
            value = value,
            unit = 'g',
            labelLong = 'Precipitation Weight',
            labelShort = 'Precip Mass'
            )


class AS_WS_MEASUREMENT_CO2(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_CO2, self).__init__(
            mtype = MEASURE_CO2,
            value = value,
            unit = 'ppm',
            labelLong = 'CO2',
            labelShort = 'CO2'
            )


class AS_WS_MEASUREMENT_NOISE(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_NOISE, self).__init__(
            mtype = MEASURE_NOISE,
            value = value,
            unit = 'dB',
            labelLong = 'Noise',
            labelShort = 'Noise'
            )


class AS_WS_MEASUREMENT_PRECIPITATION(AS_WS_MEASUREMENT):

    def __init__(self, value):
        super(AS_WS_MEASUREMENT_PRECIPITATION, self).__init__(
            mtype = MEASURE_PRECIPITATION,
            value = value,
            unit = 'mm',
            labelLong = 'Precipitation',
            labelShort = 'Precip'
            )



class AS_DB_CONNECT(object):
    """Store of database connection info"""
    
    def __init__(self, host, user, passwd, db):

        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db


def interogate(obj):
    """ Debug the properties and methods of an object """
    l = dir(obj)
    d = obj.__dict__

    from pprint import pprint
    pprint(l)
    pprint(d, indent=2)



""" debugging """
if __name__ == "__main__":
    foo = AS_WS_MEASUREMENT_NOISE(20)

    print 'mtype',foo.mtype
    print 'value',foo.value
    print 'unit',foo.unit
    print 'dtype',foo.dtype

    foo = AS_WS_MEASUREMENT_STATION_BAROMETRIC_PRESSURE(889)
    print 'station',foo.getStationPressure()
    print 'sea level',foo.getSeaLevelPressure(1060, 15)

    foo = AS_WS_MEASUREMENT_SEA_LEVEL_BAROMETRIC_PRESSURE(1006.58520566)
    print 'station',foo.getStationPressure(1060, 15)
    print 'sea level',foo.getSeaLevelPressure()


    app = AS_WS_APP()

    interogate(app)

    print app.stations[STATION_HOME_INDOOR].logFile
    print app.stations[STATION_HOME_INDOOR].timestampFile
