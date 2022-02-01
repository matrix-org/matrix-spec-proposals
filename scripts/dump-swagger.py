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
api_dir = os.path.join(os.path.dirname(scripts_dir), "data", "api")

def resolve_references(path, schema):
    if isinstance(schema, dict):
        # do $ref first
        if '$ref' in schema:
            value = schema['$ref']
            previous_path = path
            path = os.path.join(os.path.dirname(path), value)
            try:
                with open(path, encoding="utf-8") as f:
                    ref = yaml.safe_load(f)
                result = resolve_references(path, ref)
                del schema['$ref']
                path = previous_path
            except FileNotFoundError:
                print("Resolving {}".format(schema))
                print("File not found: {}".format(path))
                result = {}
        else:
            result = {}

        for key, value in schema.items():
            result[key] = resolve_references(path, value)
        return result
    elif isinstance(schema, list):
        return [resolve_references(path, value) for value in schema]
    else:
        return schema

def prefix_absolute_path_references(text, base_url):
    """Adds base_url to absolute-path references.

    Markdown links in descriptions may be absolute-path references.
    These won’t work when the spec is not hosted at the root, such as
    https://spec.matrix.org/latest/
    This turns all `[foo](/bar)` found in text into
    `[foo](https://spec.matrix.org/latest/bar)`, with
    base_url = 'https://spec.matrix.org/latest/'
    """
    return text.replace("](/", "]({}/".format(base_url))

def edit_links(node, base_url):
    """Finds description nodes and makes any links in them absolute."""
    if isinstance(node, dict):
        for key in node:
            if isinstance(node[key], str):
                node[key] = prefix_absolute_path_references(node[key], base_url)
            else:
                edit_links(node[key], base_url)
    elif isinstance(node, list):
        for item in node:
            edit_links(item, base_url)

parser = argparse.ArgumentParser(
    "dump-swagger.py - assemble the Swagger specs into a single JSON file"
)
parser.add_argument(
    "--base-url", "-b",
    default="https://spec.matrix.org/unstable/",
    help="""The base URL to prepend to links in descriptions. Default:
    %(default)s""",
)
parser.add_argument(
    "--spec-release", "-r", metavar="LABEL",
    default="unstable",
    help="""The spec release version to generate for. Default:
    %(default)s""",
)
available_apis = {
    "client-server": "Matrix Client-Server API",
    "server-server": "Matrix Server-Server API",
    "application-service": "Matrix Application Service API",
    "identity": "Matrix Identity Service API",
    "push-gateway": "Matrix Push Gateway API",
}
parser.add_argument(
    "--api",
    default="client-server",
    choices=available_apis,
    help="""The API to generate for. Default: %(default)s""",
)
parser.add_argument(
    "-o", "--output",
    default=os.path.join(scripts_dir, "swagger", "api-docs.json"),
    help="File to write the output to. Default: %(default)s"
)
args = parser.parse_args()

output_file = os.path.abspath(args.output)
release_label = args.spec_release
selected_api = args.api

major_version = release_label
match = re.match("^(r\d+)(\.\d+)*$", major_version)
if match:
    major_version = match.group(1)

base_url = args.base_url.rstrip("/")

logging.basicConfig()

output = {
    "basePath": "/",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "host": "matrix.org",
    # The servers value will be picked up by RapiDoc to provide a way
    # to switch API servers. Useful when one wants to test compliance
    # of their server with the API.
    "servers": [
        {
            "url": "https://{homeserver_address}/",
            "variables": {
                "homeserver_address": {
                    "default": "matrix-client.matrix.org",
                    "description": "The base URL for your homeserver",
                }
            },
        }
    ],
    "schemes": ["https"],
    "info": {
        "title": available_apis[selected_api],
        "version": release_label,
    },
    "securityDefinitions": {},
    "paths": {},
    "swagger": "2.0",
}

selected_api_dir = os.path.join(api_dir, selected_api)
try:
    with open(os.path.join(selected_api_dir, 'definitions', 'security.yaml')) as f:
        output['securityDefinitions'] = yaml.safe_load(f)
except FileNotFoundError:
    print("No security definitions available for this API")

for filename in os.listdir(selected_api_dir):
    if not filename.endswith(".yaml"):
        continue
    filepath = os.path.join(selected_api_dir, filename)

    print("Reading swagger API: %s" % filepath)
    with open(filepath, "r") as f:
        api = yaml.safe_load(f.read())
        api = resolve_references(filepath, api)

        basePath = api['basePath']
        for path, methods in api["paths"].items():
            path = basePath + path
            for method, spec in methods.items():
                if path not in output["paths"]:
                    output["paths"][path] = {}
                output["paths"][path][method] = spec

edit_links(output, base_url)

print("Generating %s" % output_file)

try:
    os.makedirs(os.path.dirname(output_file))
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

with open(output_file, "w") as f:
    text = json.dumps(output, sort_keys=True, indent=4)
    text = text.replace("%CLIENT_RELEASE_LABEL%", release_label)
    f.write(text)
