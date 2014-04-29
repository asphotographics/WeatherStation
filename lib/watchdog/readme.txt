watchdog Directory
--------------

This directory contains check/repair scripts that can be used with the Linux watchdog daemon. The watchdog daemon can be used to monitor the Phidget Weather Station controller daemons.

http://www.sat.dundee.ac.uk/psc/watchdog/watchdog-configure.html

http://linux.die.net/man/8/watchdog
http://linux.die.net/man/5/watchdog.conf


To use, configure the watchdog daemon to run [test-directory] binaries every [interval] seconds and to wait forever for them to exit.

echo "test-directory=/etc/watchdog.d" >> /etc/watchdog.conf
echo "test-timeout = 0" >> /etc/watchdog.conf
echo "interval = 30" >> /etc/watchdog.conf

The lib/watchdog/ check scripts can then be symbolicly link to from /etc/watchdog.d. For example:

cd /etc/watchdog.d
ln -s /usr/userapps/pws/lib/watchdog/pws_main.sh pws_main.sh

The lib/watchdog check/repair scripts are designed to run for a long time (e.g., an hour) and to test the controller daemons intermittently (e.g., every minute). As long as everything okay they will run until their time ends, whereon watchdog starts them afresh. If a problem is detected and cannot be repaired then they exit with a non-zero status, thus letting watchdog know that something is wrong and a reboot is required.

The lib/watchdog check/repair scripts can be run in test-binary mode or test-directory mode. In the former, watchdog calls the script without any arguements (if a test fails, a repair is automatically performed, if that fails, then the  system is rebooted). In the latter mode, watchdog first calls the script with a test argument (e.g., `/etc/watchdog.d/pws_main.sh test`). If a non-zero exit status is generated (meaning the test failed), then the same executable is called with a repair arguementd (e.g., `/etc/watchdog.d/pws_main.sh repair`). If the repair fails and a non-zero exit status is generated, then the system is rebooted.

The minimum intrerval for a watchdog check is 60 seconds. If this seems to aggressive, or for any other reason you do not want to use watchdog, then crondog.sh can can be used instead to execute the checks/repairs via the cron scheduler.

_setup.py can be used to configure and install watchdog and the check scripts.
