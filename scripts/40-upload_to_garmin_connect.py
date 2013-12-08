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
# Then change the gupload path  (See CHANGEME in the code)
#
# Don't forget to make this script executable :
#
# chmod +x /path/to/40-upload_to_garmin_connect.py


import errno
import os
import subprocess
import sys

# CHANGE ME:
gupload = "/path/to/bin/gupload.py"

def main(action, filename):

    if action != "DOWNLOAD":
        return 0

    try:
        process = subprocess.Popen([gupload, filename], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        (data, _) = process.communicate()
    except OSError as e:
        print "Could not send to Garmin", gupload, \
              "-", errno.errorcode[e.errno], os.strerror(e.errno)
        return -1

    if process.returncode != 0:
        print "gupload.py exited with error code", process.returncode
        return -1
    print "Successfully uploaded %s to Garmin Connect" % (filename);
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

