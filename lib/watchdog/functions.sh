#!/bin/bash

# Inlcude some init-related functions
. /lib/lsb/init-functions

INIT_DIR="/etc/init.d/"

#echo $BASH_SOURCE

test_for_watchdog()
{
    # Run the status_of_proc function to see if the daemon is running.
    #
    # Usage: check_daemon daemon daemon_name
    #
    # - daemon = the path to the daemon executable
    # - daemon_name - name of the daemon as defined in its /etc/init.d/ script

    local daemon daemon_name
    #echo "-check $@"

    daemon="$1"
    daemon_name="$2"

    status_of_proc "$daemon" "$daemon_name"
    return "$?"
}

repair_for_watchdog()
{
    # Execute the daemon's restart command.
    #
    # Usage: repair_for_watchdog daemon_name
    #
    # - daemon_name - name of the init script in /etc/init.d/

    local daemon_name
    #echo "-repair $@"

    daemon_name="$1"

    "$INIT_DIR"/"$1" restart
    return "$?"
}


handle_watchdog_daemon_check()
{
    # Handle watch dog check/test/repair requests.
    # 
    # Usage: handle_watchdog_daemon_check -d path -n name
    #        handle_watchdog_daemon_check -d path -n name test
    #        handle_watchdog_daemon_check -d path -n name repair
    #
    #   -d - the path to the daemon executable
    #   -n - name of the daemon as defined in its /etc/init.d/ script
    #
    # If watchdog is configured with the test-binary option, then it will try
    # to execute a binary file without any arguements. That binary file can
    # call this function with a daemon path and a daemon name and we will
    # check the running status of the daemon and restart it if necessary.
    # If that still fails, then we exit with a non-zero status and watchdog
    # attempts to reboot the system.
    #
    # If watchdog is configured with the test-directory option, then it will
    # try to execute binaries in that folder with the argument "test", and if
    # that fails, with the arguement "repair". A binary in the test-directory
    # can call this function to handle the testing and repair of a daemon.

    local daemon daemon_name status OPTIND

    daemon=
    daemon_name=
    status=0
    OPTIND=1

    # Parse the -d and -n options from the function arguements.
    while getopts "d:n:" opt ; do
        case "$opt" in
            d)  daemon="$OPTARG";;
            n)  daemon_name="$OPTARG";;
        esac
    done

    # Shift $@ over n positions, thus dropping the -d and -n options
    # and leaving everything else.
    shift $(($OPTIND - 1))

    #echo "daemon $daemon $daemon_name $@"

    # Check for the watchdog test or repair command.
    case "$1" in

        # test requested
        test)
            test_for_watchdog "$daemon" "$daemon_name"
            status="$?"
            ;;

        # repair is the same as our default plan (test and then fix)
        #repair)
            #repair_for_watchdog "$daemon_name"
            #exit "$?"
            #;;

        # no command specified, so test and then repair if necessary.
        *)

            if [ -n "$daemon" ] && [ -n "$daemon_name" ] ; then
                # If test returns non-zero, then try repair.
                test_for_watchdog "$daemon" "$daemon_name" || repair_for_watchdog "$daemon_name"
                status="$?"
            fi
            ;;

    esac

    #echo "status $status"

    # If exit status is non-zero, then watchdog will do a reboot.
    [ $status -ne 0 ] && exit $status
}

run_loop()
{
    # Execute a given command inside a run loop
    # 
    # Usage: run_loop [-n iterations] [-i interval] command
    #   -n - Numer of times to loop. Zero = forever.
    #   -i - Interval (seconds) to wait between loop executions.
    #   command - string which will be passed to eval
    get_lock

    local iterations counter interval limit OPTIND

    iterations=100
    counter=0
    interval=60
    limit="$iterations"
    OPTIND=1

    # Parse the -d and -n options from the function arguements.
    while getopts ":n:i:" opt ; do
        case "$opt" in
            n) iterations="$OPTARG";;
            i) interval="$OPTARG";;
        esac
    done


    # Shift $@ over n positions, thus dropping the -d and -n options
    # and leaving everything else.
    shift $(($OPTIND - 1))

    # Set up inifinite loop
    if [ $iterations -eq 0 ]; then
        limit=1
    fi

    # Enter main run loop
    while [  $counter -lt $limit ]; do

        # Evaluter the command
        eval "$@"
        sleep "$interval"

        # If iterations is zero then don't increment counter
        if [ $iterations -gt 0 ]; then
            let counter=counter+1 
        fi

    done

    exit 0
}


GET_LOCK_RAN=0
get_lock()
{
    # Get a lock using .pdf file.
    # 
    # Usage: get_lock
    #
    # This can be used to prevent multiple-instances of a script from
    # being run in parallel. If a lock exists then exit is called
    # with a status of zero.
    #
    # The lockfile is automatically removed prior to exiting and if
    # the script receives any of the following singals: SIGHUP,
    # SIGINT, SIGQUIT, SIGPIPE, SIGTERM.

    local scriptname lockfile

    # Only let get_lock be run once
    [ $GET_LOCK_RAN -gt 1 ]  && return
    GET_LOCK_RAN=1

    # Define the location of the lock
    scriptname=`basename $0`
    lockfile="/var/run/$scriptname.pid"

    # Use a lockfile containing the pid of the running process
    # If script crashes and leaves lockfile around, it will have a
    # different pid so will not prevent script running again.

    # Create empty lock file if none exists
    cat /dev/null >> "$lockfile"
    read lastPID < "$lockfile"

    # There is a race condition between when we read the .pid, check
    # for a running process and then write our .pid. In other
    # words, if scripts are spawned really quickly we may end up with
    # multiple processes running. flock is a better option, but not
    # always installed.
    # 
    # To reduce the likely-hood of a tie we sleep a random amount of
    # time, between 0 and 0.5 seconds. In theory, one script will be
    # the fastest here. Though, I supposed the race still depends on
    # when the scripts were started, so let's forget the sleep.
    #sleep $(awk "BEGIN {printf \"%.4f\",$(($RANDOM%100))/500}")

    # Another lock method is to use a mkdir, which is an atomic
    # operation and returns zero on sucess or some error if the
    # directory could not created (e.g., because it already existed).
    # http://wiki.bash-hackers.org/howto/mutex

    # If lastPID is not null and a process with that pid exists, exit
    [ ! -z "$lastPID" -a -d /proc/$lastPID ] && exit
    #echo not running

    # Save my pid in the lock file
    echo "$$" > "$lockfile"

    # Set up signal traps so we clean up the lock if we are terminated
    trap "[ -f $lockfile ] && /bin/rm -f $lockfile && exit" 0 1 2 3 13 15
}
