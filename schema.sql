SET character_set_client = utf8;

DROP TABLE as_pws_data_log;
DROP TABLE as_pws_data_hourly;
DROP TABLE as_pws_station;

CREATE TABLE `as_pws_station` (
    `fID` TINYINT UNSIGNED NOT NULL auto_increment,
    `fName` VARCHAR(255) NOT NULL default '',
    `fAltitude` SMALLINT NOT NULL default '0',
    `fLatitude` DECIMAL(8,5) NOT NULL default '0',
    `fLongitude` DECIMAL(8,5) NOT NULL default '0',
    `fDescription` varchar(255) NULL default '',
    PRIMARY KEY (`fID`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

INSERT INTO as_pws_station (fID, fName, fAltitude, fLatitude, fLongitude, fDescription)
VALUES (1, "Baymar - Outdoor", "1060", "51.05945", "-114.10899", "Phidget Weather Station");
INSERT INTO as_pws_station (fID, fName, fAltitude, fLatitude, fLongitude, fDescription)
VALUES (2, "Home - Indoor", "1060", "51.05945", "-114.10899", "Netatmo Indoor Device");
INSERT INTO as_pws_station (fID, fName, fAltitude, fLatitude, fLongitude, fDescription)
VALUES (3, "Home - Outdoor", "1060", "51.05945", "-114.10899", "Netatmo Outdoor Module");

CREATE TABLE `as_pws_data_log` (
    `fID` BIGINT UNSIGNED NOT NULL auto_increment,
    `fStationID` TINYINT UNSIGNED NOT NULL default '0',
    `fSampleDateTime` DATETIME NOT NULL default '0000-00-00 00:00:00',
    `fTemperature` DECIMAL(4,2) NOT NULL default '0',
    `fRelativeHumidity` DECIMAL(5,2) UNSIGNED NOT NULL default '0',
    `fStationBarometricPressure` SMALLINT UNSIGNED NOT NULL default '0',
    `fPrecipitationWeight` SMALLINT UNSIGNED NOT NULL default '0',
    `fInternalTemperature` DECIMAL(4,2) NOT NULL default '0',
    `fCO2` SMALLINT UNSIGNED NOT NULL default '0',
    `fNoise` TINYINT UNSIGNED NOT NULL default '0',
    `fSeaLevelBarometricPressure` SMALLINT UNSIGNED NOT NULL default '0',
    `fPrecipitation` DECIMAL(6,2) unsigned NOT NULL DEFAULT '0.0',
    PRIMARY KEY  (`fID`),
    UNIQUE KEY `StationAndTime` (`fStationID`, `fSampleDateTime`),
    FOREIGN KEY `fStationID` (`fStationID`) REFERENCES `as_pws_station` (`fID`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

CREATE TABLE `as_pws_data_hourly` (
    `fID` BIGINT UNSIGNED NOT NULL auto_increment,
    `fStationID` TINYINT UNSIGNED NOT NULL default '0',
    `fDateTime` DATETIME NOT NULL default '0000-00-00 00:00:00',
    `fTemperature` DECIMAL(4,2) NOT NULL default '0',
    `fRelativeHumidity` DECIMAL(5,2) UNSIGNED NOT NULL default '0',
    `fStationBarometricPressure` SMALLINT UNSIGNED NOT NULL default '0',
    `fPrecipitationWeight` SMALLINT UNSIGNED NOT NULL default '0',
    `fInternalTemperature` DECIMAL(4,2) NOT NULL default '0',
    `fCO2` SMALLINT UNSIGNED NOT NULL default '0',
    `fNoise` TINYINT UNSIGNED NOT NULL default '0',
    `fSeaLevelBarometricPressure` SMALLINT UNSIGNED NOT NULL default '0',
    `fPrecipitation` DECIMAL(6,2) unsigned NOT NULL DEFAULT '0.0',
    `fSampleCount` SMALLINT UNSIGNED NOT NULL default '0',
    PRIMARY KEY (`fID`),
    UNIQUE KEY `StationAndTime` (`fStationID`, `fDateTime`),
    FOREIGN KEY `fStationID` (`fStationID`) REFERENCES `as_pws_station` (`fID`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
