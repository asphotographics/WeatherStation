#!/bin/bash

# This script can be used by watchdog as either a test-binary or as binary
# in the test-directory. See the following pages for more info:
# http://linux.die.net/man/8/watchdog
# http://linux.die.net/man/5/watchdog.conf


# Replace this with the name of the daemon (as found in /etc/init.d) you want to check/tests/repair.
DAEMON_NAME="pws_display"

DIR=`/etc/init.d/$DAEMON_NAME directory`
DAEMON=`/etc/init.d/$DAEMON_NAME daemon`

# Get the dirname of this script
MY_DIR="$DIR/lib/watchdog"

# Include some functions
. $MY_DIR/_functions.sh

# See the documentation for run_loop and handle_watchdog_daemon_check in _functions.sh
run_loop -n 60 -i 60 "handle_watchdog_daemon_check -d \"$DAEMON\" -n \"$DAEMON_NAME\" \"$@\" >> /dev/null"

exit 0
