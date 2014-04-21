#!/bin/bash

INIT_DIR="/etc/init.d"

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
    #        handle_watchdog_daemon_check -d path -n name [test]
    #        handle_watchdog_daemon_check -d path -n name [repair]
    #
    # -d  the path to the daemon executable
    # -n  name of the daemon as defined in its /etc/init.d/ script
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

        # repair requested
        repair)
            repair_for_watchdog "$daemon_name"
            status="$?"
            ;;

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
    exit $status
}

