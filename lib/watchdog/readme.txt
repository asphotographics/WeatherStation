launchd Directory
--------------

This directory contains check/repair scripts that can be used witht the Linux watchdog daemon. The watchdog daemon can be used to monitor the Phidget Weather Station controller
daemons.

http://linux.die.net/man/8/watchdog
http://linux.die.net/man/5/watchdog.conf

To use, configure the watchdog daemon to run [test-binary] every [interval] seconds and to wait forever for it to exit.

echo "test-binary = /usr/userapps/pws/lib/watchdog/pws_main.sh" >> /etc/watchdog.conf
echo "test-timeout = 0" >> /etc/watchdog.conf
echo "interval = 30" >> /etc/watchdog.conf

The /usr/userapps/pws/lib/watchdog/ check/repair scripts are designed to run for a long time (e.g., an hour) and to test the controller daemons intermittently (e.g., every minute). As long as everything okay they will run until their time ends, whereon watchdog starts them afresh. If a problem is detected and cannot be repaired then they exit with a non-zero status, thus letting watchdog know that something is wrong and a reboot is required.

The minimum intrerval for a watchdog check is 60 seconds. If this seems to aggressive, or for any other reason you do not want to use watchdog, then the crondog.sh can can be used instead to execute the checks/repairs.


Configuring watchdog
----

## Remove the auto-starts for watchdog while you set things up.
# If you get soemthing wrong, having watchdog launch at startup could cause
# infinite reboots. you would then have to enter recovery mode to disable
# watchdog.
ls -l /etc/rc?.d/*watchdog*
rm /etc/rc?.d/*watchdog*
/etc/init.d/watchdog stop

## Edit the watchdog.cong file
cp /usr/userapps/pws/lib/watchdog/watchdog.conf-sample etc/watchdog.conf

echo "test-binary = /usr/userapps/pws/lib/watchdog/pws_main.sh" >> /etc/watchdog.conf
echo "test-timeout = 0" >> /etc/watchdog.conf
echo "interval = 30" >> /etc/watchdog.conf

## Test
# make sure everything is working before you enable watchdog at startup

/etc/init.d/watchdog start

## Enable watchdog at start up
update-rc.d watchdog defaults
ls -l /etc/rc?.d/*watchdog*

