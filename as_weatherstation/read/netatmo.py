import as_weatherstation.app as mod_ws_app

import as_weatherstation.read.abstract as mod_ws_read_abstract


class AS_WS_READER_NETATMO(mod_ws_read_abstract.AS_WS_READER):
    """ Netamo reader """
    def __init__(self, wsApp):

        super(AS_WS_READER_NETATMO, self).__init__(wsApp)

        import as_weatherstation.netatmo.lnetatmo as lnetatmo
        self.lnetatmo = lnetatmo

        self.lnetatmo._CLIENT_ID = self.app.netatmoClientID
        self.lnetatmo._CLIENT_SECRET = self.app.netatmoClientSecret
        self.lnetatmo._USERNAME = self.app.netatmoUsername
        self.lnetatmo._PASSWORD = self.app.netatmoPassword

        # Authenticate
        self.authorization = lnetatmo.ClientAuth(
            self.app.netatmoClientID,
            self.app.netatmoClientSecret,
            self.app.netatmoUsername,
            self.app.netatmoPassword
            )
        # Get device list
        self.deviceList = lnetatmo.DeviceList(self.authorization)


    def read(self, params):

        import time


        # What type of device/module are we dealing with?
        stype = params['station'].stype


        # Get a list of supported measurement types for the given device/module
        if not 'mtypeList' in params:
            # Define a list of measurement types to get...
            if params['moduleID']:
                # ...for a module
                params['mtypeList'] = self.deviceList.modules[params['moduleID']]['data_type']
            else:
                # ...for the main device
                params['mtypeList'] = self.deviceList.stations[params['deviceID']]['data_type']


        # Map the Netamo measurement types to our types
        fm = self.app.fieldMap # alias the maps in app config
        fields = {} # dict map of fields that getMeasure is going to return
        mtypeList = [] # ordered list of Netatmo measurement types we will pass to getMeasure 
        # (results will come back in this order)
        for field in fm['log']:
            if fm[stype][field] == None:
                continue
            elif not fm[stype][field] in params['mtypeList']:
                continue
            else:
                # We are only going to get the measurements we support,
                # regardless of what the device/module supports.
                mtypeList.append(fm[stype][field])
                fields[field] = len(mtypeList)-1 # "pointer" to the field in the result list


        # Read the measurements from the Netatmo API
        self.rawData = self.deviceList.getMeasure(
            params['deviceID'],
            params['scale'],
            ','.join(mtypeList),
            params['moduleID'],
            params['beginTime'],
            params['endTime'],
            params['limit'],
            False
            )


        # If status is not ok then bail.
        if not (self.rawData['status'] == 'ok'):
            return self.samples


        # If there were no measurements returned (usually do to a begin/end time limitation)
        # then return nothing. You can differentiate an empty set from an error
        # by checking self.rawData['status']
        if len(self.rawData['body']) == 0:
            return self.samples


        # Map Netatmo measurements to our measurement objects
        #
        # (Because 'body' is a dictionary, the items can be out of
        # chronological order.)
        sampleKeys = self.rawData['body'].keys()
        sampleKeys.sort()
        fm = self.app.fieldMap # alias the maps in app config
        for t in sampleKeys:
            sampleTime = time.localtime(float(t))
            sample = mod_ws_app.AS_WS_SAMPLE(sampleTime)
            for field in fields:
                value = self.rawData['body'][t][fields[field]]
                # Occasionally a measurement gets missed, in which case the
                # Netatmo API returns a value of None.
                if value == None: value = 0
                #print "%s %d %s %f" % (str(stype), int(field), str(fm[stype][field]), float(value))
                measure = mod_ws_app.AS_WS_SAMPLE.createMeasurement(field, value)
                sample.setMeasurement(measure)
            self.samples.append(sample)

        return self.samples

