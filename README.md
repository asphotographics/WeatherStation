WeatherStation
==============

Weather Station Python Project


Background
====
Last year I started bulding a Phidget-based autonomous weather station 
for my family's property. I started designing the software in Python.
I needed not only a logger, but also a way to moved log files off of
the weather station whenever a network connection becomes available
(basically when I show up and turn on my iPhone's Personal Hotspot
feature). Then, I would need to load the log data into a database,
do some analysis, and generate a dynamic webapp front-end.

What started out as a few simple scripts was starting to get more
complicated.

Then, I purchased a Netatmo Weather Station for my home in the city.
The Netatmo is great, logging all data to the cloud, and very mobile
friendly. I like to own my data though, so I planned to create a
script to archive the Netatmo data by downloading periodically from
the Netatmo API.

Well, the short-story is, I decided to create a more full-featured
and flexible Python-based weather station suite of applications.


Introdution
====

The Weather Station Python Project has the following primary goals:

- support any number of weather stations from different manufacturers
- be flexible: allow data to be stored, moved, managed,
  and shared in different ways

To this end the the project focuses on several key components:

- stations: a weather station installation which captures and logs
  measurement data from any number of instruments.
  
- I/O modules: I settled on a read/write paradigm for moving data
  around. For example, the following modules have been created or
  are planned:
  
    - read:
      - Phidget Interface Sensor input
      - Netatmo API measurements
      - csv log files
      - MySQL database
      - FTP server archive
      - socket file stream (planned)
      
    - write
      - csv log file
      - Phidget TextLCD display
      - MySQL database 
      - FTP server archive
      - HTTP AJAX/JSON output (in progress)
      - socket file stream (planned)
      - Upload samples to wunderground API (in progress)
      - Upload samples to OpenWeatherMap API  (planned)
      
- controllers: These scripts put it all together. There is no one
  Weather Station program. Each controller performs a particular
  task using the IO modules.
  
  For examples, the controller_pws_main.py
  can be run as a daemon to periodically sample the Phidget IFK
  sensors and respond to Phidget digitial IO events, and then save sample
  measurements to a log file. It could easily be extended to log direclty
  to a DB instead, or to the wunderground.com API.
  
  Another example: the controler_nws_archive.py can be run periodically
  (via cron or launchd) to downlad your recent Netatmo Weather Station
  data from the Netatmo API and write that data to a log file.
  
  The possiblities and combinations are almost endless. One can use as
  much or as little of the functionality as required by their
  situation. The code-base can handle one station, or dozens.
  
The code understands and supports all the measurement types of the
Netatmo outdoor and indoor modules (temperatur, humidity, pressure,
CO2, and noise). I will add support for the Netatmo Rain Gauge as
soon as I receive mine. The home-made Phidget-based weather station
generates most of these measurements as well. Basically, if a station
outputs something (such as a solar radiation measurement), I will
support it.

Due to the limited resources of the Phidget Single Board Computer I am
using for my home-made weather station, I have limited my use of a
database. Currenlty, all configuration information is stored in
text file. I have built robust configuration management command-line
tool (controller_config.py) to create and update the config file.
With wizard-like prompts, it helps you setup your stations
and any server information required. As I build more of the front-end
web-app functionality I will likely move or duplicated some of the
configuration int the DB. However, I don't want to make this an either
or proposition. A weather station sans database access should be able to
work side-by-side with the web-based reporting tools.

The Weather Station Python Project is very much in its infancy. Consider
the code-base alpha-quality, nearing beta-quality.


Wishlist
====
Add support for other stations types:
  - Davis Vantage-seris
  - AirPi
  
  
