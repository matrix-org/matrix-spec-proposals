#! /usr/bin/env python

from docutils.core import publish_file
import fileinput
import glob
import os
import re
import shutil
import subprocess
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

stylesheets = {
    "stylesheet_path": ["basic.css", "nature.css", "codehighlight.css"]
}

title_style_matchers = {
    "=": re.compile("^=+$"),
    "-": re.compile("^-+$")
}
TOP_LEVEL = "="
SECOND_LEVEL = "-"
FILE_FORMAT_MATCHER = re.compile("^[0-9]+_[0-9]{2}[a-z]*_.*\.rst$")


def check_valid_section(filename, section):
    if not re.match(FILE_FORMAT_MATCHER, filename):
        raise Exception(
            "The filename of " + filename + " does not match the expected format " +
            "of '##_##_words-go-here.rst'"
        )

    # we need TWO new lines else the next file's title gets merged
    # the last paragraph *WITHOUT RST PRODUCING A WARNING*
    if not section[-2:] == "\n\n":
        raise Exception(
            "The file " + filename + " does not end with 2 new lines."
        )

    # Enforce some rules to reduce the risk of having mismatched title
    # styles.
    title_line = section.split("\n")[1]
    if title_line != (len(title_line) * title_line[0]):
        raise Exception(
            "The file " + filename + " doesn't have a title style line on line 2"
        )

    # anything marked as xx_00_ is the start of a new top-level section
    if re.match("^[0-9]+_00_", filename):
        if not title_style_matchers[TOP_LEVEL].match(title_line):
            raise Exception(
                "The file " + filename + " is a top-level section because it matches " +
                "the filename format ##_00_something.rst but has the wrong title " +
                "style: expected '" + TOP_LEVEL + "' but got '" +
                title_line[0] + "'"
            )
    # anything marked as xx_xx_ is the start of a sub-section
    elif re.match("^[0-9]+_[0-9]{2}_", filename):
        if not title_style_matchers[SECOND_LEVEL].match(title_line):
            raise Exception(
                "The file " + filename + " is a 2nd-level section because it matches " +
                "the filename format ##_##_something.rst but has the wrong title " +
                "style: expected '" + SECOND_LEVEL + "' but got '" +
                title_line[0] + "' - If this is meant to be a 3rd/4th/5th-level section " +
                "then use the form '##_##b_something.rst' which will not apply this " +
                "check."
            )

def cat_spec_sections_to(out_file_name):
    with open(out_file_name, "wb") as outfile:
        for f in sorted(glob.glob("../specification/*.rst")):
            with open(f, "rb") as infile:
                section = infile.read()
                check_valid_section(os.path.basename(f), section)
                outfile.write(section)


def rst2html(i, o):
    with open(i, "r") as in_file:
        with open(o, "w") as out_file:
            publish_file(
                source=in_file,
                destination=out_file,
                reader_name="standalone",
                parser_name="restructuredtext",
                writer_name="html",
                settings_overrides=stylesheets
            )

def run_through_template(input):
    tmpfile = './tmp/output'
    try:
        with open(tmpfile, 'w') as out:
            subprocess.check_output(
                [
                    'python', 'build.py',
                    "-i", "matrix_templates",
                    "-o", "../scripts/tmp",
                    "../scripts/"+input
                ],
                stderr=out,
                cwd="../templating",
            )
    except subprocess.CalledProcessError as e:
        with open(tmpfile, 'r') as f:
            sys.stderr.write(f.read() + "\n")
        raise

def prepare_env():
    try:
        os.makedirs("./gen")
    except OSError:
        pass
    try:
        os.makedirs("./tmp")
    except OSError:
        pass
    
def cleanup_env():
    shutil.rmtree("./tmp")

def main():
    prepare_env()
    cat_spec_sections_to("tmp/full_spec.rst")
    run_through_template("tmp/full_spec.rst")
    shutil.copy("../supporting-docs/howtos/client-server.rst", "tmp/howto.rst")
    run_through_template("tmp/howto.rst")
    rst2html("tmp/full_spec.rst", "gen/specification.html")
    rst2html("tmp/howto.rst", "gen/howtos.html")
    if "--nodelete" not in sys.argv:
        cleanup_env()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1:] != ["--nodelete"]:
        # we accept almost no args, so they don't know what they're doing!
        print "gendoc.py - Generate the Matrix specification as HTML."
        print "Usage:"
        print "  python gendoc.py [--nodelete]"
        print ""
        print "The specification can then be found in the gen/ folder."
        print ("If --nodelete was specified, intermediate files will be "
               "present in the tmp/ folder.")
        print ""
        print "Requirements:"
        print " - This script requires Jinja2 and rst2html (docutils)."
        sys.exit(0)
    main()
