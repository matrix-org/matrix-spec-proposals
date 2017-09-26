#!/usr/bin/env python

# Runs an HTTP server on localhost:8000 which will serve the generated swagger
# JSON so that it can be viewed in an online swagger UI.

# Copyright 2016 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import SimpleHTTPServer
import SocketServer

# Thanks to http://stackoverflow.com/a/13354482
class MyHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_my_headers()
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)

    def send_my_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")


if __name__ == '__main__':
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--port', '-p',
        type=int, default=8000,
        help='TCP port to listen on (default: %(default)s)',
    )
    parser.add_argument(
        'swagger_dir', nargs='?',
        default=os.path.join(scripts_dir, 'swagger'),
        help='directory to serve (default: %(default)s)',
    )
    args = parser.parse_args()

    os.chdir(args.swagger_dir)

    httpd = SocketServer.TCPServer(("localhost", args.port),
                                   MyHTTPRequestHandler)
    print "Serving at http://localhost:%i/api-docs.json" % args.port
    httpd.serve_forever()
