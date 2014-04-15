#!/usr/bin/env python
#
# Copyright 2001-2004 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# This file is part of the standalone Python logging distribution. See
# http://www.red-dove.com/python_logging.html
#
"""
    A test harness for the logging module. An example handler - DBHandler -
    which writes to an Python DB API 2.0 data source. You'll need to set this
    source up before you run the test.
    
    Copyright (C) 2001-2004 Vinay Sajip. All Rights Reserved.
    """
import sys, string, time, logging
import as_weatherstation.app as mod_ws_app

class DBHandler(logging.Handler):
    def __init__(self, wsApp=None):
        
        logging.Handler.__init__(self)

        self.setApp(wsApp)
        self.host = ''
        self.user = ''
        self.password = ''
        self.database = ''


    def setApp(self, wsApp):

        self.app = wsApp

        if self.app is None:
            return

        import MySQLdb

        self.host = self.app.db[mod_ws_app.DB_MAIN].host
        self.user = self.app.db[mod_ws_app.DB_MAIN].user
        self.password = self.app.db[mod_ws_app.DB_MAIN].passwd
        self.database = self.app.db[mod_ws_app.DB_MAIN].db

        self.conn = MySQLdb.connect(self.host, self.user, self.password, self.database)
        self.cursor = self.conn.cursor()
       
        # Get the names of the measurement fields from the app
        # and dynamically build the SQL formatter.
        cols = []
        vals = []
        for field in self.app.fieldMap['db']:
            cols.append(self.app.fieldMap['db'][field])
            vals.append('"%%(%s)s"' % self.app.fieldMap['db'][field])

        self.SQL = """INSERT IGNORE INTO as_pws_data_log (
            fStationID,
            fSampleDateTime,
            %s
            )
            VALUES (
            "%%(stationID)d",
            "%%(dbtime)s",
            %s
            );
            """ % (",\n".join(cols), ",\n".join(vals))

        
    
    
    def formatDBTime(self, record):
        record.dbtime = time.strftime("%Y-%m-%d %H:%M:%S", record.sample.dateTime)
    
    def emit(self, record):
        try:
            #use default formatting -- this doesn't do much except format the message, which we don't use
            self.format(record)

            # move the sample measurement key/values into the record
            for field in self.app.fieldMap['db']:
                measurement = record.sample.getMeasurement(field)
                if not measurement is None:
                    record.__dict__[self.app.fieldMap['db'][field]] = measurement.getString()
                else :
                    record.__dict__[self.app.fieldMap['db'][field]] = '0'

            #now set the database time up
            self.formatDBTime(record)
            if record.exc_info:
                record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
            else:
                record.exc_text = ""
            sql = self.SQL % record.__dict__
            self.cursor.execute(sql)
            self.conn.commit()
        except:
            import traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei
    
    def close(self):
        if hasattr(self, 'cursor'):
            self.cursor.close()
            self.conn.close()
        logging.Handler.close(self)

