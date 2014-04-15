import logging
import time


def getLogger(stationID):
	import as_weatherstation.config.log as config

	# create logger
	return logging.getLogger(config.getStationTimestampLoggerID(stationID))


def getLogString(d):

	itemCount = 1 # time
	if __debug__ :
		if not isinstance(d[0], time.struct_time):
			raise AssertionError('Timestamp item zero should be a time object -- %s given' % type(d[0]))
		if not len(d) == itemCount:
			raise AssertionError('Timestamp should contain %d items: %d given' % (itemCount,len(d)))


	d2 = list(d)
	d2[0] = time.strftime("%Y-%m-%d %H:%M:%S", d[0])
	return ",".join(d2)


def getLatestTimestamp(timestampFile):
	""" Get the latest timestamp from the timestamp file """
	try:
		t = time.strptime(file_get_contents(timestampFile).rstrip(), "%Y-%m-%d %H:%M:%S")
	except (IOError, ValueError):
		return None
	return t


def file_get_contents(filename):
  with open(filename) as f:
    return f.read()

