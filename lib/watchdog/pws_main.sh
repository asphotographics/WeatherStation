#!/bin/bash

# This script can be used by watchdog as either a test-binary or as binary
# in the test-directory. See the following pages for more info:
# http://linux.die.net/man/8/watchdog
# http://linux.die.net/man/5/watchdog.conf

# Get the dirname of this script
MY_DIR=`dirname $0`

# Include some functions
. $MY_DIR/functions.sh

# DEBUGING
echo `date`


# Set the path to your Python Weather Station Application in this script:
. $MY_DIR/path_to_python_weather_station_dir.sh

# Replace these two values with the path and name of the daemon you want
# to check/tests/repair.
DAEMON=$DIR/controller_pws_main.py
DAEMON_NAME=controller_pws_main


# See the documentation for run_loop and handle_watchdog_daemon_check in functions.s
run_loop -n 60 -i 60 "handle_watchdog_daemon_check -d \"$DAEMON\" -n \"$DAEMON_NAME\" \"$@\" >> /dev/null"
exit 0
