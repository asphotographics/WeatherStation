#! /bin/bash

# This script can be used as an alternative to the Linux watchdog daemon.
# Cron this script to run periodically, passing it the names of
# watchdog scripts to run. See usage for more details.

scriptname=$0
reboot_=1
OPTIND=1

# Parse the -d and -n options from the function arguements.
while getopts ":d" opt ; do
    case "$opt" in
        d) reboot_=0;;
    esac
done


# Shift $@ over n positions, thus dropping the -d and -n options
# and leaving everything else.
shift $(($OPTIND - 1))

if [ $# -eq 0 ]; then
    echo "Usage: $scriptname [-d] watchdogscript [watchdogscript [..]]"
    echo ""
    echo "   -d              - If this option is set, the we will not reboot on error."
    echo "   watchdogscript  - absolute path to a script to run, or name of scipt in lib/watchdog"
    echo ""
    echo "Each script is run in turn. If a script fails then a message is logged in syslog."
    echo "If -d is not set, then a reboot will occur if any script exits with a non-zero status."
    echo "To support reboot, the script must be run as root."
    exit 1
fi


status=0

# Move to the lib/watchdog directory so we can load scipts simply by name
dir=`dirname $0`
cd "$dir"

# Loop through all the given scripts
for i in "$@"; do

    # If script does not exist, then ignore it
    if [ ! -f "$i" ]; then
        echo "Unknown script: $i" >&2
        continue
    fi

    # Execute the script and get its exit status
    /bin/bash "$i"
    status=$?

    # Status is non-zero, then log a message in syslog
    if [ $status -ne 0 ]; then
        if [ $reboot_ -eq 1 ]; then
            # If reboot is true, then after loggin error start the reboot proceess and exit
            logger -s -p "cron.error" "$0 failed with $i: rebooting now"
            reboot
            exit 1
        else
            # If reboot is false, then log error, and continue execution with next script
            logger -s -p "cron.error" "$0 failed with $i"
        fi
    fi
done
