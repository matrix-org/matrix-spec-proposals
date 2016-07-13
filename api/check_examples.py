#! /usr/bin/env python
#
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

import sys
import json
import os


def import_error(module, package, debian, error):
    sys.stderr.write((
        "Error importing %(module)s: %(error)r\n"
        "To install %(module)s run:\n"
        "  pip install %(package)s\n"
        "or on Debian run:\n"
        "  sudo apt-get install python-%(debian)s\n"
    ) % locals())
    if __name__ == '__main__':
        sys.exit(1)

try:
    import jsonschema
except ImportError as e:
    import_error("jsonschema", "jsonschema", "jsonschema", e)
    raise

try:
    import yaml
except ImportError as e:
    import_error("yaml", "PyYAML", "yaml", e)
    raise


def check_parameter(filepath, request, parameter):
    schema = parameter.get("schema")
    example = None
    try:
        example_json = schema.get('example')
        if example_json and not schema.get("format") == "byte":
            example = json.loads(example_json)
    except Exception as e:
        raise ValueError("Error parsing JSON example request for %r" % (
            request
        ), e)
    fileurl = "file://" + os.path.abspath(filepath)
    if example and schema:
        try:
            print ("Checking request schema for: %r %r" % (
                filepath, request
            ))
            # Setting the 'id' tells jsonschema where the file is so that it
            # can correctly resolve relative $ref references in the schema
            schema['id'] = fileurl
            resolver = jsonschema.RefResolver(filepath, schema, handlers={"file": load_yaml})
            jsonschema.validate(example, schema, resolver=resolver)
        except Exception as e:
            raise ValueError("Error validating JSON schema for %r" % (
                request
            ), e)


def check_response(filepath, request, code, response):
    example = None
    try:
        example_json = response.get('examples', {}).get('application/json')
        if example_json:
            example = json.loads(example_json)
    except Exception as e:
        raise ValueError("Error parsing JSON example response for %r %r" % (
            request, code
        ), e)
    schema = response.get('schema')
    fileurl = "file://" + os.path.abspath(filepath)
    if example and schema:
        try:
            print ("Checking response schema for: %r %r %r" % (
                filepath, request, code
            ))
            # Setting the 'id' tells jsonschema where the file is so that it
            # can correctly resolve relative $ref references in the schema
            schema['id'] = fileurl
            resolver = jsonschema.RefResolver(filepath, schema, handlers={"file": load_yaml})
            jsonschema.validate(example, schema, resolver=resolver)
        except Exception as e:
            raise ValueError("Error validating JSON schema for %r %r" % (
                request, code
            ), e)


def check_swagger_file(filepath):
    with open(filepath) as f:
        swagger = yaml.load(f)

    for path, path_api in swagger.get('paths', {}).items():

        for method, request_api in path_api.items():
            request = "%s %s" % (method.upper(), path)
            for parameter in request_api.get('parameters', ()):
                if parameter['in'] == 'body':
                    check_parameter(filepath, request, parameter)

            try:
                responses = request_api['responses']
            except KeyError:
                raise ValueError("No responses for %r" % (request,))
            for code, response in responses.items():
                check_response(filepath, request, code, response)


def load_yaml(path):
    if not path.startswith("file:///"):
        raise Exception("Bad ref: %s" % (path,))
    path = path[len("file://"):]
    with open(path, "r") as f:
        return yaml.load(f)


if __name__ == '__main__':
    paths = sys.argv[1:]
    if not paths:
        paths = []
        for (root, dirs, files) in os.walk(os.curdir):
            for filename in files:
                if filename.endswith(".yaml"):
                    paths.append(os.path.join(root, filename))
    for path in paths:
        try:
            check_swagger_file(path)
        except Exception as e:
            raise ValueError("Error checking file %r" % (path,), e)
