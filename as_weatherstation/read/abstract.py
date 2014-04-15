import as_weatherstation.app as mod_ws_app

class AS_WS_READER(object):
	""" Abstract reader class """

	def __init__(self, wsApp):
		self.app = wsApp
		self.samples = []
		self.rawDdata = None



	def read(self, params):
		"""
		Read some samples from somewhere (this abstract version
		does nothing -- child classes will override this method)
		"""
		pass



	def resetSamples(self):
		""" Reset the samples list """
		self.samples = []



	def flushSamples(self):
		""" Empty and return the samples list """

		s = []

		# At the end of this while loop self.samples will be empty.
		# However, in a threaded or event driven environment
		# it may not be empty when the return happens. The only way
		# to prevent this is to stop all threads and remove
		# all event listeners prior to calling flushSamples()
		while len(self.samples) > 0:
			s.append(self.samples.pop(0))

		return s



	def aggregateSamples(self, samples = None):
		""" Aggregate the values of a sample list down to a single sample """

		if samples == None:
			samples = self.samples

		measurements = {}
		for sample in samples:
			sampleTime = sample.dateTime # keep only the last time (this assumes the samples are in order, which they should be)
			for mtype in sample.measurements:
				if not mtype in measurements:
					measurements[mtype] = []
				measurements[mtype].append(sample.measurements[mtype].value)


		aSample = mod_ws_app.AS_WS_SAMPLE(sampleTime)
		for mtype in measurements:

			value = self.aggregateMeasurements(mtype, measurements[mtype])
			"""
			total = sum(measurements[mtype])
			count = len(measurements[mtype])
			average = total/count
			print "%d: %f / %d = %f | %f" % (mtype, total, count, average, value)
			"""
			measure = mod_ws_app.AS_WS_SAMPLE.createMeasurement(mtype, value)
			aSample.setMeasurement(measure)

		return [aSample]



	def aggregateMeasurements(self, mtype, measurements):
		"""
		The default aggregate method calculates the average for a given measurement.
		Child classes can override this method to provie other functionality.
		"""
		return sum(measurements)/len(measurements)
