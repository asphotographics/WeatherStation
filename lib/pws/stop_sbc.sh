stop_daemons()
{
    local init

    # Loop through daemon names and execute the stop command
    for i in $@; do
        init="/etc/init.d/$i"
        if [ -f "$init" ]; then
            "$init" stop 2> /dev/null
        fi
    done
}

stop_watchers()
{
    local lockfile processes lastPID

    # Loop through the watcher processes
    for i in $@; do
        lockfile="/var/run/$i.pid"
        if [ -f "$lockfile" ]; then
            # If .pid file is found then send process a TERM signal
            read lastPID < $lockfile
            echo "Sending SIGTERM to $i (process ID $lastPID)"
            kill -n 15 $lastPID
        else
            # If no .pid found, print a list of matching processes
            processes=`ps -C "$i" -o pid=,stat=`
            echo "No .pid file found for $i"
            if [ -n "$processes" ]; then
                echo "But the following running processes match:"
                echo "$processes"
            fi
        fi
    done
}

# Stop the PWS init daemons and watchers (order is important)

# 1) Stop watchdog first or system may repair itself or reboot
to_stop=("watchdog")
stop_daemons ${to_stop[@]}

# 2) Stop watchers so they don't try to restart the controllers
to_stop=("pws_main.sh" "pws_display.sh")
stop_watchers ${to_stop[@]}

# 3) Stop the controller daemons last
to_stop=("ws_log_upload" "pws_display" "pws_main")
stop_daemons ${to_stop[@]}
