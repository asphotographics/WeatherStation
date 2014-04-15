#! /usr/bin/python
# coding: utf-8


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
STYPE_NETATMO_DEVICE = 'STYPE_NETATMO_DEVICE'
STYPE_NETATMO_MODULE = 'STYPE_NETATMO_MODULE'
STYPE_PWS = 'STYPE_PWS'


# Phidget Weather Station IO type constants
PWS_IO_SENSOR = 0
PWS_IO_INPUT = 1
PWS_IO_OUTPUT = 2


# Bitwise logfile types
LOGFILE_CURRENT = 1 # the file that is currently being logged to
LOGFILE_BACKUP = 2 # backup files created by log rotate (have ".[datatime]" appended, possibly GZIPed)
LOGFILE_IMPORTED = 4 # file that has already been imported into the DB (GZIPed)
LOGFILE_ALL = 7 # All -- update this if adding new types


DB_MAIN = 1 # main database

class AS_WS_APP(object):
    """Configuration settings for weather station app"""

    def __init__(self):

        import socket
        self.hostname = socket.gethostname()

        import config.app as mod_config_app
        self._config = mod_config_app.getConfig()


        # Log file location
        self._setDataFolder(self._config.get('app', 'dataFolder'))
        self.importedPrefix = "log.imported"


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
        self.stations = {}
        sList = self._config.options('stations')
        for sLabel in sList :

            sID = self._config.getint('stations', sLabel)
            sSection = "station%d" % sID
            sOptions = self._config.options(sSection)
            params = {}

            for o in sOptions :
                # Because station options are quite dynamic, we have a helper
                # convert the values to the proper types for us.
                params[o] = mod_config_app.getStationOption(self._config, sSection, o)

            self.stations[sLabel] = AS_WS_STATION(
                self,
                sLabel,
                sID,
                params
                )


        self.db = {}
        # if a database connection is defined specific to the current host, use it
        # This is more for development than anything else, so you can have a
        # seperate database config for your development environment versus production.
        dbSection = "database_main_%s" % self.hostname.lower()
        if not self._config.has_section(dbSection): dbSection = 'database_main'
        self.db[DB_MAIN] = AS_DB_CONNECT(
            self._config.get(dbSection, 'host'),
            self._config.get(dbSection, 'user'),
            self._config.get(dbSection, 'password'),
            self._config.get(dbSection, 'database')
            )



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
        self.dataFolder = folder
        self.logFolder = self.dataFolder + "log/"
        self.importedFolder = self.logFolder + "imported/"
        self.errorFile = self.dataFolder + "error.txt"

        self.logFileName = "log_station_%d.txt"

        self.logFile = self.logFolder + self.logFileName
        self.timestampFile = self.logFolder + "latest_station_%d.txt"

        self.importedFolder = self.logFolder + "imported/"


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

        from os import listdir
        from os.path import isfile, join
        import re

        files = {}

        datePattern = '(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})'

        if lftype & LOGFILE_CURRENT:

            files[LOGFILE_CURRENT] = []
            f = self.getLogFile(stationID)
            if isfile(f):
                files[LOGFILE_CURRENT].append(f)


        if lftype & LOGFILE_BACKUP:

            files[LOGFILE_BACKUP] = []
            allFiles = AS_WS_APP.listDirectoryFiles(self.logFolder)
            regex = re.compile(re.escape('%s.'%self.getLogFile(stationID)) + datePattern)
            for f in allFiles:
                if not regex.match(f) is None:
                    files[LOGFILE_BACKUP].append(f)


        if lftype & LOGFILE_IMPORTED:

            files[LOGFILE_IMPORTED] = []
            allFiles = AS_WS_APP.listDirectoryFiles(self.importedFolder)
            regex = re.compile(re.escape('%s%s.'%(self.importedFolder, self.getLogFileName(stationID))) + datePattern)
            for f in allFiles:
                if not regex.match(f) is None:
                    files[LOGFILE_IMPORTED].append(f)


        return files



    @staticmethod
    def listDirectoryFiles(directory):
        """ Get a list of files in a direcotry """
        from os import listdir
        from os.path import isfile, join
        return [ join(directory,f) for f in listdir(directory) if isfile(join(directory,f)) ]



    def moveLogFileToImported(self, logFile, compress=True):
        """ Move a file to the 'imported' folder with optional gzip compression. Returns new file path. """
        import shutil, os, re

        dest = '%s%s' % (self.importedFolder, os.path.basename(logFile))
        if compress and not re.compile('\.gz$').findall(logFile):
            src = self.gZipFile(logFile)
            os.remove(logFile)
            return self.moveLogFileToImported(src, False)
        else:
            shutil.move(logFile, dest)
            return dest
            


    def gZipFile(self, aFile):
        """ Compress a file using gzip. The original file is left in place. Returns gzip file path. """
        import gzip
        zFile = '%s.gz' % aFile
        f_in = open(aFile, 'rb')
        f_out = gzip.open(zFile, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        return zFile




class AS_WS_STATION(object):
    """Generic station details"""
    
    def __init__(self, wsApp, label, id, params):

        self.app = wsApp
        self.label = label
        self.id = id
        for param in params :
            self.__dict__[param] = params[param]


    def getLogFile(self): return self.app.getLogFile(self.id)
    def setLogFile(self, value): raise ValueError('AS_WS_STATION.logFile attribute is read-only')
    def delLogFile(self): raise ValueError('AS_WS_STATION.logFile attribute is read-only')
    logFile = property(getLogFile, setLogFile, delLogFile, None)


    def getTimestampFile(self): return self.app.getTimestampFile(self.id)
    def setTimestampFile(self): raise ValueError('AS_WS_STATION.timestampFile attribute is read-only')
    def delTimestampFile(self): raise ValueError('AS_WS_STATION.timestampFile attribute is read-only')
    timestampFile = property(getTimestampFile, setTimestampFile, delTimestampFile, None)







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
