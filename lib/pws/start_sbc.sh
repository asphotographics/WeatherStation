start_daemons()
{
    local init

    # Loop through daemon names and execute the start command
    for i in $@; do
        init="/etc/init.d/$i"
        if [ -f "$init" ]; then
            "$init" start
        fi
    done
}

# Start the PWS init daemons and watchers (order is important)


# 1) Start the controller daemons first
to_start=("log_upload" "pws_display" "pws_main")
start_daemons ${to_start[@]}

# 2) Start the watchdog daemon (which will start the test/repair watchers)

echo "Start watchdog daemon? [Y/n]"
read do_watchdog

if [ $do_watchdog = "Y" ]; then
    to_start=("watchdog")
    start_daemons ${to_start[@]}
fi
