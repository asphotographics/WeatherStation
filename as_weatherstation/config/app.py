#! /usr/bin/python


def getConfig():

	import ConfigParser

	config = ConfigParser.SafeConfigParser(allow_no_value=True)
	config.optionxform = str # we don't want option names transformed -- spell them correctly!
	config.read('app.cfg')

	return(config)

def getStationOption(config, section, option):
	""" Dynamically convert station options to the valid type """

	from decimal import Decimal

	otypes = {
		'stype': str,
		'elevation': int,
		'interfaceKitID': int,
		'textLCDID': [None, int],
		'intervalSensorSample': int,
		'intervalSensorLog': int,
		'sensorBP': int,
		'sensorInternalTemp': int,
		'sensorLoad': int,
		'sensorRH': int,
		'sensorTemp': int,
		'rainGaugeArea': Decimal,
		'rainGaugeVolume': Decimal,
		'inputRG': int,
		'remoteHost': str,
		'deviceID': str,
		'moduleID': [None, str]
		}

	rawValue = config.get(section, option)

	if not option in otypes:
		return rawValue

	otype = otypes[option]
	if isinstance(otypes[option], list):
		otype = otypes[option]
	else:
		otype = [otypes[option]]

	v = None
	for t in otype:
		if t is None:
			if rawValue is None:
				return rawValue
		else:
			try:
				v = t(rawValue)
				break
			except ValueError:
				continue

	if v is not None:
		return v
	else:
		return rawValue
		
