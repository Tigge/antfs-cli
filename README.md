ANT-FS Command Line Interface
=============================

[![Travis branch](https://img.shields.io/travis/Tigge/antfs-cli/master.svg)](https://travis-ci.org/Tigge/antfs-cli)
[![Coveralls branch](https://img.shields.io/coveralls/Tigge/antfs-cli/master.svg)](https://coveralls.io/r/Tigge/antfs-cli?branch=master)

This program (`antfs-cli`, previously Garmin-Forerunner-610-Extractor or
Garmin-Extractor) extracts all activity FIT files from a device and writes
them to a folder (see file locations below). The first time it runs it
attempts to sync with the watch. This produces an `authfile` which is written
to the same folder. On startup this program will try to read that file to
avoid having to re-sync.

Requirements
------------

- [openant >= 0.3](https://github.com/Tigge/openant)

Installation
------------

Run `sudo python setup.py install` to install ANT-FS Command Line Interface. This
will install an `antfs-cli` binary in `/usr/bin` or similar.


Usage
-----

    Usage: antfs-cli [options]

    Options:
      -h, --help  show this help message and exit
      --upload    enable uploading
      --debug     enable debug

Upload to Garmin Connect
------------------------

This program can upload automatically the activities from your watch to [Garmin Connect](https://connect.garmin.com) by using [garmin-uploader](https://github.com/La0/garmin-uploader).

To setup the activity upload, follow these steps:

 1. Install upload extra dependecies
    ```
    sudo pip install antfs-cli[upload]
    ```
 2. Setup your Garmin Connect credentials in `~/.guploadrc`
    ```
    [Credentials]
    username=yourgarminuser
    password=yourgarminpass
    ```
 3. Copy the file `scripts/40-upload_to_garmin_connect.py` into the directory `~/.config/antfs-cli/scripts`
    Make sure it is still executable.

Now after every successful activity download from your watch, the activity will be uploaded to Garmin Connect.

File locations
--------------

### Simple answer (probably correct for most people)

Your files are placed in `~/.config/antfs-cli/`

### Long answer

FIT files and authfiles are stored in an the location specified by the XDG
Base Directory specification. It uses the `$XDG_CONFIG_HOME` with
`$HOME/.config` as backup. In this directory a `antfs-cli` folder is created
in which a folder for each device is created. Both the `.FIT` files and
`authfile` are stored in this device-specific folder. All logs are stored
in a `logs` subfolder of the `antfs-cli` directory.

Supported devices
-----------------

Any device supported by [openant](https://github.com/Tigge/openant) should work.

### ANT USB Sticks

 - [ANTUSB2 Stick](http://www.thisisant.com/developer/components/antusb2/)
 (0fcf:1008: Dynastream Innovations, Inc.)
 - [ANTUSB-m Stick](http://www.thisisant.com/developer/components/antusb-m/)
 (0fcf:1009: Dynastream Innovations, Inc.)

### ANT-FS Devices

Any compliant ANT-FS device should in theory work, but those specific devices
have been reported as working:

 - Garmin Forerunner 60
 - Garmin Forerunner 405CX
 - Garmin Forerunner 310XT
 - Garmin Forerunner 610
 - Garmin Forerunner 910XT
 - Garmin FR70
 - Garmin Swim

Please let me know if you have any success with devices that are not listed here.
