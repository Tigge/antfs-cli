#!/usr/bin/env python
#
# Code by Tony Bussieres <t.bussieres@gmail.com>
# Updated by Bastien Abadie <bastien@nextcairn.com>
# inspired by 40-convert_to_tcx.py by Gustav Tiger <gustav@tiger.name>
#
# This helper uses garmin-uploader to send the fit files to Garmin Connect
#
# To install garmin-uploader
#
# sudo pip install garmin-uploader
#
# edit the file ~/.guploadrc and add the following
# [Credentials]
# username=yourgarminuser
# password=yourgarminpass
#
# Don't forget to make this script executable :
#
# chmod +x /path/to/40-upload_to_garmin_connect.py

from __future__ import absolute_import, print_function

import sys
import os.path
import logging

try:
    from garmin_uploader import logger
    from garmin_uploader.user import User
    from garmin_uploader.workflow import Activity
except ImportError:
    print('Python package garmin_uploader is not available. Please install with pip install garmin-uploader')
    sys.exit(1)

# Setup garmin uploader logger
logger.setLevel(logging.INFO)

def main(action, filename):
    assert os.path.exists(filename)

    if action != "DOWNLOAD":
        return 0

    # Auth with ~/.guploadrc credentials
    user = User()
    if not user.authenticate():
        logger.error('Invalid Garmin Connect credentials')
        return -1

    # Upload the activity
    activity = Activity(filename)
    if not activity.upload(user):
        logger.error('Failed to send activity to Garmin')
        return -1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
