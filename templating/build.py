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

from jinja2 import Environment, FileSystemLoader
import internal.units
import internal.sections
import json

def load_units():
    print "Loading units..."
    return internal.units.load()

def load_sections(env, units):
    print "Loading sections..."
    return internal.sections.load(env, units)

def create_from_skeleton(skeleton, sections):
    print "Creating spec from skeleton..."
    print "Section keys: %s" % (sections.keys())
    return skeleton.render(sections.data)


def check_unaccessed(name, store):
    unaccessed_keys = store.get_unaccessed_set()
    if len(unaccessed_keys) > 0:
        print "Found %s unused %s keys." % (len(unaccessed_keys), name)
        print unaccessed_keys

def main():
    # add a template filter to produce pretty pretty JSON
    def jsonify(input):
        return json.dumps(input, indent=4)

    # make Jinja aware of the templates and filters
    env = Environment(loader=FileSystemLoader("templates"))
    env.filters["jsonify"] = jsonify

    # load up and parse the lowest single units possible: we don't know or care
    # which spec section will use it, we just need it there in memory for when
    # they want it.
    units = load_units()

    # use the units to create RST sections
    sections = load_sections(env, units)

    # combine all the RST sections into a coherent spec
    skeleton = env.get_template("skeleton.rst")
    spec = create_from_skeleton(skeleton, sections)

    check_unaccessed("units", units)
    check_unaccessed("sections", sections)
    
    with open("spec.rst", "w") as f:
        f.write(spec)


if __name__ == '__main__':
    main()
