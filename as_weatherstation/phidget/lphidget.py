import time

#Phidget specific imports
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, InputChangeEventArgs, OutputChangeEventArgs, SensorChangeEventArgs
from Phidgets.Devices.InterfaceKit import InterfaceKit
from Phidgets.Devices.TextLCD import TextLCD



class PHIDGET_IFK(object):
    """ Phidget InterfaceKit """
    def __init__(self, serialNumber=None, waitForAttach=1000, **kargs):

        self.interfaceKit = InterfaceKit()

        if 'remoteHost' in kargs:
            self.interfaceKit.openRemote(kargs['remoteHost'], serialNumber)
        else:
            self.interfaceKit.openPhidget(serialNumber)
    
        self.ratiometric = 1
        if 'ratiometric' in kargs:
            self.ratiometric = kargs['ratiometric'] 

        h = [
            'onAttachHandler',
            'onDetachHandler',
            'onErrorhandler',
            'onInputChangeHandler',
            'onOutputChangeHandler',
            'onSensorChangeHandler'
            ]

        for event in h:
            self.__dict__[event] = None
            if event in kargs:
                self.__dict__[event] = kargs[event]

        self.interfaceKit.setOnAttachHandler(self.attached)
        self.interfaceKit.setOnDetachHandler(self.detached)
        self.interfaceKit.setOnErrorhandler(self.error)
        self.interfaceKit.setOnInputChangeHandler(self.inputChanged)
        self.interfaceKit.setOnOutputChangeHandler(self.outputChanged)
        self.interfaceKit.setOnSensorChangeHandler(self.sensorChanged)


        if waitForAttach > 0:
            try:
                self.interfaceKit.waitForAttach(waitForAttach)
            except PhidgetException as e:
                #print("Phidget Exception %i: %s" % (e.code, e.details))
                try:
                    self.interfaceKit.closePhidget()
                except PhidgetException as e2:
                    pass
                raise e



    def attached(self, e):
        self.interfaceKit.setRatiometric(self.ratiometric)
        time.sleep(0.05)
        if self.onAttachHandler: self.onAttachHandler(e)

    def detached(self, e):
        if self.onDetachHandler: self.onDetachHandler(e)

    def error(self, e):
        error = {'code': e.eCode, 'description': e.description}
        if self.onErrorhandler: self.onErrorhandler(error, e)

    def outputChanged(self, e):
        if self.onInputChangeHandler: self.onInputChangeHandler(e.index, e.state, e)

    def inputChanged(self, e):
        if self.onInputChangeHandler: self.onInputChangeHandler(e.index, e.state, e)

    def sensorChanged(self, e):
        if self.onInputChangeHandler: self.onInputChangeHandler(e.index, e.value, e)




class PHIDGET_TEXTLCD(object):
    """ Phidget TextLCD with integrated InterfaceKit """
    def __init__(self, serialNumber=None, waitForAttach=1000, **kargs):

        self.textLCD = TextLCD()

        if 'remoteHost' in kargs:
            self.textLCD.openRemote(kargs['remoteHost'], serialNumber)
        else:
            self.textLCD.openPhidget(serialNumber)


        h = [
            'onAttachHandler',
            'onDetachHandler',
            'onErrorhandler'
            ]

        for event in h:
            self.__dict__[event] = None
            if event in kargs:
                self.__dict__[event] = kargs[event]

        self.textLCD.setOnAttachHandler(self.attached)
        self.textLCD.setOnDetachHandler(self.detached)

        if waitForAttach > 0:
            try:
                self.textLCD.waitForAttach(waitForAttach)
            except PhidgetException as e:
                #print("Phidget Exception %i: %s" % (e.code, e.details))
                try:
                    self.textLCD.closePhidget()
                except PhidgetException as e2:
                    pass
                raise e
    

    def attached(self, e):
        from Phidgets.Phidget import PhidgetID
        if e.device.getDeviceID()==PhidgetID.PHIDID_TEXTLCD_ADAPTER:
            e.device.setScreenIndex(0)
            e.device.setScreenSize(TextLCD.TextLCD_ScreenSize.PHIDGET_TEXTLCD_SCREEN_2x20)
        if self.onAttachHandler: self.onAttachHandler(e)

    def detached(self, e):
        if self.onDetachHandler: self.onDetachHandler(e)

    def error(self, e):
        error = {'code': e.eCode, 'description': e.description}
        if self.onErrorhandler: self.onErrorhandler(error, e)

