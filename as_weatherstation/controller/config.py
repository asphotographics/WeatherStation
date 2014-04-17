#!/usr/bin/python
# encoding=utf-8

"""
********************************************************************************
@package Controller Weather Station Config
********************************************************************************

This controller executes the main run loop of the config setup
command-line utility.

This script can be run when setting up or modifying an application instance
as an alternative to editing app.cfg by hand. It makes sure required
options are filled out and has lots of nice goodies to help administrators
understand the available options and the data types associated with them.

********************************************************************************
CONFIGURATION
********************************************************************************
app.cfg
    - basic app config: data directory, DB connection info, station IDs and details
    - PWS configuration (sensor/input port assignment, rain gauge calibration
        logging/polling intervals)

as_ws.log.config - log configration: rotation times, backup count


********************************************************************************
TODO
********************************************************************************
- use tput to get terminal screen size and clear display occasionaly


********************************************************************************
CHANGELOG
********************************************************************************
v1.0 - config conroller created


********************************************************************************
"""

import cmd
import ConfigParser
from collections import OrderedDict

import as_weatherstation.controller.abstract as mod_ws_controller_abstract
import as_weatherstation.app as mod_ws_app
import as_weatherstation.config.app as mod_ws_config_app


class AS_CONTROLLER_CONFIG(mod_ws_controller_abstract.AS_CONTROLLER_ABSTRACT):
    """ Controller that runs a command-line configuration file setup routine. """

    def __init__(self):
        """ Call super().__init__() and instantiate an AS_CONFIGPARSER() """

        super(AS_CONTROLLER_CONFIG, self).__init__()

        self.config = mod_ws_config_app.AS_CONFIGPARSER()



    def _main(self):
        """ Start the command-line configuration application. """

        """
        Plan:
        Check if default config file exists
            If it does, ask if user if they want to edit it
                If edit, load file
                
        After entering the run loop, the user can:

            Run wizard which runs setup and add_station
            Run setup which configures the main sections (app, DB, netatmo, FTP)
            Run add_station to add a new station (or edit_station to edit an existing station)
            Run print to preview the configuration
            Run save to write the configuration out to file

        """

        setupCmd = AS_CMD_MAIN(self.config)
        l = setupCmd.precmd('read')
        r = setupCmd.onecmd(l)
        r = setupCmd.postcmd(r, l)
        if not r:
            setupCmd.cmdloop()


class AS_CMD_ABSTRACT(cmd.Cmd, object):
    """
    A Cmd object used to set-up the Weather Station configuration.

    This is an abstract class which defines general config related methods, such as setting prompts
    handling user input, getting config values, explainig config options, etc. It can be
    sub-classed to perform nested command operations.

    see https://wiki.python.org/moin/CmdModule
    """

    def __init__(self, config, parentCommand=None):
        """
        @brief Call super().__init__(), store the config, and setup the 'explain' and 'defaults' configs.

        @param config AS_CONFIGPARSER object - the config parser used to read/write config files, and hold option values
        @param parentCommand optional AS_CMD_ABSTRACT object - for nested operations
        """

        super(AS_CMD_ABSTRACT, self).__init__()

        self.parentCommand = parentCommand

        self.config = config

        # The 'explain' file acts like a regular config file, but the value of
        # each option is actually a help text string explaining the option.
        self.explainFile = 'as_weatherstation/config/app-explain.cfg'
        self.explainConfig = mod_ws_config_app.AS_CONFIGPARSER()
        self.explainConfig.read(self.explainFile)

        # The 'defaults' file acts like a regular config file, but the value of
        # each option is actually a default which can be used to pre-populate
        # a new configuration. Only of a subset of options will have a
        # default value.
        self.defaultsFile = 'as_weatherstation/config/app-defaults.cfg'
        self.defaultsConfig = mod_ws_config_app.AS_CONFIGPARSER()
        self.defaultsConfig.read(self.defaultsFile)



    def getPrompt(self):
        """ Return the prompt string displayed at the command line """
        if isinstance(self.parentCommand, AS_CMD_ABSTRACT):
            return self.concatPrompt(self.parentCommand.prompt, self._prompt)
        else:
            return '[ configure ] '

    def setPrompt(self, prompt):
        """ Set the prompt string displayed at the command line """
        self._prompt = prompt

    def delPrompt(self):
        """ Do nothing -- prompt is required to have a value """
        return

    prompt = property(getPrompt, setPrompt, delPrompt, None)

    def concatPrompt(self, oldPrompt, newPrompt):
        """ Build hierarchical prompt string by chaining together the prompts from ancestors """
        return "%s:%s ] " % (oldPrompt[:-3], newPrompt)



    def help_exit(self):
        print ""
        print "Exit %s." % self.prompt
        print "You can also use the Ctrl-D shortcut."
        print ""

    def do_exit(self, s):
        """
        Exit a command loop
        
        Called from a nested Cmd, it returns to us to the parent command loop.
        Called from the root Cmd, it will exit the main run loop and probably end the program
        """
        return True



    def help_list(self):
        print ""
        print "list"
        print "    print a selection of help topics"
        print ""

    def do_list(self, s):
        """ Show selection of help pages for all available commands """

        import re

        regex = re.compile('^help_(.*)')
        h = []
        for i in sorted(dir(self)):
            m = re.match(regex, i)
            if not m is None:
                h.append(m.group(1))

        if len(h) == 0:
            print ""
            print "INFO: No help topics found."
            print ""
            return

        print ""
        print "Choose a help topic:"
        s = self.rawInput(choices=h)
        if isinstance(s, bool):
            return s

        try:
            getattr(self, 'help_%s' % s)()
        except AttributeError as e:
            print ""
            print "ERROR: 'help %s' could not be found." % s
            print ""



    def help_quit(self):
        import os
        print ""
        print "Quit %s without saving." % os.path.basename(__file__)
        print ""

    def do_quit(self, s):
        """ Exit the script after confirmation """
        if self.confirmQuit():
            exit()

    def confirmQuit(self):
        """ Confirm the quit command """
        print ""
        print "Are you sure you want to discard unsaved changes and quit?"
        if self.rawInput(choices=['yes', 'no']) == 'yes':
            return True



    def rawInput(self, prompt=None, choices=None, allowOther=''):
        """
        A helper method for getting user input outside the command (do_) structure 

        @param prompt optional str - prompt string displayed at the command line.
            If None, then default Cmd prompt will be used.
        @param choices optional list - String choices that will be presented to the user
            with a select modal dialog. If ommited, text input is returned
        @param allowOther optional str - Used in conjuction with choices. If not empty,
            an "other" choice will be appended to choices. If the user selects "other"
            then they will be asked to enter input according to the instructions of allowOther.

        @return str value selected or entered
        """

        if prompt is None:
            prompt = self.prompt

        other = 'other..'
        if choices:
            if allowOther != '':
                choices.append(other)

        # If choices then we loop until the user makes a valid selection
        # Fo normal input, we exit after the first iteration.
        go = True
        while go == True:

            if choices:
                print ""
                for i in range(0, len(choices)):
                    print '    [%d] %s' % (i+1, choices[i])
                print ""
            else:
                go = False

            s = raw_input(prompt)

            # User can abort by entering one of the following commands
            if s in ['exit', 'quit', 'cancel']:
                l = self.precmd(s)
                r = self.onecmd(l)
                return self.postcmd(r, l)


            # Ask user to select a choice
            if choices:

                # If user makes an invalid selection make then try again
                try:
                    i = int(s)
                    if i == 0 or i > len(choices):
                        raise ValueError()
                except ValueError as e:
                    print ""
                    print "ERROR: Invalid selection '%s' entered." % s
                    print ""
                    print "Try again:"
                    continue

                v = choices[i-1]

                # "other" chosen, recursively prompt for input
                if allowOther and v == other:
                    print ""
                    print allowOther
                    return self.rawInput(prompt)

            else:

                v = s

            go = False

        return v



    def help_cancel(self):
        print ""
        print "cancel"
        print "    Cancel the current operation."
        print ""

    def do_cancel(self, s):
        """ Cancel a command """
        print ""
        print "OKAY: Command canceled."
        print ""
        return False



    def help_explain(self):
        print ""
        print "explain"
        print "    See an explanation of each available option."
        print ""
        print "explain <section> <option>"
        print "    See an explanation of <option> in <section>"
        print ""

    def do_explain(self, s):
        """
        Diplay an explanation of config file options.

        @param s str - If s is empty, read and display the entire explain file, else,
            try to explain just the option and/or section specified by s. Normally,
            s is '[section] [option]'. If self.section is set, then s can simply
            be '[option]' and we will use self.section as a default.
        """
        

        if s == '':

            # Nothing fancy. Just read and print the "exlain" file.
            explainFile = 'as_weatherstation/config/app-explain.cfg'
            print ""
            print "OKAY: Displaying '%s'" % self.explainFile
            print ""
            with open(self.explainFile, 'rb') as configfile:
                print configfile.read()

            return

        else:

            parts = str.split(s, ' ', 1)

            if len(parts) < 2:
                if hasattr(self, 'section'):
                    parts = [self.section, ' '.join(parts)] 
                else:
                    print ""
                    print "ERROR: Command must be in the form 'explain <section> <option>'."
                    print ""
                    return

            noExplanation = {'boolean': False}
            e = AS_CMD_ABSTRACT.getConfigValue(self, parts[0], parts[1], noExplanation, self.explainConfig)

            if noExplanation['boolean'] == True:
                print ""
                print "WARNING: No explanation for option '%s' in [%s]." % (parts[1], parts[0])
                print ""
            else:
                print ""
                print "[%s] %s" % (parts[0], parts[1])
                print "    %s" % e
                print ""



    def getConfigValue(self, section, option, noOption={}, config=None):
        """
        Get a value for a configuration [option] in [section] from [config] object 

        @param section str - the name of the section to look in
        @param option str - the name of the option to get the value of
        @param noOption optional dict - noOption['boolean'] will be set to True if the
            option or section is missing from config. If the option of section is
            found in config, then noOption['boolean'] is set to False. This exists
            so that you can get the existence/non-existence of the option sent
            back via reference, because you can’t always tell by the return value
            if the value was actually retrieved from the config or not.
        @param config optional AS_CONFIGPARSER object - if present, it will be used, otherwise
            self.config will be used.

        @return string
        """

        if config is None:
            config = self.config

        try:
            v = str(config.get(section, option, raw=True))
            noOption['boolean'] = False
            return v
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as e:
            noOption['boolean'] = True
            return ''

    

    def help_help(self):
        print ""
        print "help <topic>"
        print "    print help for the given topic"
        print ""



    def help_print(self):
        print ""
        print 'print'
        print "    Print the current state of the configuration to the screen."
        print ""

    def do_print(self, s):
        """ Print the current config sections and options """
        self._print()

    def _print(self, config=None):
        """ Print the current config sections and options """

        from StringIO import StringIO

        if config is None:
            config = self.config

        # Use StringIO file-like oobject to capture output in memory
        configFile = StringIO()
        config.write(configFile)
        print ""
        print configFile.getvalue()
        print ""



    def emptyline(self):
        """ If user hits enter with an empty line, show help """
        self.do_help('')



class AS_CMD_MAIN(AS_CMD_ABSTRACT):
    """
    @brief Extend AS_CMD_ABSTRACT to do more wizardy type setup stuff

    This class can be used as the main run loop for a config setup program,
    as it nows how to read and write files, kick of sub-commands, etc.
    """

    _prompt = 'main'

    _read = False

    def __init__(self, config, parentCommand=None):
        """
        @brief Call super().__init__() and define which sections to configure in the wizard.

        @param config AS_CONFIGPARSER object - the config parser used to read/write config files, and hold option values
        @param parentCommand optional AS_CMD_ABSTRACT object - for nested operations
        """

        super(AS_CMD_MAIN, self).__init__(config, parentCommand)

        self._wizardSections = OrderedDict()
        self._wizardSections['app'] = AS_CMD_SECTION_APP
        self._wizardSections['database_main'] = AS_CMD_SECTION_DB
        self._wizardSections['ftp'] = AS_CMD_SECTION_FTP
        self._wizardSections['netatmo'] = AS_CMD_SECTION_NETATMO


    def preloop(self):
        """ Before starting the main loop show the intro text """
        self.help_intro()
        super(AS_CMD_MAIN, self).preloop()

    def postloop(self):
        """ After the main loop ends say goodbye """
        print ""
        print 'OKAY: Goodbye'
        print ""
        super(AS_CMD_MAIN, self).postloop()



    def help_read(self):
        print ""
        print 'read'
        print '    Read default configuration file (%s).' % self.config.filePath
        print 'read <file>'
        print '    Read configuration file <file>'
        print ""

    def do_read(self, filename):
        """
        Read a config file into a config object

        @param filename string - If empty, the default file specified by the config object will be read.
            If a config file was already loaded in this session then display an error. To load a second
            file, you shoudl first quit the program and start over. Show an error if file cannot be
            read (doesn't exist, bad permissions, etc.) Before reading the file, confirm with user.
        """

        if self._read:
            print ""
            print "ERROR: Config file '%s' already loaded. Cannot load another file." % self._read
            print ""
            return

        if filename == '':
            filename = self.config.filePath

        if not self.config.isfile(filename):
            print ""
            print "ERROR: File '%s' could not be read." % filename
            print ""
            return

        else:

            print ""
            print "NOTICE: File '%s' exists." % filename
            print ""
            print "This file's options will override any options already set in this session."
            print ""
            print "Do you want to continue reading this file?"
            s = self.rawInput(choices=['yes', 'no'])
            if isinstance(s, bool):
                self.config.mode = 'new'
                return s

            if s == 'yes':
                self.config.read(filename)
                self.config.mode = 'edit'
                self._read = filename
                self._print()
                print "OKAY: Configuration file '%s' loaded." % filename
                print ""
            else:
                self.config.mode = 'new'



    def help_intro(self):
        print ""
        print "********************************************************************************"
        print "Welcome to the Weather Station configuration setup utility."
        print "********************************************************************************"
        print ""
        print "This utility will help you create a .cfg file for your station application."
        print "The information required will vary depending on your station type."
        print "Look at app-sample.cfg for some examples of different options to be set."
        print ""
        print "Type 'explain' to see an explanation of each available option."
        print "Type 'wizard' to walk through the setup process."
        print "Type 'save' to save the configuration to a file."
        print "Type 'help' or ? to get a complete list of commands."
        print "Type 'list' to choose a command from a list."
        print ""
        print "Current mode: %s" % self.config.mode
        print ""


    def help_exit(self):
        """ Similar to the parent method, but warn that unsaved data is discarded """
        super(AS_CMD_MAIN, self).help_exit()
        print "Unsaved data is discarded."
        print ""

    def do_exit(self, s):
        """ Exit after confirmation (this class will usually be the root Cmd). """
        return self.confirmQuit()



    def help_wizard(self):
        print ""
        print "Start the setup wizard. Wizard runs the 'setup' and 'add_station' commands."
        print ""

    def do_wizard(self, s):
        """ Setup wizard, runs basic setup commands and then prompts to add a station if none are present """

        commands = []
        commands.append('setup')
        for command in commands:
            l = self.precmd(command)
            r = self.onecmd(l)
            r = self.postcmd(r, l)
            if r:
                return r

        if not self.config.has_section('stations'):

            s = ''
            while not s:
                print ""
                print "Enter the label for your first station (like 'STATION_KIND_LOCATION' or 'STATION_NETATMO_HOME_INDOOR'):"
                prompt = '%sstation label = ' % self.concatPrompt(self.prompt, 'stations')
                s = self.rawInput(prompt)
                if isinstance(s, bool):
                    return s

            l = self.precmd('add_station %s' % s)
            r = self.onecmd(l)
            r = self.postcmd(r, l)
            if r:
                return r

        print ""
        print "OKAY: Done wizard."
        print ""



    def help_setup(self):
        print ""
        print 'setup <section>'
        print '    Setup a section: %s' % ', '.join(self._wizardSections.keys())
        print 'setup'
        print '    Setup all sections.'
        print ""


    def do_setup(self, s):
        """
        Setup a non-station section.

        @param s string - If empty, then all sections run by wizard are configured.
            If not empty, then s should specifiy a non-station section to configure.
        """

        if s == '':
            sections = self._wizardSections
            s = 'all'
        else:
            if not s in self._wizardSections:
                print ""
                print "ERROR: Invalid section '%s'. Valid sections: %s" % (s, ', '.join(self._wizardSections.keys()))
                print ""
                return
            sections = OrderedDict([(s, self._wizardSections[s])])

        for section in sections:
            self._setup(sections[section], section, s)


    def _setup(self, aCmd, section, string, **kargs):
        """
        Configure a section using a nested AS_CMD_SECTION_* class.

        If string is not 'all' and config mode is not 'new' then enter aCmd's main run loop.

        @param aCmd AS_CMD_SECTION_* class reference - aCmd is instantiated with args 'section' and 'kargs'.
            If config mode is 'new' then class's 'set' command is run with out other arguments.
        @param section string - passed to aCmd on instantiation as both the 'section' and 'prompt' arguement.
        @param string string - not passed to aCmd, but if is 'all' then classes 'set' command is run
            with out other arguments.
        @param kargs optional - additional arguments unpacked and passed to aCmd.
        """
            
        setupCmd = aCmd(self.config, self, section, section, **kargs)
        
        if string == 'all' or self.config.mode == 'new':
            l = setupCmd.precmd('set')
            r = setupCmd.onecmd(l)
            r = setupCmd.postcmd(r, l)
        else:
            setupCmd.cmdloop()


    def help_edit_station(self):
        print ""
        print "edit_station"
        print "    Show a list of stations to edit."
        print "edit_station <station label>"
        print "    You will be prompted to edit the station's options."
        print ""


    def do_edit_station(self, s):
        """
        Edit a station using a nested AS_CMD_SECTION_STATION object. 

        @param s string - If empty, then prompt user to select a station to edit.
            If not empty, then s should specify the label the station to edit
            (as stored in the [stations] section). An error will be displayed
            if there are no stations configured, or if s is an invalid station.
            Since configuration option requirements vary by station type, an
            error is shown if the existing stype is not defined (probably
            because of a borked config file). Once the station is identified,
            AS_CMD_SECTION_STATION's main run loop is entered.
        """

        stations = self.config.items('stations', raw=True)

        if not self.config.has_section('stations'):
            print ""
            print "ERROR: No stations configured. Type 'add_station <station label>'."
            print ""
            return

        if s == '':
            print ""
            print 'Select a station to edit:'
            s = self.rawInput(choices=self.config.options('stations'))
            if isinstance(s, bool):
                return s

        else:

            if not self.config.has_option('stations', s):
                print ""
                print "ERROR: Invalid station '%s' entered. Type 'edit_station' to list stations." % s
                print ""
                return

        stationID = self.config.getint('stations', s)

        sectionName = 'station%d' % stationID

        stype = False
        if self.config.has_section(sectionName):
            if self.config.has_option(sectionName, 'stype'):
                stype = self.config.get(sectionName, 'stype')

            if not stype in mod_ws_app.STYPE_CLASS_LOOKUP:
                print ""
                print "ERROR: Existing station type '%s' is invalid." % stype
                print ""
                stype = False
        
        if stype == False:    
            # Prompt for stype
            stype = self._selectStationType()
            if isinstance(stype, bool):
                return stype

        # Configure the station
        self._setup(AS_CMD_SECTION_STATION, sectionName, '', stype=stype)

        


    def help_add_station(self):
        print ""
        print "add_station <station label>"
        print "    Create a new station in [stations] section and assign it a new ID."
        print "    You will be prompted to select a station type and then set the station's options."
        print ""

    def do_add_station(self, s):
        """
        Add a new station identified by label s. A nested AS_CMD_SECTION_STATION object
        is used to configure the station options.

        @param s string - Display an error if s is empty or contains spaces.
            If not stations have been configured, create the [stations] section of the config.
            Get the next incremental station ID integer, and set the station label in the
            [stations] section. Prompt the user to select an stype for the station, and
            then instantiate a AS_CMD_SECTION_STATION object and call that object's
            set command to prompt user to enter option values for the new station.
        """

        import re

        if s == '':
            print ""
            print 'ERROR: Station label is required.'
            print ""
            return

        if re.match(' ', s):
            print ""
            print "ERROR: Station label cannot contain spaces ('%s'" % s
            print ""
            return

        if not self.config.has_section('stations'):
            self.config.add_section('stations')
        
        stations = self.config.items('stations', raw=True)

        # Get new station ID
        previousStationID = 0
        maxID = 0
        for (sLabel, stationID) in stations:
            stationID = int(stationID)
            maxID = max(stationID, previousStationID)
            if s == sLabel:
                print ""
                print "ERROR: Station '%s' already exists with ID %d" % (sLabel, stationID)
                print ""
                print "Try 'edit_station %s'" % sLabel
                print ""
                return

        nextStationID = maxID + 1

        # Create the station option in [stations]
        self.config.set('stations', s, str(nextStationID))
        print ""
        print "OKAY: Station '%s' created with new ID %d" % (s, nextStationID)
        print ""

        # Prompt for stype
        stype = self._selectStationType()
        if isinstance(stype, bool):
            return stype

        # Configure the station
        sectionName = 'station%d' % nextStationID
        self._setup(AS_CMD_SECTION_STATION, sectionName, 'all', stype=stype)


    def _selectStationType(self):
        """ Helper to prompt user to select a station type from the legal list """
        choices = []
        for atype in mod_ws_app.STYPE_CLASS_LOOKUP:
            choices.append(atype)

        print "Select a station type (enter the corresponding number, or enter cancel):"
        return self.rawInput(choices=choices)


    def help_save(self):
        print ""
        print 'save <file>'
        print '    Save configuration setup to a <file>. If <file> is omitted, default location (%s) is used.' % self.config.filePath
        print ""

    def do_save(self, s):
        """
        Write config contents to a file. An error will be displayed if the file cannot be written.

        @param s string - If empty, then default config file path is used. Otherwise, s should
            specify the path where the file should be saved.
        """

        if s == '':
            s = self.config.filePath

        try:
            self.config.writeToPath(s)
            print ""
            print "OKAY: File '%s' saved." % s
            print ""
        except mod_ws_config_app.AS_CONFIGPARSER_EXCEPTION as e:
            if e.code == mod_ws_config_app.AS_CONFIGPARSER_ERROR_CODES.fileExists:
                print ""
                print "ERROR: Could not save file. File '%s' exists." % s
                print ""
                print "Try 'save <file>' with a different file name or change"
                print "to edit mode with 'mode edit' and try 'save %s'" % s
                print "again to overwrite existing file."
                print ""



    modes = ['edit', 'new']

    def help_mode(self):
        print ""
        print 'mode'
        print "    Display the current mode ('%s')" % self.config.mode
        print 'mode <mode>'
        print "    Change mode to <mode>. Valid modes: %s" % ', '.join(self.modes)
        print ""

    def do_mode(self, s):
        """
        Set the config mode. This affects the flow of the wizard and the config write
        handling (verbosity).

        @param s string - If empty then current mode is displayed, else mode is checked against
            valid modes and then set.
        """

        if s == '':
            print "Current mode is '%s'." % self.config.mode
            return
    
        if not s in self.modes:
            print "Invalid mode '%s'. Valid modes: %s" % (s, ', '.join(self.modes))
        else:
            self.config.mode = s




class AS_CMD_SECTION_ABSTRACT(AS_CMD_ABSTRACT):
    """
    @brief Extend AS_CMD_ABSTRACT to do more config section-related stuff.

    This class can be subclassed to provide nested sub-command routines for configuring
    an individual section ([section]).
    """

    _prompt = 'abstract'
    _suppress = []

    def __init__(self, config, parentCommand=None, section='abstract', prompt='abstract'):
        """
        @brief Initialize the section config Cmd

        Set some object properties and makes sure the config has the
        section defined.  Then load in default values for section options
        that have a default.

        Child classes should be sure to call super().__init__() in
        their __init__()

        @param config AS_CONFIGPARSER object - the config parser used to
            read/write config files, and hold option values
        @param parentCommand optional AS_CMD_ABSTRACT object - for nested
            operations
        @param section str - Name of the section in the config object/file.
            Children should set this.
        @param prompt str - String to be used in the Cmd prompt to notify the
            user that we are editing this section. Children should set this
        """

        super(AS_CMD_SECTION_ABSTRACT, self).__init__(config, parentCommand)

        self.section = section
        self.prompt = prompt

        if not self.config.has_section(self.section):
            self.config.add_section(self.section)

        self.loadDefaults()



    def loadDefaults(self):
        """ Load section default values for options """

        noOption = {'boolean': False}
        for o in self.options:
            noOption['boolean'] = False
            v = self.getConfigValue(o, noOption, self.defaultsConfig)
            if noOption['boolean'] == False:
                self.config.set(self.section, o, v)



    def preloop(self):
        """ Display some help text before entering the main loop """

        self.help_set()
        print ""
        print "Type 'exit' to leave this section and return to the main configuration."
        print "Type 'help' ? to get a complete list of commands"
        print ""


        
    def help_explain(self):
        """ Run paretn's help_explain() and then print some sub-class specific info. """
        super(AS_CMD_SECTION_ABSTRACT, self).help_explain()
        print "explain <option>"
        print "    See an explanation of <option> in [%s]" % self.section
        print ""


    def help_set(self):
        """ Explain set command and show which options can be set in this section. """

        print ""
        print "set"
        print "    Loop through each option and enter its value"
        print ""
        print "set <option> <value>"
        print "    Set value of <option> in [%s] section to <value>." % self.section
        print "    <value> may be _current to keep current value."
        print "    For some options <value> may be 'None'."
        print ""
        print "    The following options are availabile in [%s]:" % self.section
        print ""

        for o in self.options:

            oInfo = self.getOptionInfo(o)

            showCurrent = False
            if oInfo['current'] is None:
                showCurrent = True
            elif len(oInfo['current']) > 0:
                showCurrent = True

            if showCurrent:
                print '        - %s = %s (%s)' % (o, oInfo['current'], oInfo['help'])
            else:
                print '        - %s (%s)' % (o, oInfo['help'])

        print ""




    
    def do_set(self, s):
        """
        Set section option value(s).

        @parm s string - If s is empty, then loop through all options in this
            section and prompt for a value. User may be prompted for a text
            value or to select from a list of values (or both), depending on
            the option. If s is in the form 'option value' then that option is
            set. Otherwise, an error is displayed.
        """

        if s == '':

            print ""
            print "Set the value for each option in section [%s]." % self.section
            print ""

            # iterate over options and prompt for value
            for o in self.options:

                if o in self._suppress:
                    continue

                oInfo = self.getOptionInfo(o)

                # Define choices to select from
                choices = []
                currentValueLabel = oInfo['current']
                if oInfo['noCurrent'] == False:
                    currentValueLabel = "current value ('%s')" % oInfo['current']
                    choices.append(currentValueLabel)

                if not oInfo['current'] is None:
                    if oInfo['types'][0] is None:
                        choices.append('None')

                typeString =''
                if oInfo['typesString']:
                    typeString = 'of type %s ' % oInfo['typesString']

                instructions = 'Enter '
                if len(choices) > 0:
                    instructions = "Select value for %s:" % o
                    allowOther = "Enter a new value %sfor %s:" % (typeString, o)
                else:
                    instructions = "Enter a value %sfor %s:" % (typeString, o)
                    allowOther = ''

                print ""
                print "[%s] %s" % (self.section, o)
                print "    %s" % oInfo['help']
                print ""
                print ""

                print instructions
                prompt = '%s%s = ' % (self.prompt, o)
                s = self.rawInput(prompt, choices=choices, allowOther=allowOther)
                if isinstance(s, bool):
                    return bool

                if s == currentValueLabel:
                    s = oInfo['current']

                # Use the set command to set the value.
                l = self.precmd('set %s %s' % (o, s))
                r = self.onecmd(l)
                r = self.postcmd(r, l)

            print ""
            print "OKAY: Done with section [%s]." % self.section
            print ""

            return True


        # s was not '', so handle command argument
        parts = s.strip().split(' ')
        if len(parts) < 1:
            print ""
            print "ERROR: Command must be in the form of 'set <option> <value>'."
            print ""
            return


        v = ' '.join(parts[1:])
        if v == "_current":
            v = self.getConfigValue(parts[0])

        if v == 'None':
            v = None

        # Do it! set the value.
        self.config.set(self.section, parts[0], v)

        print ""
        print "OKAY: %s set to '%s'\n" % (parts[0], v)
        print ""



    def getOptionInfo(self, option):
        """
        @brief Get information for a section option. 

        Package up the results of self.getConfigValue(),
        self.getTypeString(), and self.getOptionHelp() into a dict object.

        @parm option str - The name of the option.

        @return dict - {
            current: current value of the section option
            types: list of types supported by the option
            typesString: user-friendly string representation of types
            help: string description of section option
            noCurrent: True if there is no current value for the option, else False
            }
        """

        noCurrent = {'boolean': False}

        info = {}
        info['current'] = self.getConfigValue(option, noOption=noCurrent)

        if isinstance(self.options[option], str):
            info['types'] = []
            info['typesString'] = ''
            info['help'] = self.options[option]
        else:
            info['types'] = self.options[option]
            info['typesString'] = self.getTypeString(info['types'])
            h = self.getOptionHelp(option)
            if h == '':
                info['help'] = '%s' % info['typesString']
            else:
                info['help'] = '%s - %s' % (info['typesString'], h)

        # Make sure type is always a list
        if not isinstance(info['types'], list):
            info['types'] = [info['types']]

        info['noCurrent'] = noCurrent['boolean']

        return info



    def getOptionHelp(self, option):
        """
        Get the help string for the option from the 'explain' file.

        @parm option str - The name of the option.

        @return str
        """

        return self.getConfigValue(option, config=self.explainConfig)
        


    def getTypeString(self, types):
        """
        Create user-friendly string representation of the given types (e.g. 'None, int or str').

        @parm types mixed - a type or a list of types

        @return str
        """
        if not isinstance(types, list):
            return self.getTypeName(types)
        l = len(types)
        if l == 1:
            return self.getTypeName(types[0])
        elif l == 0:
            return ''
        else:
            t = [[],'']
            for i in types:
                t[0].append(self.getTypeName(i))
            t[1] = t[0].pop()
            t[0] = ', '.join(t[0]) 
            return ' or '.join(t)



    def getTypeName(self, aType):
        """
        Get the string name of type.

        @param aType type

        @return str
        """
        try:
            return aType.__name__ 
        except AttributeError as e:
            return str(aType)



    def getConfigValue(self, option, noOption={}, config=None):
        """
        Get the value of section option from a configuration object using super().getConfigValue()

        @parm option str - The name of the option.
        @param noOption optional dict - the dict attribute 'boolean' will be set to True if the option
            does not exist in the section config, else False
        @param config optional AS_CONFIGPARSER object - If not provided, super().getConfigValue()
            will use self.config. If the option is not defined you may get back an empty string
            and you can use noOption['boolean'] to check the existance of option.

        @return str
        """

        return super(AS_CMD_SECTION_ABSTRACT, self).getConfigValue(self.section, option, noOption, config)




class AS_CMD_SECTION_APP(AS_CMD_SECTION_ABSTRACT):
    """
    @brief A Cmd sub-class for the [app] section of config.

    Instantiate as a sub-routine of the config setup Cmd.

    Defines the section name as well as the options and their supported types.
    """

    _prompt = 'app'
    section = 'app'
    options = OrderedDict([
        ('dataFolder', str)
        ])

class AS_CMD_SECTION_DB(AS_CMD_SECTION_ABSTRACT):
    """
    @brief A Cmd sub-class for a [database] section of config.

    Instantiate as a sub-routine of the config setup Cmd.

    Defines the section options and their supported types.

    Section name should be passed into the constructor
    as there can be several [databas_*] sections and
    this class handles them all.
    """

    _prompt = 'database'
    section = 'database'
    options = OrderedDict([
        ('host', str),
        ('user', str),
        ('password', str),
        ('database', str)
        ])

class AS_CMD_SECTION_FTP(AS_CMD_SECTION_ABSTRACT):
    """
    @brief A Cmd sub-class for the [ftp] section of config.

    Instantiate as a sub-routine of the config setup Cmd.

    Defines the section name as well as the options and their supported types.
    """

    _prompt = 'ftp'
    section = 'ftp'
    options = OrderedDict([
        ('host', str),
        ('username', str),
        ('password', str),
        ('path', str)
        ])

class AS_CMD_SECTION_NETATMO(AS_CMD_SECTION_ABSTRACT):
    """
    @brief A Cmd sub-class for the [netatmo] section of config.

    Instantiate as a sub-routine of the config setup Cmd.

    Defines the section name as well as the options and their supported types.

    Not to be confused with Netatmo station sections. All station
    sections are handled by AS_CMD_SECTION_STATION.
    """

    _prompt = 'netatmo'
    section = 'netatmo'
    options = OrderedDict([
        ('clientID', str),
        ('clientSecret', str),
        ('username', str),
        ('password', str),
        ('oldestTimestamp', str)
        ])

class AS_CMD_SECTION_STATION(AS_CMD_SECTION_ABSTRACT):
    """
    @brief A Cmd sub-class for the [station*] sections of config.

    Instantiate as a sub-routine of the config setup Cmd.

    Station sections are more dynamic than other sections.
    There can be multiple [station*] sections,
    and the options available in each varies depending
    on the station type (stype).

    Section name should be passed into the constructor
    as there can be multiple [station*] sections and
    this class handles them all.

    Station type should also be passed into the constructor
    so we can set ourselves up properly for that stype.

    Station section options (and there supported types)
    are not defined here. They are retrieved from the
    as_weatherstation.app module.
    """

    _prompt = 'station*'
    section = 'station*'
    _suppress = ['stype']

    def __init__(self, config, parentCommand=None, section="station*", prompt="station*", stype=""):
        """
        @brief Override the parent __init__ to do [station*] related things.

        Store the station type (stype), figure out what class of station we are and get
        the section option specification from that class. Then call super().__init__()

        We also set the stype option in our section of config. This option should be
        suppressed whenever we are prompting for input (the user already chose an stype
        and it cannot be changed).

        @param config AS_CONFIGPARSER object - the config parser used to
            read/write config files, and hold option values
        @param parentCommand optional AS_CMD_ABSTRACT object - for nested
            operations
        @param section str - Name of the section in the config object/file.
        @param prompt str - String to be used in the Cmd prompt to notify the
            user that we are editing this section.
        """

        # Set our station type
        self.stype = stype

        # Get the class of this stype
        sclass = mod_ws_app.STYPE_CLASS_LOOKUP[self.stype]

        # Get the option spec for stype
        self.options = sclass.optionsSpec()

        super(AS_CMD_SECTION_STATION, self).__init__(config, parentCommand, section, prompt)

        self.config.set(self.section, 'stype', self.stype)




    def loadDefaults(self):
        """
        @brief Load station option defaults into config

        Station defaults do not come from the <self.section> section in
        app-defaults.cfg. Instead, [stations] in app-defaults.cfg should
        contain an option matching the self.stype. This option's value should
        point to the section that has the defaults for this type of station.
        """

        # Cache the name of the [station*] section so we don't have to look it up again.
        if not hasattr(self, 'defaultsSection'):
            self.defaultsSection = self.getStationClassSection(self.defaultsConfig)

        # If no pointer to station defaults section, then we can't do much.
        # TODO: we could throw an error here, as the section should exist for full functionality, but maybe the section has no defaults?
        if not self.defaultsSection:
            return

        # Get the option default values from self.defaultsConfig
        noOption = {'boolean': False}
        for o in self.options:
            noOption['boolean'] = False
            v = AS_CMD_ABSTRACT.getConfigValue(self, section=self.defaultsSection, option=o, noOption=noOption, config=self.defaultsConfig)
            if noOption['boolean'] == False:
                self.config.set(self.section, o, v)



    def getOptionHelp(self, option):
        """
        @brief Get the help string for the option from the 'explain' file. Overrides the parent method.

        As with defaults, the help text for station options does not come from the self.section section.
        Instead, [stations] in app-explain.cfg should contain an option matching the self.stype.
        This option's value should point to the section that has the explanations for this type of station.

        @param option str - The name of the option.

        @return str
        """

        # Cache the name of the [station*] section so we don't have to look it up again.
        if not hasattr(self, 'explainSection'):
            self.explainSection = self.getStationClassSection(self.explainConfig)

        # If no pointer to station explain section, then we can't do much.
        if not self.explainSection:
            return

        return AS_CMD_ABSTRACT.getConfigValue(self, section=self.explainSection, option=option, config=self.explainConfig)



    def getStationClassSection(self, config):
        """
        @brief Get the [station*] pointer form the option matching our stype in [stations] of config.

        This is with explainConfig and defaultsConfig to get the station
        option explanations and default values respectivley for our
        station type (stype).
        """

        v = AS_CMD_ABSTRACT.getConfigValue(self, section='stations', option=self.stype, config=config)

        if not v:
            return False

        return 'station%d' % int(v)

