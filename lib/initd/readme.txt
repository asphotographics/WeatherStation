initd Directory
--------------

This directory contains shell scripts that can be used in conjuction with the
Linux initd launch system.

In general the scripts use the start-stop-daemon program to daemonize long
running controllers, like controller_pws_main.py.

The following page has a good description of how to use init scripts to 
daemonize Python scripts:

http://blog.scphillips.com/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/

For controllers that need only be run periodically and quit after performing a specific task, such as controller_log_rotate.py, use cron to control the launch interval.