import as_weatherstation.app as mod_ws_app
import as_weatherstation.read.abstract as mod_ws_read_abstract


class AS_WS_READER_CSVFILE(mod_ws_read_abstract.AS_WS_READER):
    """ CSV file reader """

    def __init__(self, wsApp):

        super(AS_WS_READER_CSVFILE, self).__init__(wsApp)



    def read(self, aFile, lines=0):

        self.samples = self.readCSV(aFile, lines)

        return self.samples



    def readCSV(self, aFile, lines=0):

        if lines > 0:
            return self._readCSVLines(aFile, lines)
        else:
            print aFile
            return self._readCSV(aFile)



    def _readCSV(self, aFile):
        """ Read a csv file into a multi-dimensional list """

        import csv, gzip

        samples = []
        if self.isGZipped(aFile):
            func = gzip.open
        else:
            func = open
        with func(aFile, 'rb') as f:
            csvData = csv.reader(f, delimiter=",")
            for row in csvData:
                samples.append(self.parseCSVLine(row)) 

        return samples


    def isGZipped(self, aFile):
        import re
        if re.compile('\.gz$').findall(aFile):
            return True
        else:
            return False



    def _readCSVLines(self, aFile, lines):

        import subprocess

        # The shell command to get the recent history from the file
        if self.isGZipped(aFile):
            getLatestLogs = 'gzip -dck "%s" | tail -n%d' % (aFile, lines)
        else:
            getLatestLogs = 'tail -n%d "%s"' % (lines, aFile)

        # Spawn a command line process, and obtain the output
        getLatestLogsProc = subprocess.Popen(getLatestLogs, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        l = [line.strip() for line in getLatestLogsProc.stdout]

        #print l;

        samples = []
        if len(l) == 0:
            return samples

        import csv
        csvData = csv.reader(l, delimiter=",")
        for row in csvData:
            samples.append(self.parseCSVLine(row)) 

        return samples



    def parseCSVLine(self, line):
    
        return line

