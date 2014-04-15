#!/usr/local/bin/python
# coding: utf-8

import re
import time
import threading, Queue
#import as_weatherstation.threading as threading

from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException


import as_weatherstation.app as mod_ws_app
import as_weatherstation.write.abstract as mod_ws_write_abstract

import as_weatherstation.phidget.lphidget as mod_lphidget

# Bitwise writer options
TEXTLCD_OPT_NONE = 0
TEXTLCD_OPT_NAME = 1
TEXTLCD_OPT_TIME = 2
TEXTLCD_OPT_NET = 4
TEXTLCD_OPT_ALL = 7


class AS_WS_WRITER_TEXTLCD(mod_ws_write_abstract.AS_WS_WRITER):
    """ Display samples on a Phidget TextLCD """

    def __init__(self, wsApp, sLabel=None):

        super(AS_WS_WRITER_TEXTLCD, self).__init__(wsApp)

        self.resetLines() # the lines that we printed
        self.rMax = 2 # default rows of LCD screen -- get real size with self.getDisplaySize()
        self.cMax = 20 # default cols of LCD screen

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


        # Connect the Phidget TextLCD
        #
        # We are not going to block or wait for attachement.
        # Phidget will raise exceptions if you do things before attachement
        # occurs. Therefore, you should call self.textLCD.textLCD.isAttached()
        # or self.textLCD.textLCD.waitForAttach(milliseconds) before
        # calling self.write(), etc.
        self.isAttached = False
        args = {
            'waitForAttach': 0,
            'serialNumber': self.station.textLCDID,
            'onAttachHandler': self.onAttachHandler,
            'onDetachHandler': self.onDetachHandler
        }
        if 'remoteHost' in self.station.__dict__:
            args['remoteHost'] = self.station.remoteHost

        self.textLCD = mod_lphidget.PHIDGET_TEXTLCD(**args)


        # http://www.phidgets.com/docs/LCD_Character_Display_Primer
        # This list is not complete, but covers the most common
        # punctuation and symbols. The degree symbol is probably the
        # only one we care about.
        self.charmap = {
            '\x21': '!',
            '\x22': '"',
            '\x23': '#',
            '\x24': '$',
            '\x25': '%',
            '\x26': '&',
            '\x27': '’',
            '\x28': '(',
            '\x29': ')',
            '\x2A': '*',
            '\x2B': '+',
            '\x2C': ',',
            '\x2D': '-',
            '\x2E': '.',
            '\x2F': '/',
            '\x3A': ':',
            '\x3B': ';',
            '\x3C': '<',
            '\x3D': '=',
            '\x3E': '>',
            '\x3F': '?',
            '\xDF': '°'
            }



    def onAttachHandler(self, e):
        """ Do stuff when the Phidget TextLCD is attached """

        self.isAttached = True

        # Setup custom 'trend' characters
        # http://www.phidgets.com/documentation/customchar.html
        e.device.setCustomCharacter(0, 1017984, 130)
        e.device.setCustomCharacter(1, 167392, 521)
        e.device.setCustomCharacter(2, 311296, 15461)



    def onDetachHandler(self, e):
        """ Do stuff when the Phidget TextLCD is detached """
        global exitFlag

        threadLock.acquire()
        self.isAttached = False
        exitFlag = 1
        threadLock.release()

        

    def getDisplaySize(self):
        """ Get the row and column lengths for the TextLCD. Only do this after teh TextLCD is attached. """
        self.cMax = self.textLCD.textLCD.getColumnCount()
        self.rMax = self.textLCD.textLCD.getRowCount()



    def resetLines(self):
        """ Empty the line cache """
        self.lines = []


    def write(self, samples, duration=60, options=TEXTLCD_OPT_ALL):
        """ Calculate some trends for the given sample measurements and them display on the TextLCD """
        """
        - samples list: AS_WS_SAMPLE objects. Last is displayed and others are used to calculate trend.
        - duration int: Seconds over which to display the data
        - options int: Bitwise cobination of TEXTLCD_OPT*. Enables display of additional data, such as
            sample time, station IP addresses, etc.
        """
        
        # Split the latest sample off from the previous ones
        if len(samples) > 1:
            current = samples[-1]
            recent = samples[0:-1]
        else:
            current = samples[0]
            recent = [samples[0]]

        # Aggregate the recent samples
        aggregate = self.aggregateSamples(recent).pop()

        # Get a list of the fields the station supports
        fm = self.app.fieldMap[self.station.stype]

        # Assign a trend icon to each measurement
        trends = {}
        for mtype in fm:

            # Ignore any measurements that the station does not handle
            # (logs have zeros for missing measurements, and we don't care about those).
            if not fm[mtype] is None:

                mCurrent = current.getMeasurement(mtype)
                if mCurrent is None:
                    break
                mAggregate = aggregate.getMeasurement(mtype)
                if mAggregate is None:
                    break

                vCurrent = mCurrent.value
                vAggregate = mAggregate.value

                if vCurrent > vAggregate:
                    trends[mtype] = 1 # up
                elif vCurrent < vAggregate:
                    trends[mtype] = 2 # down
                else:
                    trends[mtype] = 0 # steady


        # Get the display size
        self.getDisplaySize()


        # Display status on TextLCD
        for n in range(self.rMax):
            self.textLCD.textLCD.setDisplayString(n, "")
        self.textLCD.textLCD.setDisplayString(0, "Updating...")
        self.textLCD.textLCD.setCursorBlink(True)


        # Prepare the display lines
        lines = []

        if options & TEXTLCD_OPT_NAME:
            # The first line will display the station label
            slabel = re.sub('_', ' ', self.station.label).title()
            #lines.append((slabel[:18] + '..') if len(slabel) > 20 else slabel)
            lines.append(slabel)

        if options & TEXTLCD_OPT_TIME:
            # The second line will display the date and time of the current sample
            lines.append(time.strftime("%Y-%m-%d %H:%M:%S", current.dateTime))

        if options & TEXTLCD_OPT_NET:
           for interface in self.getInterfaces():
                lines.append('%s %s' % (interface['interface'], interface['ip']))
            

        # Format each label, measurement, and trend in a 20 character long string.
        # Label is left justified. Measurement and trend are right justified.
        for mtype in trends:
            m = current.getMeasurement(mtype)
            value = m.getFormattedString(0)
            label = m.labelLong
            # Try to fit the text on a line with out scrolling
            if (len(value) + len(label)) > (self.cMax - 3):
                label = m.labelShort
            w = self.cMax - 3 - len(label)    
            text = ('{0} {1: >'+str(w)+'}').format(label, self.mapSpecialCharacters(value))
            lines.append(text + " " + self.textLCD.textLCD.getCustomCharacter(trends[mtype]))


        # Display the lines
        self.displayLines(lines, duration)
        


    def displayLines(self, lines, duration=60, mode='scroll'):
        """ Display a list of text lines on the TextLCD. The lines are cached in self.lines """
        """
        - lines list: text to display
        - duration int optional: Seconds over which all lines will be displayed. Default is 60
        - mode string optional: display method. Default scroll. see AS_WS_WRITER_TEXTLCD.displayText()

        TODO: Add 'wrap' mode to wrap long lines to display width. Additional lines will be created.
        """

        self.lines = lines

        # We will display rMax lines at a time, so make sure we have an appropriate number.
        if len(self.lines) % self.rMax:
            self.lines.append('')

        # Calculate how long each screen should be displayed
        screenDuration = duration/(len(self.lines)/2)

        # Create the screens
        screens = []
        i = 0
        while i < len(self.lines):
            screenLines = []
            for n in range(i, i+self.rMax):
                screenLines.append(self.lines[n])
            screens.append({'lines': screenLines, 'duration': screenDuration, 'mode': mode})
            i = i + self.rMax

        self.displayScreens(screens)



    def displayScreens(self, screens):
        """ Display screens on the TextLCD using threads to allow asynchronous line animation. """
        """
        - screens dict:
            - lines list: text lines that will be displayed on this screen (max = self.rMax)
            - duration int optional: how many seconds to display the screen for
            - mode string optional: animation mode (see AS_WS_WRITER_TEXTLCD.displayText())
        """

        global exitFlag
        exitFlag = 0

        self.textLCD.textLCD.setCursorBlink(False)

        # Create a thread for each line.
        # Every screen must contain the same number of lines.
        # We use threads so that individual lines can be animated
        # without blocking the display of subsequent lines.
        # Each thread will have its own queue to pull text from.
        threads = []
        threadQueues = []
        for i in range(0, len(screens[0]['lines'])):
            threadQueues.append(Queue.Queue(1)) # only accept 1 item at a time (we handle the timer, not the queue)
            thread = AS_WS_WRITER_TEXTLCD_THREAD(
                i,
                'Thread%d'%(i),
                threadQueues[i]
                )
            thread.start()
            threads.append(thread)



        # Put the screen lines in the thread queues and then sleep for the required duration.
        for screen in screens:
            if exitFlag: # we may be interrupted mid process if the TextLCD is detached
                break
            for i in range(0, len(screen['lines'])):
                threadLock.acquire()
                threadQueues[i].put({
                    'callback': self.displayText,
                    'kargs': {
                        'row': i,
                        'text': screen['lines'][i],
                        'mode': screen['mode'],
                        'duration': 0
                        }
                    })
                threadLock.release()

            time.sleep(screen['duration'])

            # Wait for queue to empty
            for threadQueue in threadQueues: 
                while not threadQueue.empty():
                    pass

        # Notify threads it's time to exit
        exitFlag = 1
        #print "exitFlag %d" % exitFlag

        # Wait for all threads to complete
        for t in threads:
            t.join()
        

    def displayText(self, row, text, duration=10, mode='scroll'):
        """ Display a line of text on the Phidget TextLCD """
        """
        row int - which line to display one (0 or 1)
        text string - will trim or scroll if longer than 20 characters
        duration int - how long to display the text. After screen is updated we will block for this amount of time.
        mode string - scroll, trim (default), or None
        """
        if len(text) <= self.cMax:
            # print
            if self.textLCD.textLCD.isAttached():
                # We tend to seg fault if more than one thread talks to
                # the display at one time, so get a lock first
                threadLock.acquire()
                #print 'displayText', row, text, duration
                self.textLCD.textLCD.setDisplayString(row, text)
                threadLock.release()
                time.sleep(duration)
            return
        elif mode == 'scroll':
            # scroll
            frameDuration = 0.25
            frameCount = len(text)-self.cMax
            for i in range(0, frameCount+1):
                self.displayText(row, text[i:self.cMax+i], frameDuration, None)
                continue
            time.sleep(frameDuration*2) # triple the length of time the last frame is displayed
            self.displayText(row, text[:self.cMax], max(1,duration-frameDuration*(frameCount+2)), None)
        else:
            # trim
            t = (text[:self.cMax-2] + '..') if len(text) > self.cMax else text
            self.displayText(row, t, None)
        

            
    def mapSpecialCharacters(self, s):
        """ Replace special characters in string with Phidget TextLCD friendly characters """
        # TODO strip any character greater than \xFF

        for i in self.charmap:
            regex = re.compile(re.escape(self.charmap[i]))
            s = re.sub(regex, i, s)
        return s


    
    def aggregateSamples(self, samples):
        """ Aggregate the values of a sample list """

        if not samples:
            return []

        measurements = {}
        for sample in samples:
            sampleTime = sample.dateTime # keep only the last time (this assumes the samples are in order, which they should be)
            for mtype in sample.measurements:
                if not mtype in measurements:
                    measurements[mtype] = []
                measurements[mtype].append(sample.measurements[mtype].value)


        aSample = mod_ws_app.AS_WS_SAMPLE(sampleTime)
        for mtype in measurements:
            value = self.aggregateMeasurements(measurements[mtype])
            measure = mod_ws_app.AS_WS_SAMPLE.createMeasurement(mtype, value)
            aSample.setMeasurement(measure)

        return [aSample]



    def aggregateMeasurements(self, measurements):
        """ Calculates the average for a given set of measurements """

        return sum(measurements)/len(measurements)



    def getInterfaces(self):
        """ Get the IP addresses of the network interfaces """

        import subprocess

        regex = re.compile("^((eth|en|wlan)\d+).*(HWaddr|ether) ([^ ]+).*(addr:|inet )([^ ]+)", re.MULTILINE|re.DOTALL)

        interfaces = []
        for interface in ['en0', 'en1', 'eth0', 'wlan0']:

            try:
                a = subprocess.check_output('ifconfig %s' % interface, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                continue
                
            result = regex.match(a)

            if result != None:
                interF = result.group(1)
                mac = result.group(4)
                ip = result.group(6)

                interfaces.append({'interface': interF, 'ip': ip, 'mac': mac})

        return interfaces



"""
********************************************************************************
Thread Related Stuff
********************************************************************************
"""

exitFlag = 0

class AS_WS_WRITER_TEXTLCD_THREAD(threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    
    def run(self):
        """ Called on Start() """
        """
        While global exitFlag is false, try to execute an item from our queue.
        If the queue is empty, wait a while and then try again.
        Loop can be terminated by setting global exitFlag to true.
        """
        global exitFlag
        while not exitFlag:
            #print 'Thread exitFlag %d' % exitFlag
            threadLock.acquire()
            if not self.q.empty():
                data = self.q.get()
                threadLock.release()
                data['callback'](**data['kargs'])
                self.q.task_done()
            else:
                threadLock.release()
            time.sleep(0.5)

""" Global thread lock object """
threadLock = threading.RLock()
