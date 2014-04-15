import as_weatherstation.app as mod_ws_app
import as_weatherstation.read.csvfile as mod_ws_read_csvfile


class AS_WS_READER_LOG(mod_ws_read_csvfile.AS_WS_READER_CSVFILE):
    """ Log file reader """


    def __init__(self, wsApp, sLabel=None):

        super(AS_WS_READER_LOG, self).__init__(wsApp)

        # No station specified so try to find one in the station list.
        # There must be one station, and only one, configured
        # for this to work, otherwise we will throw an error.
        if sLabel == None:
            for label in wsApp.stations:
                if not sLabel is None:
                    raise ValueError('Multiple weather stations configured. Please manually specify which configuration to use.')
                sLabel = label

        if sLabel is None:
            raise ValueError('No stations found in configuration.')
            
        self.station = self.app.stations[sLabel]


        # Figure out which sensor and inputs to read from
        """
        fm = self.app.fieldMap[mod_ws_app.STYPE_PWS]
        self.sensors = {}
        self.inputs = {}
        for field in fm:
            if fm[field] is None:
                continue
            if fm[field][0] == mod_ws_app.PWS_IO_SENSOR:
                self.sensors[field] = getattr(self.station, fm[field][1])
            elif fm[field][0] == mod_ws_app.PWS_IO_INPUT:
                self.inputs[field] = getattr(self.station, fm[field][1])
        """




    def read(self, log=None, lines=0):

        """ Read the station log file """

        if log is None:
            log = self.station.logFile

        return super(AS_WS_READER_LOG, self).read(log, lines)



    def parseCSVLine(self, line):
        """ Override the parent's method  """
    
        from time import strptime

        fm = self.app.fieldMap['log']

        sample = mod_ws_app.AS_WS_SAMPLE(strptime(line[0], "%Y-%m-%d %H:%M:%S"))
        for i in range(1, len(line)):
            mtype = fm[i-1]
            measurement = mod_ws_app.AS_WS_SAMPLE.createMeasurement(mtype, line[i])
            sample.setMeasurement(measurement)

        return sample



    def aggregateMeasurements(self, mtype, measurements):

        # For digital inputs the aggregate is the sum of the value sampled
        # (that is, the events are additive).
        if mtype in self.inputs:
            return sum(measurements)
        else:
            return super(AS_WS_READER_PWS, self).aggregateMeasurements(mtype, measurements)



