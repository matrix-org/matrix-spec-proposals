#!/usr/bin/env python
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
import traceback


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


def check_example_file(examplepath, schemapath):
    with open(examplepath) as f:
        example = yaml.load(f)

    with open(schemapath) as f:
        schema = yaml.load(f)

    fileurl = "file://" + os.path.abspath(schemapath)
    schema["id"] = fileurl
    resolver = jsonschema.RefResolver(schemapath, schema, handlers={"file": load_yaml})

    print ("Checking schema for: %r %r" % (examplepath, schemapath))
    try:
        jsonschema.validate(example, schema, resolver=resolver)
    except Exception as e:
        raise ValueError("Error validating JSON schema for %r %r" % (
            examplepath, schemapath
        ), e)


def check_example_dir(exampledir, schemadir):
    errors = []
    for root, dirs, files in os.walk(exampledir):
        for filename in files:
            if filename.startswith("."):
                # Skip over any vim .swp files.
                continue
            examplepath = os.path.join(root, filename)
            schemapath = examplepath.replace(exampledir, schemadir)
            if schemapath.find("#") >= 0:
                schemapath = schemapath[:schemapath.find("#")]
            try:
                check_example_file(examplepath, schemapath)
            except Exception as e:
                errors.append(sys.exc_info())
    for (exc_type, exc_value, exc_trace) in errors:
        traceback.print_exception(exc_type, exc_value, exc_trace)
    if errors:
        raise ValueError("Error validating examples")


def load_yaml(path):
    if not path.startswith("file:///"):
        raise Exception("Bad ref: %s" % (path,))
    path = path[len("file://"):]
    with open(path, "r") as f:
        return yaml.load(f)


if __name__ == '__main__':
    try:
        check_example_dir("examples", "schema")
    except:
        sys.exit(1)
