#!/usr/bin/python
# encoding=utf-8

import as_pws.controller.display as mod_pws_controller_display

controller = mod_pws_controller_display.AS_CONTROLLER_PWS_DISPLAY()
controller.main('STATION_BAYMAR_OUTDOOR')

def close():
    global controller
    del(controller)

close()
