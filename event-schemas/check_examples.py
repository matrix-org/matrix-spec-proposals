#! /usr/bin/env python

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


def check_example_file(examplepath, schemapath):
    with open(examplepath) as f:
        example = yaml.load(f)

    with open(schemapath) as f:
        schema = yaml.load(f)

    fileurl = "file://" + os.path.abspath(schemapath)

    print ("Checking schema for: %r %r" % (examplepath, schemapath))
    # Setting the 'id' tells jsonschema where the file is so that it
    # can correctly resolve relative $ref references in the schema
    schema['id'] = fileurl
    try:
        jsonschema.validate(example, schema)
    except:
        raise ValueError("Error validating JSON schema for %r %r" % (
            examplepath, schemapath
        ), e)


def check_example_dir(exampledir, schemadir):
    for root, dirs, files in os.walk(exampledir):
        for filename in files:
            examplepath = os.path.join(root, filename)
            schemapath = examplepath.replace(exampledir, schemadir)
            check_example_file(examplepath, schemapath)


if __name__ == '__main__':
    check_example_dir("examples", "schema")
