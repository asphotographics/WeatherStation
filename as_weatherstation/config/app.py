#! /usr/bin/python
# coding: utf-8

import ConfigParser


class AS_CONFIGPARSER_EXCEPTION(Exception):

    def __init__(self, code, message):
        self.code = code
        self.message = message





class AS_CONFIGPARSER_ERROR_CODES():

    fileExists = 1




class AS_CONFIGPARSER(ConfigParser.SafeConfigParser, object):

    def __init__(self, allow_no_value=True):

        super(AS_CONFIGPARSER, self).__init__(allow_no_value=allow_no_value)

        #super(AS_PWS_APP, self).__init__()
        self.optionxform = str # we don't want option names transformed -- spell them correctly!
        self.filePath = 'app.cfg'
        self.mode = 'new'



    """
    @staticmethod
    def super(aType, instance):
        # ConfigParser.SafeConfigParser is an old-style object and can't be used with super.
        # Just so we don’t call the wrong ancestor somewhere else we will create our own
        # reference to ConfigParser.SafeConfigParser. Use AS_CONFIGPARSER.super(), wherever you would normally
        # use super(). You will have to pass self to all class methods of AS_CONFIGPARSER.super(), unfortunately.

        return ConfigParser.SafeConfigParser 
    """
       


    def write(self, fileobject=None):
        """ Similar to the parent method, but allow an empty fileobject
        as we prefer to write to self.filePath. Raise error if attempting
        to write to an existing file and not in edit mode. """

        if fileobject is None:

            self.writeToPath(self.filePath)

        else:

            if self.mode != 'edit' and len(fileobject.read(1)):
                raise AS_CONFIGPARSER_EXCEPTION(
                    AS_CONFIGPARSER_ERROR_CODES.fileExists,
                    "Configuration file '%s' exists and is not empty" % fileobject.name
                    )

            super(AS_CONFIGPARSER, self).write(fileobject)


    def isfile(self, filepath):
        """ Check if file exists """
        
        from os.path import isfile
        return isfile(filepath)
            

    def writeToPath(self, filepath=None):
        """ Write to a path instead of a file object. """

        if filepath is None:
            filepath = self.filePath

        if self.mode != 'edit' and self.isfile(filepath):
            raise AS_CONFIGPARSER_EXCEPTION(AS_CONFIGPARSER_ERROR_CODES.fileExists, "Configuration file '%s' already exists" % filepath)

        with open(filepath, 'w+b') as configfile:
            self.write(configfile)


    def read(self, filenames=None):
        """ Similar to parent read, but allow filenames to be None, as we prefer to read from self.filePath """
        if filenames is None:
            filenames = self.filePath
        self.mode = 'edit'
        return super(AS_CONFIGPARSER, self).read(filenames)





# Factory
def getConfig():

    config = AS_CONFIGPARSER()
    config.read()
    return(config)


def getStationOption(config, otypes, section, option):
    """ Dynamically convert station options to the valid type """

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
            if rawValue is None or rawValue == '':
                return None
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
        
