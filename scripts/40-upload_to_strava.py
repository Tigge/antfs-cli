#!/usr/bin/env python3
#
# Code by Matheus Cansian <dev@drpexe.com>
#
# This helper uses stravalib to send the fit files to Strava
#
# To install stravalib
#
# sudo pip install stravalib
#
# This script uses a third party API to facilitate Strava's OAuth
# authentication. If you want to deploy your own API you can use
# the instructions below and change the constants on this script.
# https://github.com/mscansian/drpexe-uploader
#
# You can fetch the credentials by running the script without any arguments
#
# ./40-upload_to_strava.py
#
# Credentials are written to ~/.drpexe-uploader-credentials
#
# Don't forget to make this script executable :
#
# chmod +x /path/to/40-upload_to_strava.py
from __future__ import print_function, with_statement

import sys
import os.path

try:
    from urllib.parse import urlparse
    from http.server import HTTPServer, BaseHTTPRequestHandler
except ImportError:  # Python 2.7
    from urlparse import urlparse
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from stravalib import Client
from stravalib.exc import ActivityUploadFailed, AccessUnauthorized

# drpexe-uploader config
# https://github.com/mscansian/drpexe-uploader
# do not change unless you want to create your own strava app
DRPEXE_CLIENT_ID = 17666
DRPEXE_UPLOADER_API = (
    'https://in27m0omnk.execute-api.us-east-1.amazonaws.com/prod'
)

STRAVA_CREDENTIALS_FILE = os.path.expanduser('~/.drpexe-uploader-credentials')
STRAVA_UPLOAD_PRIVATE = False
LOCAL_SERVER_PORT = 8000


def main(action, filename):
    if action != "DOWNLOAD":
        return 0

    try:
        with open(STRAVA_CREDENTIALS_FILE, 'r') as f:
            access_token = f.read().strip(' \t\n\r')
    except FileNotFoundError:
        print('No Strava credentials provided.')
        print('You first need to run the script to fetch the credentials')
        print('./40-upload_to_strava.py')
        return -1

    try:
        client = Client(access_token=access_token)
        client.get_athlete()
    except AccessUnauthorized:
        print('Your token has expired. Starting authentication flow\n')
        return -2

    try:
        print('Uploading {}: '.format(os.path.basename(filename)), end='')
        with open(filename, 'rb') as f:
            upload = client.upload_activity(
                activity_file=f,
                data_type='fit',
                private=STRAVA_UPLOAD_PRIVATE,
            )
    except (ActivityUploadFailed, FileNotFoundError) as err:
        print('FAILED')
        print('Reason:', err)
        return -1

    print('SUCCESS')
    return 0


def start_strava_auth_flow():
    print('---------------------------------------------')
    print('| Starting Strava OAuth authentication flow |')
    print('---------------------------------------------\n')

    client = Client()
    url = client.authorization_url(
        client_id=DRPEXE_CLIENT_ID,
        redirect_uri=DRPEXE_UPLOADER_API,
        scope='activity:write',
        state='REDIRECT-%s' % LOCAL_SERVER_PORT,
    )
    print('Open the following page to authorize drpexe-uploader to '
          'upload files to your Strava account\n')
    print(url)

    httpd = HTTPServer(('127.0.0.1', LOCAL_SERVER_PORT), AuthRequestHandler)
    httpd.handle_request()


class AuthRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        querystring = urlparse(self.path).query
        key, value = querystring.split('=')
        assert key == 'access_token'

        # Write credentials to disk
        with open(STRAVA_CREDENTIALS_FILE, 'w') as f:
            f.write(value)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(
            (
                'This message means you have been successfully authenticated.'
                '\n\nYou can now close this page.'
            ).encode("utf-8")
        )
        print('Authentication succeeded')
        print('Credentials have been saved to %s' % STRAVA_CREDENTIALS_FILE)


if __name__ == "__main__":
    if len(sys.argv) != 1:
        while True:
            return_code = main(action=sys.argv[1], filename=sys.argv[2])
            if return_code == -2:
                start_strava_auth_flow()
                continue  # Authentication failed
            sys.exit(return_code)
    start_strava_auth_flow()
    sys.exit(0)
