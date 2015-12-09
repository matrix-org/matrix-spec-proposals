#!/usr/bin/env python2

# dump-swagger reads all of the swagger API docs used in spec generation and
# outputs a JSON file which merges them all, for use as input to a swagger UI
# viewer.
# See https://github.com/swagger-api/swagger-ui for details of swagger-ui.

import errno
import json
import os.path
import re
import shutil
import sys

templating_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templating")
sys.path.insert(0, templating_dir)
os.chdir(templating_dir)

from matrix_templates.units import resolve_references, MatrixUnits

if len(sys.argv) < 2 or len(sys.argv) > 3:
    sys.stderr.write("usage: %s output_directory [client_release_label]\n" % (sys.argv[0],))
    sys.exit(1)

output_directory = sys.argv[1]
release_label = sys.argv[2] if len(sys.argv) > 2 else "unstable"

major_version = release_label
match = re.match("^(r\d)+(\.\d+)*$", major_version)
if match:
    major_version = match.group(1)

apis = MatrixUnits().load_swagger_apis()

output = {
    "basePath": "/_matrix/client/" + major_version,
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "host": "localhost:8008",
    "info": {
        "title": "Matrix Client-Server API",
        "version": release_label,
    },
    "paths": {},
    "swagger": "2.0",
}

for file, contents in apis.items():
    for path, methods in contents["paths"].items():
        for method, spec in methods.items():
            if "tags" in spec.keys():
                if path not in output["paths"]:
                    output["paths"][path] = {}
                output["paths"][path][method] = spec

path = os.path.join(output_directory, "api-docs")
try:
    os.makedirs(os.path.dirname(path))
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

with open(path, "w") as f:
    text = json.dumps(output, sort_keys=True, indent=4)
    text = text.replace("%CLIENT_RELEASE_LABEL%", release_label)
    text = text.replace("%CLIENT_MAJOR_VERSION%", major_version)
    f.write(text)
