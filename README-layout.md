# WeatherStation - File Layout #
==============

Directories and files within the root directory of the Weather Station Python Project are organized as follows:

## Top-level folder ##
====

- README.md `- General overview of the project`
- README-layout.md `- this file`
- app-sample.cfg `- a sample configuration file`
- app.cfg `- the current configuration (generate with controller_config.py, or copy and edit app-sample.cfg)`
- app.pth `- list paths that should be added to sys.path (for Python module imports)`

`The main program executables are in the root directory and are prefixed "controller_":`
- controller\_config.py `- config creation and management controller`
- controller\_log\_dbload.py `- load log file data into the database`
- controller\_log\_download.py `- download log files from the FTP server to "[data]/log/downloaded/"`
- controller\_log\_rotate.py `- backup the active log file and start a new one`
- controller\_log\_upload.py `- upload backup log files to the FTP server`
- controller\_netatmo\_archive.py `- dowload data from the Netatmo API and store in a log file`
- controller\_pws\_display.py `- Phidget Weather Station: display recent log data on an attached TextLCD`
- controller\_pws\_main.py `- Phidget Weather Station: sample sensors and monitor digital inputs, writing data to a log file at regular intervals`
- schema.sql `- Database schema`


## as\_nws sub-folder ##
====

as\_nws/: `- Package containing Netatmo weather station -specific modules`
- \_\_init\_\_.py `- Tells Python to treat this directory as a package`
- app.py `- The main application class for the Netatmo weather station`

as\_nws/controller/: `- Controller sub-modules for the Netatmo weather station`
- \_\_init\_\_.py
- archive.py `- Archive controller class`


## as\_pws sub-folder ##
====

as\_pws/: `- Package containing Phidget Weather Station -specific modules`
- \_\_init\_\_.py
- app.py

as\_pws/controller: `- Controller sub-modules for the Phidget Weather Station`
- \_\_init\_\_.py
- display.py `- Display controller class`
- main.py `- Main controller class`


## as\_weatherstation sub-folder ##
====

as\_weatherstation/: `- Package containing general weather station modules and base-classes`
- \_\_init\_\_.py `- Configures the sys.path using site.addsitedir()`
- app.py `- The main application classes for all weather stations`
- util.py `- Basic utility functions`

as\_weatherstation/config/: `- Configuration sub-module`
- \_\_init\_\_.py
- app-defaults.cfg `- Configuration containing default values used by the config controller`
- app-explain.cfg `- Configuration containing explainations of the options available in the config controller`
- app.py `- configuration class pertaining to the main application (loads and manages /app.cfg or the database configuration contents)`
- log.py `- configuration class for setting up logging`

as\_weatherstation/controller/: `- General weather station controller sub-module`
- \_\_init\_\_.py
- abstract.py `- Abstract base class (not really an ABC, but meant to be extended not instantiated)`
- config.py `- Configuration controller class`

as\_weatherstation/controller/log/: `- Log controller sub-module`
- \_\_init\_\_.py
- dbload.py `- Controller to read log data from a file and write to the database`
- download.py `- Controller to download remote log files from the FTP server`
- rotate.py `- Controller to cause the rotation of the active log file`
- upload.py `- Controller to upload backup log files to the FTP server and then move the files to the "uploaded" folder`

as\_weatherstation/log/: `- Sub-modules that work with the built-in Python logging module`
- \_\_init\_\_.py
- dbhandler.py `- A logging handler which writes data to a MySQL database - see as_weatherstation/config/log.py`
- error.py `- Functions related to the as_weatherstation.log.error logger - see as_weatherstation/config/log.py`
- message.py `- Functions related to the as_weatherstation.log.message logger - see as_weatherstation/config/log.py`
- timestamp.py `- Functions related to the as_ws.log.timestamp_* loggers - see as_weatherstation/config/log.py`
- weather.py `- Functions related to the as_ws.log.weather_* loggers - see as_weatherstation/config/log.py`

as\_weatherstation/netatmo/: `- Netatmo API sub-modules`
- \_\_init\_\_.py
- error.py `- Netatmo API error handler`
- lnetatmo.py `- Wrapper library for talking to the Netatmo API`

as\_weatherstation/phidget/: `- Phidget I/O sub-modules`
- \_\_init\_\_.py
- lphidget.py `- Wrapper library for talking to a Phidget InterfaceKit or TextLCD`

as\_weatherstation/read/: `- Data read sub-modules`
- \_\_init\_\_.py
- abstract.py `- Abstract reader class`
- csvfile.py `- Class which reads from a CSV file`
- log.py `- Class which reads from a log file`
- netatmo.py `- Class which reads from the Netatmo API`
- pws.py `- Class which reads from the Phidget Interface Kit`

as\_weatherstation/write/: `- Data write sub-modules`
- \_\_init\_\_.py
- abstract.py `- Abstract writer class`
- db.py `- Class which writes data to MySQL via the logging dbhandler`
- log.py `- Class which writes data to a file via a logging handler`
- textlcd.py `- Class which displays data on a Phidget TextLCD via the lphidget.py library`


## data sub-folder ##
====

data/: `- Data, such as log files and messages, are stored here. The folder location can be configured in app.cfg`
- error.txt `- Error messages related to controller execution. Rotated according to rules in as_weatherstation/log/config.py`
- messages.txt `- Info messages related to controller execution. Rotated according to rules in as_weatherstation/log/config.py`

data/log/ `- Data sub-folder containing weather station logs`

data/log/downloaded/ `- Data sub-folder containing remote logs downloaded from the FTP server to this instance`

data/log/imported/ `- Data sub-folder containing logs which have been imported into the database`

data/log/uploaded/ `- Data sub-folder containing logs which have been uploaded to the FTP server from this instance`


## lib sub-folder ##
====

lib/ `- Library folder containing supporting scripts`

lib/initd/: `- Startup scripts compatible with the Debian init system (which is what the PhidgetSBC runs)`
- \_setup.sh `- Script which configures and installs init scripts`
- ws\_log\_upload.sh `- Log upload daemon init script`
- pws\_display.sh `- Phidget Weather Station TextLCD display daemon init script`
- pws\_main.sh `- Phidget Weather Station interfaceKit daemon init sript`
- readme.txt 

lib/launchd/: `- Startup scripts compatible with the OS X launchd system`
- com.springerphotographics.ws.log\_download.plist `- Log download luanchd plist`
- readme.txt

lib/pws/: `- Scripts for managing a Phidget Weather Station instance`
- install_sbc.sh `- Script to install and configure application files, binaries, packages, Python modules, init scripts, watchdog scripts, etc., on a PhidgetSBC`
- start_sbc.sh `- Utility script which starts the application daemons and check scripts running on a PhidgetSBC`
- start_sbc.sh `- Utility script which stops the application daemons and check scripts running on a PhidgetSBC`

lib/site-packages/: - 
- ftputil `- High-level Python FTP client library by Stefan Schwarzer - https://pypi.python.org/pypi/ftputil/`

lib/watchdog/: `- Scripts compatible with the Linux watchdog system monitoring daemon`
- \_functions.sh `- Function library used by check scripts`
- \_setup.sh `- Script which configures watchdog and installs check scripts`
- crondog.sh `- Schedule check scripts with cron instead of watchdog`
- pws\_display.sh `- Check script: test if daemon pws_display is running and if not restart it`
- pws\_main.sh `- Check script: test if daemon pws_main is running and if not restart it`
- readme.txt
- watchdog.conf `- Sample watchdog.conf file which can be copied to /etc/watchdog.conf (modified and installed automatically by _setup.sh)`
