#!/usr/bin/env python2

# dump-swagger reads all of the swagger API docs used in spec generation and
# outputs a JSON file which merges them all, for use as input to a swagger UI
# viewer.
# See https://github.com/swagger-api/swagger-ui for details of swagger-ui.

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


import errno
import json
import logging
import os.path
import re
import shutil
import sys
import yaml

scripts_dir = os.path.dirname(os.path.abspath(__file__))
templating_dir = os.path.join(os.path.dirname(scripts_dir), "templating")
api_dir = os.path.join(os.path.dirname(scripts_dir), "api")

sys.path.insert(0, templating_dir)

from matrix_templates.units import resolve_references, MatrixUnits

if len(sys.argv) > 3:
    sys.stderr.write("usage: %s [output_file] [client_release_label]\n" % (sys.argv[0],))
    sys.exit(1)

if len(sys.argv) > 1:
    output_file = os.path.abspath(sys.argv[1])
else:
    output_file = os.path.join(scripts_dir, "swagger", "api-docs.json")

release_label = sys.argv[2] if len(sys.argv) > 2 else "unstable"

major_version = release_label
match = re.match("^(r\d)+(\.\d+)*$", major_version)
if match:
    major_version = match.group(1)


logging.basicConfig()

os.chdir(templating_dir)
apis = MatrixUnits().load_swagger_apis()

output = {
    "basePath": "/",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "host": "matrix.org:8448",
    "schemes": ["https"],
    "info": {
        "title": "Matrix Client-Server API",
        "version": release_label,
    },
    "securityDefinitions": {},
    "paths": {},
    "swagger": "2.0",
}

with open(os.path.join(api_dir, 'client-server', 'definitions',
                       'security.yaml')) as f:
    output['securityDefinitions'] = yaml.load(f)

for file, contents in apis.items():
    basePath = contents['basePath']
    for path, methods in contents["paths"].items():
        path = (basePath + path).replace('%CLIENT_MAJOR_VERSION%',
                                         major_version)
        for method, spec in methods.items():
            if "tags" in spec.keys():
                if path not in output["paths"]:
                    output["paths"][path] = {}
                output["paths"][path][method] = spec


print "Generating %s" % output_file

try:
    os.makedirs(os.path.dirname(output_file))
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

with open(output_file, "w") as f:
    text = json.dumps(output, sort_keys=True, indent=4)
    text = text.replace("%CLIENT_RELEASE_LABEL%", release_label)
    text = text.replace("%CLIENT_MAJOR_VERSION%", major_version)
    f.write(text)
