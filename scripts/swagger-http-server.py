#!/usr/bin/env python
#
# Runs an HTTP server on localhost:8000 which will serve the generated swagger
# JSON so that it can be viewed in an online swagger UI.
#

import argparse
import os
import SimpleHTTPServer
import SocketServer

PORT = 8000

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
    parser.add_argument('swagger_dir', nargs='?',
                        default=os.path.join(scripts_dir, 'swagger'))
    args = parser.parse_args()

    os.chdir(args.swagger_dir)

    httpd = SocketServer.TCPServer(("localhost", PORT), MyHTTPRequestHandler)
    print "Serving at http://localhost:%i/api-docs.json" % PORT
    httpd.serve_forever()
