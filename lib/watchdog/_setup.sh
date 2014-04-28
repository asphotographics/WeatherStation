#!/bin/bash

if [ ! -d "/etc/init.d" ]; then
    echo "ERROR: $0 will install watchdog scripts on Linux systems that use the initd startup system."
    echo "ERROR: /etc/init.d is not accessible and may not be available on this operating system."
    exit 1
fi

test -x /usr/sbin/watchdog
if [ $? -ne 0 ]; then
    echo "ERROR: Watchdog does not appear to be installed on this system."
    echo "ERROR: Cannot continue watchdog script installation."
    exit 2
fi

ORIG_WD=`pwd`

SCRIPT_DIR=`dirname "$0"`
DIR=`readlink -fn "$SCRIPT_DIR/../.."`

####
# Setup watchdog
####

# Check to see what daemons are installed
DAEMONS=`ls /etc/init.d/{pws,ws_,nws_}* 2> /dev/null`
if [ ${#DAEMONS[@]} -eq 0 ]; then
    echo "ERROR: No weather station daemon init scripts appear to be installed in /etc/init.d"
    echo "ERRRO: Cannot continue watchdog script installation."
    exit 3
fi

echo ""
echo "Do you want to configure the watchdog test scripts? [Y/n]"
read ANSWER

if [ $ANSWER = "Y" ]; then

    # Stop watchdog and prevent it from running at startup
    echo "Stopping watchdog..."
    echo `/etc/init.d/watchdog stop`
    echo `update-rc.d -f watchdog remove`

    # Create the watchdog test directory if not exists
    watchdog_d="/etc/watchdog.d"
    do_watchdog=1
    echo -ne "Checking '$watchdog_d'..."
    if [ -d $watchdog_d ]; then
        echo "exists."
    else
        mkdir -p "$watchdog_d"
        if [ $? -eq 0 ]; then
            echo "created."
        else
            do_watchdog=0
            echo "failed to create."
            echo "WARNING: Cannot configure watchdog."
        fi
    fi

    # Configure watchdog.conf and link test executables
    if [ $do_watchdog -eq 1 ]; then

        WATCHDOG_LIB="$DIR/lib/watchdog"
        WATCHDOG_CONF="/etc/watchdog.conf"

        # Copy the exalpe conf file to /etc
        echo "Copying example watchdog.conf to '$WATCHDOG_CONF'"
        cp --backup=numbered "$WATCHDOG_LIB/watchdog.conf" "$WATCHDOG_CONF"

        # Modify /etc/watchdog.conf
        sed -i -r -e "/^[[:space:]]*test-directory/d" "$WATCHDOG_CONF"
        echo "Adding test-directory = $watchdog_d to '$WATCHDOG_CONF'"
        echo "test-directory = $watchdog_d" >> "$WATCHDOG_CONF"
        sed -i -r -e "/^[[:space:]]*interval/d" "$WATCHDOG_CONF"
        echo "Adding interval = 30 to '$WATCHDOG_CONF'"
        echo "interval = 30" >> "$WATCHDOG_CONF"
        sed -i -r -e "/^[[:space:]]*test-timeout/d" "$WATCHDOG_CONF"
        echo "Adding test-timeout = 0 to '$WATCHDOG_CONF'"
        echo "test-timeout = 0" >> "$WATCHDOG_CONF"

        # Link the test executables into the /etc/watchdog.d
        tests=("pws_main.sh" "pws_display.sh")
        for i in ${tests[@]}; do
            test_src="$DIR/lib/watchdog/$i"
            test_link="$watchdog_d/$i"
            rm -f "$test_link"
            if [ -f $test_src ]; then

                # The test script should have the same name as the daemon,
                # minus the .sh extension. Check if daemon is installed.
                daemon_name=`echo "$i" | sed -e "s/\.sh//"`
                if [ -e "/etc/init.d/$daemon_name" ]; then
                    echo "Linking '$test_src' to '$test_link'"
                    ln -s "$test_src" "$test_link"
                else
                    echo ""
                    echo "WARNING: Daemon '/etc/init.d/$daemon_name' for test '$test_src' does not appear to be installed."
                    echo ""
                    echo "Press 'enter' to continue..."
                    read
                fi

            else
                echo ""
                echo "WARNING: Test script '$test_src' not found"
                echo ""
                echo "Press 'enter' to continue..."
                read
            fi
        done

        # Tell the user how to test, start, and enable watchdog
        echo ""
        echo "Done setup of watchdog."
        echo ""
        echo "Please thoroughly test the executables in '$watchdog_d'." 
        echo "For example, do..."
        echo "  $watchdog_d/$i test || echo \$?"
        echo "and..."
        echo "  $watchdog_d/$i repair || echo \$?"
        echo "After test executables have been checked you can start watchdog with:"
        echo "  /etc/init.d/watchdog start"
        echo "If that seems stable, only then should you enable watchdog at startup with:"
        echo "  /usr/sbin/update-rc.d watchdog defaults"
        echo ""
        echo "Press 'enter' to continue..."
        read
         
    fi

fi



exit 0
