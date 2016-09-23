#!/usr/bin/python
#
# Code by Tony Bussieres <t.bussieres@gmail.com> inspired by 
# 40-convert_to_tcx.py by Gustav Tiger <gustav@tiger.name>
#
# This helper uses GcpUploader to send the fit files to Garmin Connect
# 
# To install GcpUploader:
#
# sudo pip install GcpUploader
#
# edit the file ~/.guploadrc and add the following
# [Credentials]
# username=yourgarminuser
# password=yourgarminpass
#
# Then point the GUPLOAD environment variable at the path to your gupload.py
# script (defaults to /usr/bin/gupload.py)
#
# Don't forget to make this script executable :
#
# chmod +x /path/to/40-upload_to_garmin_connect.py

from __future__ import absolute_import, print_function

import errno
import os
import subprocess
import sys

gupload = os.getenv("GUPLOAD") or "/usr/bin/gupload.py"
if not os.path.exists(gupload):
    sys.stderr.write("%s didn't exist; ensure GcpUploader is installed, "
                     "and set GUPLOAD correctly if necessary.\n")
    sys.exit(1)

def main(action, filename):

    if action != "DOWNLOAD":
        return 0

    try:
        process = subprocess.Popen([gupload, filename], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (data, _) = process.communicate()
    except OSError as e:
        print("Could not send to Garmin", gupload, \
              "-", errno.errorcode[e.errno], os.strerror(e.errno))
        return -1

    if process.returncode != 0:
        print("gupload.py exited with error code", process.returncode)
        return -1

    if data.find("Status: SUCCESS ") != -1:
        print("Successfully uploaded %s to Garmin Connect" % filename)
        return 0

    if data.find("Status: EXISTS ") != -1:
        print("%s already uploaded to Garmin Connect" % filename)
        return 0

    print("Couldn't understand output from uploading %s to Garmin Connect:" %
          filename)
    print(data)
    return -1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

