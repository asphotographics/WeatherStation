import as_weatherstation.app as mod_ws_app
import as_weatherstation.read.abstract as mod_ws_read_abstract

#Phidget specific imports
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, InputChangeEventArgs, OutputChangeEventArgs, SensorChangeEventArgs
from Phidgets.Devices.InterfaceKit import InterfaceKit

from as_weatherstation.phidget import lphidget as mod_lphidget


class AS_WS_READER_PWS(mod_ws_read_abstract.AS_WS_READER):
	""" Phidget Weather Station reader """

	def __init__(self, wsApp, sLabel=None, onInputChangeHandler=None):

		super(AS_WS_READER_PWS, self).__init__(wsApp)


		# No PWS specified so try to find one in the station list.
		# There must be one PWS, and only one PWS, configured
		# for this to work, otherwise we will throw an error.
		if sLabel == None:
			for label in wsApp.stations:
				if wsApp.stations[label].stype == mod_ws_app.STYPE_PWS:
					if not sLabel is None:
						raise ValueError('Multiple Phidget Weather Stations configured. Please manually specify which configuration to use.')
					sLabel = label

		if sLabel is None:
			raise ValueError('No Phidget Weather Station found in configured station list.')
			
		self.station = self.app.stations[sLabel]


		# Figure out which sensor and inputs to read from
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


		if onInputChangeHandler is None:
			onInputChangeHandler = getattr(self, 'onInputChangeHandler')

		# Connect the IFK
		if 'remoteHost' in self.station.__dict__:
			self.phidgetIFK = mod_lphidget.PHIDGET_IFK(
				self.station.interfaceKitID,
				remoteHost=self.station.remoteHost,
				onInputChangeHandler=onInputChangeHandler
				)
		else:
			self.phidgetIFK = mod_lphidget.PHIDGET_IFK(
				self.station.interfaceKitID,
				onInputChangeHandler=onInputChangeHandler
				)
		


	def read(self):

		import time

		# Sample the sensors
		sampleTime = time.localtime()
		sample = mod_ws_app.AS_WS_SAMPLE(sampleTime)
		for field in self.sensors:

			if field == mod_ws_app.MEASURE_STATION_BAROMETRIC_PRESSURE:
				method = 'getSensorRawValue'
			else:
				method = 'getSensorValue'

			sensorFunc = getattr(self.phidgetIFK.interfaceKit, method)
			value = self.convertSensorValue(sensorFunc(self.sensors[field]), field)

			#print "%d %d" % (field, value)
			measure = mod_ws_app.AS_WS_SAMPLE.createMeasurement(field, value)
			sample.setMeasurement(measure)

		# Add the sample
		self.samples.append(sample)

		return self.samples



	def onInputChangeHandler(self, index, state, event):

		import time

		match = False
		for mtype in self.inputs:
			if self.inputs[mtype] == index:
				match = mtype
				break

		#print "%s %d %s" % (match, index, state)
		if match == False: return

		sampleTime = time.localtime()

		if match == mod_ws_app.MEASURE_PRECIPITATION and state == 1:
			value = round((self.station.rainGaugeVolume/self.station.rainGaugeArea)*10, 2) # millimetres
		else:
			return

		sample = mod_ws_app.AS_WS_SAMPLE(sampleTime)
		measure = mod_ws_app.AS_WS_SAMPLE.createMeasurement(match, value)
		sample.setMeasurement(measure)
		self.samples.append(sample)

	def aggregateMeasurements(self, mtype, measurements):

		# For digital inputs the aggregate is the sum of the value sampled
		# (that is, the events are additive).
		if mtype in self.inputs:
			return sum(measurements)
		else:
			return super(AS_WS_READER_PWS, self).aggregateMeasurements(mtype, measurements)
	


	def convertSensorValue(self, value, mtype):


			# These conversions are in the product manual
			if mtype == mod_ws_app.MEASURE_TEMPERATURE or mtype == mod_ws_app.MEASURE_INTERNAL_TEMPERATURE:
				return round((value * 0.2222) - 61.111, 1)

			elif mtype == mod_ws_app.MEASURE_RELATIVE_HUMIDITY:
				return int(round((value * 0.1906) - 40.2, 0))

			elif mtype == mod_ws_app.MEASURE_STATION_BAROMETRIC_PRESSURE:
				# This version of the equation requires the use of Phidgets.Devices.InterfaceKit.getSensorRawValue()
				return int(round((((value / 4.095)/4.0) + 10.0) * 10, 0))

			elif mtype == mod_ws_app.MEASURE_PRECIPITATION_WEIGHT:
				return int(round((((value / 70.0) - (10.0/7.0)) * 453.59237), 0))

			else:
				raise ValueError('Unsupported measurement type %s' % str(mtype))


