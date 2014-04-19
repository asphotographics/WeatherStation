#!/usr/local/bin/python
# coding: utf-8

""" A collection of general utility functions. """

def getInterfaces():
    """
    Get the IP addresses of the network interfaces

    @return list of dicts - each dict item containing interface, ip, and mac attributes
    """

    import subprocess, re

    regex = re.compile("^((eth|en|wlan)\d+).*(HWaddr|ether) ([^ ]+).*(addr:|inet )([^ ]+)", re.MULTILINE|re.DOTALL)

    interfaces = []
    for interface in ['en0', 'en1', 'eth0', 'wlan0']:

        try:
            a = subprocess.check_output('ifconfig %s' % interface, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            continue
            
        result = regex.match(a)

        if result != None:
            interF = result.group(1)
            mac = result.group(4)
            ip = result.group(6)

            interfaces.append({'interface': interF, 'ip': ip, 'mac': mac})

    return interfaces

