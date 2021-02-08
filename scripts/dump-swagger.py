#!/usr/bin/env python3

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

import argparse
import errno
import json
import logging
import os.path
import re
import sys
import yaml


scripts_dir = os.path.dirname(os.path.abspath(__file__))
templating_dir = os.path.join(scripts_dir, "templating")
api_dir = os.path.join(os.path.dirname(scripts_dir), "data", "api")

sys.path.insert(0, templating_dir)

from matrix_templates import units

parser = argparse.ArgumentParser(
    "dump-swagger.py - assemble the Swagger specs into a single JSON file"
)
parser.add_argument(
    "--client_release", "-c", metavar="LABEL",
    default="unstable",
    help="""The client-server release version to generate for. Default:
    %(default)s""",
)
parser.add_argument(
    "-o", "--output",
    default=os.path.join(scripts_dir, "swagger", "api-docs.json"),
    help="File to write the output to. Default: %(default)s"
)
args = parser.parse_args()

output_file = os.path.abspath(args.output)
release_label = args.client_release

major_version = release_label
match = re.match("^(r\d+)(\.\d+)*$", major_version)
if match:
    major_version = match.group(1)

logging.basicConfig()

output = {
    "basePath": "/",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "host": "matrix.org",
    "schemes": ["https"],
    "info": {
        "title": "Matrix Client-Server API",
        "version": release_label,
    },
    "securityDefinitions": {},
    "paths": {},
    "swagger": "2.0",
}

cs_api_dir = os.path.join(api_dir, 'client-server')
with open(os.path.join(cs_api_dir, 'definitions',
                       'security.yaml')) as f:
    output['securityDefinitions'] = yaml.load(f)

for filename in os.listdir(cs_api_dir):
    if not filename.endswith(".yaml"):
        continue
    filepath = os.path.join(cs_api_dir, filename)

    print("Reading swagger API: %s" % filepath)
    with open(filepath, "r") as f:
        api = yaml.load(f.read())
        api = units.resolve_references(filepath, api)

        basePath = api['basePath']
        for path, methods in api["paths"].items():
            path = (basePath + path).replace('%CLIENT_MAJOR_VERSION%',
                                             major_version)
            for method, spec in methods.items():
                if "tags" in spec.keys():
                    if path not in output["paths"]:
                        output["paths"][path] = {}
                    output["paths"][path][method] = spec

print("Generating %s" % output_file)

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
