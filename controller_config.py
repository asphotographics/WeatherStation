#!/usr/bin/python
# encoding=utf-8


import as_weatherstation.config.app as mod_ws_config_app
from os.path import isfile

# Running the config controller is the only time that it is acceptable
# to not have an app.cfg file. Since much of the code relies on
# an app object, and the app object expects a valid config,
# we load in the defaults config if app.cfg has not been created yet.
# It is a bit of chicken and egg situation we are in.
#
# This is dangerous, because the defaults config contains junk stations,
# is missing a DB connection, and defines a data path that the
# user may not like. Well, hopefully no other code besides the
# config controller decides to do anything during this execution.
# The sooner we get an app.cfg the better.
if not isfile(mod_ws_config_app.DEFAULT_FILE_PATH):
    mod_ws_config_app._config = mod_ws_config_app.AS_CONFIGPARSER()
    mod_ws_config_app._config.read('as_weatherstation/config/app-defaults.cfg')

import as_weatherstation.controller.config as mod_ws_controller_config

controller = mod_ws_controller_config.AS_CONTROLLER_CONFIG()
controller.main()

