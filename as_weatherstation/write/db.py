import logging

import as_weatherstation.app as mod_ws_app
from as_weatherstation.log import dbhandler as mod_ws_log_dbhandler
import as_weatherstation.write.abstract as mod_ws_write_abstract

class AS_WS_WRITER_DB(mod_ws_write_abstract.AS_WS_WRITER):
    """ Write samples to a text log """

    def __init__(self, wsApp, slabel):

        super(AS_WS_WRITER_DB, self).__init__(wsApp)

        self.slabel = slabel

        #self.dbhandler = mod_ws_log_dbhandler.DBHandler(self.app)

        # Configured in as_weatherstation/config/log.py
        self.db_logger = logging.getLogger(__name__)
        #elf.db_logger.setLevel(logging.INFO)
        #elf.db_logger.addHandler(self.dbhandler)



    def write(self, samples):

        # Loop through the samples list and log the measurements
        for s in samples:
            # Write measurements via logger
            self.db_logger.info('', extra={'stationID': self.app.stations[self.slabel].id, 'sample': s})
