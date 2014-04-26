WeatherStation - File Layout
==============

Directories and files within the root directory of the Weather Station Python Project are organized as follows:

Top-level folder
====

- README.md `- General overview of the project`
- README-layout.md `- this file`
- app-sample.cfg `- a sample configuration file`
- app.cfg `- the current configuration (generate with controller_config.py, or copy and edit app-sample.cfg)`
- app.pth `- list paths that should be added to sys.path (for Python module imports)`

`The main program executables are in the root directory and are prefixed "controller_":`
- controller_config.py `- config creation and management controller`
- controller_log_dbload.py `- load log file data into the database`
- controller_log_download.py `- download log files from the FTP server to "[data]/log/downloaded/"`
- controller_log_rotate.py `- backup the active log file and start a new one`
- controller_log_upload.py `- upload backup log files to the FTP server`
- controller_netatmo_archive.py `- dowload data from the Netatmo API and store in a log file`
- controller_pws_display.py `- Phidget Weather Station: display recent log data on an attached TextLCD`
- controller_pws_main.py `- Phidget Weather Station: sample sensors and monitor digital inputes, writing data to a log file at regular intervals`

- schema.sql `- Database schema`

as_nws sub-folder
====

as_nws/: `- Package containing Netatmo weather station -specific modules`
- \_\_init\_\_.py `- Tells Python to treat this directory as a package`
- app.py `- The main application class for the Netatmo weather station`

as_nws/controller/: `- Controller sub-modules for the Netatmo weather station`
- \_\_init\_\_.py
- archive.py `- Archive controller class`

as_pws sub-folder
====

as_pws/: `- Package containing Phidget Weather Station -specific modules`
- \_\_init\_\_.py
- app.py

as_pws/controller: `- Controller sub-modules for the Phidget Weather Station`
- \_\_init\_\_.py
- display.py `- Display controller class`
main.py `- Main controller class`

as_weatherstation sub-folder
====

as_weatherstation/: `- Package containing general weather station modules and base-classes`
- \_\_init\_\_.py `- Configures the sys.path using site.addsitedir()`
- app.py `- The main application classes for all weather stations`
- util.py `- Basic utility functions`

as_weatherstation/config/: `- Configuration sub-module`
- \_\_init\_\_.py
- app-defaults.cfg `- Configuration containing default values used by the config controller`
- app-explain.cfg `- Configuration containing explainations of the options available in the config controller`
- app.py `- configuration class pertaining to the main application (loads and manages /app.cfg or the database configuration contents)`
- log.py `- configuration class for setting up logging`

as_weatherstation/controller/: `- General weather station controller sub-module`
- \_\_init\_\_.py
- abstract.py `- Abstract base class (not really an ABC, but meant to be extended not instantiated)`
- config.py `- Configuration controller class`

as_weatherstation/controller/log/: `- Log controller sub-module`
- \_\_init\_\_.py
- dbload.py `- Controller to read log data from a file and write to the database`
- download.py `- Controller to download remote log files from the FTP server`
- rotate.py `- Controller to cause the rotation of the active log file`
- upload.py `- Controller to upload backup log files to the FTP server and then move the files to the "uploaded" folder`

as_weatherstation/log/: `- Sub-modules that work with the built-in Python logging module`
- \_\_init\_\_.py
- dbhandler.py `- A logging handler which writes data to a MySQL database - see as_weatherstation/config/log.py`
- error.py `- Functions related to the as_weatherstation.log.error logger - see as_weatherstation/config/log.py`
- message.py `- Functions related to the as_weatherstation.log.message logger - see as_weatherstation/config/log.py`
- timestamp.py `- Functions related to the as_ws.log.timestamp_* loggers - see as_weatherstation/config/log.py`
- weather.py `- Functions related to the as_ws.log.weather_* loggers - see as_weatherstation/config/log.py`

as_weatherstation/netatmo/: `- Netatmo API sub-modules`
- \_\_init\_\_.py
- error.py `- Netatmo API error handler`
- lnetatmo.py `- Wrapper library for talking to the Netatmo API`

as_weatherstation/phidget/: `- Phidget I/O sub-modules`
- \_\_init\_\_.py
- lphidget.py `- Wrapper library for talking to a Phidget InterfaceKit or TextLCD`

as_weatherstation/read/: `- Data read sub-modules`
- \_\_init\_\_.py
- abstract.py `- Abstract reader class`
- csvfile.py `- Class which reads from a CSV file`
- log.py `- Class which reads from a log file`
- netatmo.py `- Class which reads from the Netatmo API`
- pws.py `- Class which reads from the Phidget Interface Kit`

as_weatherstation/write/: `- Data write sub-modules`
- \_\_init\_\_.py
- abstract.py `- Abstract writer class`
- db.py `- Class which writes data to MySQL via the logging dbhandler`
- log.py `- Class which writes data to a file via a logging handler`
- textlcd.py `- Class which displays data on a Phidget TextLCD via the lphidget.py library`

data sub-folder
====

data/: `- Data, such as log files and messages, are stored here. The folder location can be configured in app.cfg`
- error.txt `- Error messages related to controller execution. Rotated according to rules in as_weatherstation/log/config.py`
- messages.txt `- Info messages related to controller execution. Rotated according to rules in as_weatherstation/log/config.py`

data/log/ `- Data sub-folder containing weather station logs`

data/log/downloaded/ `- Data sub-folder containing remote logs downloaded from the FTP server to this instance`

data/log/imported/ `- Data sub-folder containing logs which have been imported into the database`

data/log/uploaded/ `- Data sub-folder containing logs which have been uploaded to the FTP server from this instance`


lib sub-folder
====

lib/ `- Library folder containing supporting scripts`

lib/initd/: `- Startup scripts compatible with the Debian init system (which is what the PhidgetSBC runs)`
- controller_log_upload.sh `- Log upload daemon init script`
- controller_pws_display.sh `- Phidget Weather Station TextLCD display daemon init script`
- controller_pws_main.sh `- Phidget Weather Station interfaceKit daemon init sript`
- readme.txt 

lib/launchd/: `- Startup scripts compatible with the OS X launchd system`
- com.springerphotographics.ws.log_download.plist `- Log download luanchd plist`
- readme.txt

lib/site-packages/: - 
- ftputil `- High-level Python FTP client library by Stefan Schwarzer - https://pypi.python.org/pypi/ftputil/`

lib/watchdog/: `- Scripts compatible with the Linux watchdog system monitoring daemon`
- crondog.sh `- Schedule check scripts with cron instead of watchdog`
- functions.sh `- Function library used by check scripts`
- path_to_python_weather_station_dir.sh `- Contains a variable pointing to the weather station installation path`
- pws_main.sh `- Check script: test if controller_pws_main is running and if not restart it`
- readme.txt
- watchdog.conf-sample `- Sample watchdog.conf file which can be copied to /etc/watchdog.conf`
