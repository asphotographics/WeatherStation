launchd Directory
--------------

This directory contains launchd plist files that can be used in conjuction with the
OS X launchd daemon/agent startup system.

The launchd system can be used to start and monitor long-running controllers, like controller_pws_main.py. It can also be used to periodically run short-lived scripts, like controller_log_dbload.py, that quit after performing specific task and do not need to stay running. In the latter case, launchd is a replacement for the older cron system.

The Apple Developer pages describe the launchd system and daemon/agent plist parameters:

https://developer.apple.com/library/mac/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html#//apple_ref/doc/uid/10000172i-SW7-BCIEDDBJ

If you create your own luanchd plists, make sure to add an environemnet variable for LANG (en_CA.UTF-8, or whatever echo $LANG at the command-line would return). This will for sure be needed by the ftputil package.