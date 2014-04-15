#! /usr/bin/python
# coding: utf-8

import as_weatherstation.app as ws_app

class AS_NWS_APP(ws_app.AS_WS_APP):
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





""" Instance of AS_NWS_APP for use in the program """
app = AS_NWS_APP()





""" DEBUG """
def debug():

	from pprint import pprint

	ws_app.interogate(app.db[ws_app.DB_MAIN])

	pprint(app.stations)

	print app.oldestTimestamp

	print app.stations['STATION_HOME_INDOOR'].logFile
	print app.stations['STATION_HOME_INDOOR'].timestampFile



if __name__ == "__main__": debug()
#else : debug()

