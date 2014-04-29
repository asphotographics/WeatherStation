#!/usr/bin/python
# encoding=utf-8

from collections import OrderedDict
import re
import ConfigParser 

import as_weatherstation.app as mod_ws_app
import as_weatherstation.read.netatmo as mod_ws_read_netatmo

class AS_NWS_APP(mod_ws_app.AS_WS_APP):
    """Configuration settings for NMeasureArchive-PY App"""

    def __init__(self):

        super(AS_NWS_APP, self).__init__()

        """
        Each time the script runs it picks up where it left off last time
        (i.e., as indicated by timestampFile contents).

        In the event that there is no timestampFile it will try to get the
        last sample time from AS_NMA_STATION.logFile

        As a last resort, the script will start archiving from
        oldestTimestamp. It should only do this on first run though.

        However since the Netatmo API returns a max of 1024 records
        per call it may take some time to get all data going back to
        oldestTimestamp.

        1024 samples per call
        --------------------- = 3.56 days worth of samples/per call
         288 samples per day 

        ...if the Netatmo device samples every 5 minutes
        """
        self.oldestTimestamp = self._config.get('netatmo', 'oldestTimestamp')

        """
        Netatmo api credentials
        """
        self.netatmoClientID = self._config.get('netatmo', 'clientID')
        self.netatmoClientSecret = self._config.get('netatmo', 'clientSecret')
        self.netatmoUsername = self._config.get('netatmo', 'username')
        self.netatmoPassword = self._config.get('netatmo', 'password')



    def listNetatmoAPIStations(self):
        """
        @brief Create a list of new and exisiting stations based on the devices/modules
        returned by the Netatmo API.

        This can be used to list devices/modules associated with the Netatmo
        account, so you can, for example, add them to the app.cfg file.

        For each device/module we create a station label like
        "STATION_[station_name]_[module_name]". If that label matches an exisiting
        station then we associate it with the existing ID. Otherwise, the station
        objects id attibute will be None.

        If is important to note that we are not using these stations in anyway. We are
        just listing them, and you have to decide what to do with them.

        @return OrderedDict - Dictionary of AS_WS_STATION_NETATMO_* objects keyed on
            the station label
        """

        # Get the Netatmo API reader object
        reader = mod_ws_read_netatmo.AS_WS_READER_NETATMO(self)

        from pprint import pprint

        #pprint(reader.deviceList.stations)
        #pprint(reader.deviceList.modules)

        s = reader.deviceList.stations
        m = reader.deviceList.modules

        # Loop through the devices and modules and create stations
        stations = OrderedDict()
        for dID in s:

            # We might not know about this kind of device (might be a thermostat)
            if not s[dID]['type'] in mod_ws_app.NETATMO_STYPE_LOOKUP:
                continue

            # Get general info about this installation
            deviceID = dID.encode('utf-8')
            elevation = s[dID]['place']['altitude']
            stationName = 'STATION_%s' % self.labelToUpperUnderscore(s[dID]['station_name'])

            # Make label for this device
            sLabel = '%s_%s' % (stationName, self.labelToUpperUnderscore(s[dID]['module_name']))

            # See if this label has already been assigned an ID
            try:
                sID = self._config.getint('stations', sLabel)
            except ConfigParser.NoOptionError as e:
                sID = None

            # Add device info to station options
            options = {}
            options['stype'] = mod_ws_app.NETATMO_STYPE_LOOKUP[s[dID]['type']] 
            options['deviceID'] = deviceID
            options['elevation'] = elevation
            
            # Create an object of the appropriate class for this device    
            sclass = mod_ws_app.STYPE_CLASS_LOOKUP[options['stype']]
            stations[sLabel] = sclass(
                self,
                sLabel,
                sID,
                options
                )


            # Loop through the modules of this device and add them as stations
            for mID in s[dID]['modules']:

                # Make label for this module
                sLabel = '%s_%s' % (stationName, self.labelToUpperUnderscore(m[mID]['module_name']))

                # See if this label has already been assigned an ID
                try:
                    sID = self._config.getint('stations', sLabel)
                except  ConfigParser.NoOptionError as e:
                    sID = None

                # Add module info to station options
                options = {}
                options['stype'] = mod_ws_app.NETATMO_STYPE_LOOKUP[m[mID]['type']]
                options['deviceID'] = deviceID
                options['moduleID'] = mID.encode('utf-8')
                options['elevation'] = elevation

                # Create an object of the appropriate class for this device    
                sclass = mod_ws_app.STYPE_CLASS_LOOKUP[options['stype']]
                stations[sLabel] = sclass(
                    self,
                    sLabel,
                    sID,
                    options
                    )

        return stations






""" DEBUG """
def debug():

    from pprint import pprint
    
    app = AS_NWS_APP()

    mod_ws_app.interogate(app.db[mod_ws_app.DB_MAIN])

    pprint(app.stations)

    print app.oldestTimestamp

    print app.stations['STATION_HOME_INDOOR'].logFile
    print app.stations['STATION_HOME_INDOOR'].timestampFile



if __name__ == "__main__": debug()
#else : debug()

