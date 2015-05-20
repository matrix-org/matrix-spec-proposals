#!/usr/bin/env python
""" 
Builds the Matrix Specification as restructed text (RST).

Architecture
============
+-------+                            +----------+
| units |-+                          | sections |-+
+-------+ |-+ === used to create ==> +----------- | === used to create ==> SPEC
  +-------+ |                          +----------+
   +--------+
RAW DATA (e.g. json)                  Blobs of RST

Units
=====
Units are random bits of unprocessed data, e.g. schema JSON files. Anything can
be done to them, from processing it with Jinja to arbitrary python processing.
They are dicts.

Sections
========
Sections are short segments of RST. They will be in the final spec, but they
are unordered. They typically use a combination of templates + units to
construct bits of RST.

Skeleton
========
The skeleton is a single RST file which is passed through a templating system to
replace variable names with sections.

Processing
==========
- Execute all unit functions to load units into memory and process them.
- Execute all section functions (which can now be done because the units exist)
- Execute the skeleton function to bring it into a single file.

Checks
======
- Any units made which were not used at least once will produce a warning.
- Any sections made but not used in the skeleton will produce a warning.
"""

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from argparse import ArgumentParser, FileType
import json
import os
import sys
import textwrap

import internal.units
import internal.sections

def load_units():
    print "Loading units..."
    return internal.units.load()

def load_sections(env, units):
    print "\nLoading sections..."
    return internal.sections.load(env, units)

def create_from_template(template, sections):
    return template.render(sections.data)

def check_unaccessed(name, store):
    unaccessed_keys = store.get_unaccessed_set()
    if len(unaccessed_keys) > 0:
        print "Found %s unused %s keys." % (len(unaccessed_keys), name)
        print unaccessed_keys

def main(file_stream=None, out_dir=None):
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # add a template filter to produce pretty pretty JSON
    def jsonify(input, indent=None, pre_whitespace=0):
        code = json.dumps(input, indent=indent)
        if pre_whitespace:
            code = code.replace("\n", ("\n" +" "*pre_whitespace))

        return code

    def indent(input, indent):
        return input.replace("\n", ("\n" + " "*indent))

    def wrap(input, wrap=80):
        return '\n'.join(textwrap.wrap(input, wrap))

    # make Jinja aware of the templates and filters
    env = Environment(
        loader=FileSystemLoader("templates"),
        undefined=StrictUndefined
    )
    env.filters["jsonify"] = jsonify
    env.filters["indent"] = indent
    env.filters["wrap"] = wrap

    # load up and parse the lowest single units possible: we don't know or care
    # which spec section will use it, we just need it there in memory for when
    # they want it.
    units = load_units()

    # use the units to create RST sections
    sections = load_sections(env, units)

    # print out valid section keys if no file supplied
    if not file_stream:
        print "\nValid template variables:"
        for key in sections.keys():
            print "  %s" % key
        return

    # check the input files and substitute in sections where required
    print "Parsing input template: %s" % file_stream.name
    temp = Template(file_stream.read())
    print "Creating output for: %s" % file_stream.name
    output = create_from_template(temp, sections)
    with open(os.path.join(out_dir, file_stream.name), "w") as f:
        f.write(output)
    print "Output file for: %s" % file_stream.name

    check_unaccessed("units", units)


if __name__ == '__main__':
    parser = ArgumentParser(
        "Process a file (typically .rst) and replace templated areas with spec"+
        " info. For a list of possible template variables, add"+
        " --show-template-vars."
    )
    parser.add_argument(
        "file", nargs="?", type=FileType('r'),
        help="The input file to process."
    )
    parser.add_argument(
        "--out-directory", "-o", help="The directory to output the file to."+
        " Default: /out",
        default="out"
    )
    parser.add_argument(
        "--show-template-vars", "-s", action="store_true",
        help="Show a list of all possible variables you can use in the"+
        " input file."
    )
    args = parser.parse_args()

    if (args.show_template_vars):
        main()
        sys.exit(0)

    if not args.file:
        print "No file supplied."
        parser.print_help()
        sys.exit(1)

    main(file_stream=args.file, out_dir=args.out_directory)
