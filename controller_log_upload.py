#!/usr/bin/python
# encoding=utf-8

import as_weatherstation.controller.log.upload as mod_ws_controller_log_upload

controller = mod_ws_controller_log_upload.AS_CONTROLLER_LOG_UPLOAD()
controller.count = 0
controller.main()
