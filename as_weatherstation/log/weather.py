import logging
import time


def getLogger(stationID):
	import as_weatherstation.config.log as config

	# create logger
	return logging.getLogger(config.getStationLogLoggerID(stationID))


def getLogString(d):

	itemCount = 10 # time and 9 instrument samples
	if __debug__ :
		if not isinstance(d[0], time.struct_time):
			raise AssertionError('Log item zero should be a time object -- %s given' % type(d[0]))
		if not len(d) == itemCount:
			raise AssertionError('Log item should contain %d items: %d given' % (itemCount,len(d)))

	d2 = list(d)
	d2[0] = time.strftime("%Y-%m-%d %H:%M:%S", d[0])
	return ",".join(d2)


def getLatestTimestamp(logFile):
	""" Get latest timestamp by looking at the last line of the log file """
	try:
		line = fileGetLastLine(logFile)
	except (OSError, IOError):
		return None

	tString = line.split(',')[0]

	try:
		t = time.strptime(tString, "%Y-%m-%d %H:%M:%S")
	except ValueError:
		return None

	return t


def fileGetLastLine(filename):
	""" Get the last line of a file """
	import os
	size = os.path.getsize(filename)

	# Do a binary seek of the last n bytes of a file
	# 'n' is 1024 bytes or the length of the file, whichever is less
	maxLineLength = 1024
	if size < 1024: maxLineLength = size

	with open(filename, 'rb') as fh:
		first = next(fh).decode()

		fh.seek(-(maxLineLength), 2)
		last = fh.readlines()[-1].decode()
	return last
