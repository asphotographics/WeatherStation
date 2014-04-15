import as_weatherstation.app as mod_ws_app

class AS_WS_WRITER(object):
	""" Abstract reader class """

	def __init__(self, wsApp):
		self.app = wsApp

	def write(self, params):
		pass

