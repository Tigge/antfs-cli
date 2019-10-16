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

import pickle
import sys
import os.path
import xdg.BaseDirectory

try:
    from urllib.parse import urlparse, parse_qs
    from http.server import HTTPServer, BaseHTTPRequestHandler
except ImportError:  # Python 2.7
    from urlparse import urlparse, parse_qs
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from stravalib import Client
from stravalib.exc import ActivityUploadFailed

# drpexe-uploader config
# https://github.com/mscansian/drpexe-uploader
# do not change unless you want to create your own strava app
CLIENT_ID = 39902
CLIENT_SECRET = '44dfaeb5510f81137ff73286be6c1e876759907f'

STRAVA_CREDENTIALS_FILE = os.path.join(xdg.BaseDirectory.save_data_path('antfs-cli'), 'strava-credentials')
STRAVA_UPLOAD_PRIVATE = False


def main(action, filename):
    if action != "DOWNLOAD":
        return 0

    try:
        with open(STRAVA_CREDENTIALS_FILE, 'rb') as f:
            token_data = pickle.load(f)
            access_token = token_data['access_token']
    except (FileNotFoundError, KeyError):
        print('No Strava credentials provided.')
        print('You first need to run the script to fetch the credentials')
        print('./40-upload_to_strava.py')
        return -1

    try:
        client = Client(access_token=access_token)
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

    httpd = HTTPServer(('127.0.0.1', 0), AuthRequestHandler)

    client = Client()
    url = client.authorization_url(
        client_id=CLIENT_ID,
        redirect_uri='http://{}:{}'.format('localhost', httpd.server_port),
        scope='activity:write',
    )
    print('Open the following page to authorize drpexe-uploader to '
          'upload files to your Strava account\n')
    print(url)

    httpd.handle_request()


class AuthRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        querystring = urlparse(self.path).query
        params = parse_qs(querystring)

        client = Client()
        token_data = client.exchange_code_for_token(client_id=CLIENT_ID,
                                                    client_secret=CLIENT_SECRET,
                                                    code=params['code'][0])

        # Write credentials to disk. Use the simplest pickle protocol
        # to keep it human-readable.
        with open(STRAVA_CREDENTIALS_FILE, 'wb') as f:
            pickle.dump(token_data, f, 0)

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
        sys.exit(main(action=sys.argv[1], filename=sys.argv[2]))
    start_strava_auth_flow()
    sys.exit(0)
