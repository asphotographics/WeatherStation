#! /usr/bin/python
# coding: utf-8

import as_weatherstation.app as ws_app

class AS_PWS_APP(ws_app.AS_WS_APP):
	"""Configuration settings for NMeasureArchive-PY App"""

	def __init__(self):

		super(AS_PWS_APP, self).__init__()

		#self.netatmoClientID = self._config.get('netatmo', 'clientID')





""" Instance of AS_PWS_APP for use in the program """
app = AS_PWS_APP()





""" DEBUG """
def debug():

	from pprint import pprint

	ws_app.interogate(app.db[ws_app.DB_MAIN])

	pprint(app.stations['STATION_BAYMAR_OUTDOOR'].__dict__)



if __name__ == "__main__": debug()
#else : debug()

