import as_weatherstation.app as mod_ws_app

from as_weatherstation.log import error as mod_ws_log_error
from as_weatherstation.log import weather as mod_ws_log_weather
from as_weatherstation.log import timestamp as mod_ws_log_timestamp

import as_weatherstation.write.abstract as mod_ws_write_abstract

class AS_WS_WRITER_LOG(mod_ws_write_abstract.AS_WS_WRITER):
    """ Write samples to a text log """

    def __init__(self, wsApp, log_logger, timestamp_logger=None):
        super(AS_WS_WRITER_LOG, self).__init__(wsApp)
        self.log_logger = log_logger
        self.timestamp_logger = timestamp_logger


    def write(self, samples):

        # Loop through the samples list and log the measurements
        for s in samples:
            sampleTime = s.dateTime
            row = [sampleTime]
            for field in self.app.fieldMap['log']: # fm['log'] has to be a list (a dictionary could be in any order)
                measurement = s.getMeasurement(field)
                if not measurement is None:
                    # Even though the DB stores integers for all fields
                    # we will store higher precision floats in the log
                    # if given.
                    row.append(measurement.getString())
                else :
                    row.append('0')

            #print row

            # Write measurements to log
            self.log_logger.info(mod_ws_log_weather.getLogString(row))

        # Close the log file so other process can use it
        #self.log_logger.handlers[0].stream.close()
        #self.log_logger.handlers[0].stream = None


        # Write timestamp to log so we know the last time archiver ran
        if not self.timestamp_logger is None:

            self.timestamp_logger.info(mod_ws_log_timestamp.getLogString([sampleTime]))

            # Close the timestamp file so other processes can use it
            #self.timestamp_logger.handlers[0].stream.close()
            #self.timestamp_logger.handlers[0].stream = None

