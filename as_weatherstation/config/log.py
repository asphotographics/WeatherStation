#! /usr/bin/python

def config(errorFile, params):
    """ Helper to parse logging configuration """
    """ errorFile str - Path to log file """
    """ params dict - configuration parameters """
    """   stations dict - keys are stationIDs, values are instances of as_nma.config.app.AS_NMA_STATION """

    """ A seperate log logger and timestamp logger will be created for each station """
    """ Get the loggers with the log.weather, log.timestamp, and log.error modules' getLogger() functions """

    if not 'wsApp' in params:
        params['wsApp'] = None

    import logging
    import logging.config
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'message': {
                'format': '%(message)s',
                },
            'simple': {
                'format': '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                },
            'brief': {
                'format': '%(name)s - $(filename)s (%(lineno)d) - %(levelname)s - %(message)s',
                }
            },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
                },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'simple',
                'filename': errorFile,
                'maxBytes': 1024*1024,
                'backupCount': 10,
                'delay': True
                },
            'dbhandler': {
                'class': 'as_weatherstation.log.dbhandler.DBHandler',
                'formatter': 'message',
                'level': 'INFO',
                'wsApp': params['wsApp']
                },
            },
        'loggers': {
            'as_weatherstation.log.error': {
                'level': 'WARN',
                'handlers': ['error_file'],
                'propagate': False
                },
            'as_weatherstation.write.db': {
                'level': 'INFO',
                'handlers': ['dbhandler'],
                'propagate': False
                }
            },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console']
            }
        }


    if 'stations' in params:
        for sLabel in params['stations']:

            sID = params['stations'][sLabel].id
            logHandlerID = ('weather_log_file_%d' % sID)
            timestampHandlerID = ('weather_timestamp_file_%d' % sID)
            logLoggerID = getStationLogLoggerID(sID)
            timestampLoggerID = getStationTimestampLoggerID(sID)

            # Add some handlers
            config['handlers'][logHandlerID] = {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': 'INFO',
                'formatter': 'message',
                'filename': params['stations'][sLabel].logFile,
                'when': 'S', # use seconds so we can have nice timestamp on backup files
                'interval': 24*60*60, # every day
                'backupCount': 1000000000000, # One-trillion. Essentially unlimited. You will run out of diskspace if you don't archive backups.
                'encoding': None,
                'delay': True,
                'utc': False
                }
            config['handlers'][timestampHandlerID] = {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'message',
                'filename': params['stations'][sLabel].timestampFile,
                'mode': 'w', # every time we write we create a new file
                'encoding': None,
                'delay': True
                }

            # Add some loggers
            config['loggers'][logLoggerID] = {
                'level': 'DEBUG',
                'handlers': [logHandlerID],
                'propagate': False
                }
            config['loggers'][timestampLoggerID] = {
                'level': 'DEBUG',
                'handlers': [timestampHandlerID],
                'propagate': False
                }

            # save names of station loggers
            params['stations'][sLabel].logLoggerID = logLoggerID
            params['stations'][sLabel].timestampLoggerID = timestampLoggerID


    logging.config.dictConfig(config)



def getStationLogLoggerID(sID):
    
    return ('as_ws.log.weather_%d' % sID)



def getStationTimestampLoggerID(sID):
    return ('as_ws.log.timestamp_%d' % sID)

