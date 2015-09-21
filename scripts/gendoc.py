#! /usr/bin/env python

from docutils.core import publish_file
import fileinput
import glob
import os
import re
import shutil
import subprocess
import sys
import yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))

stylesheets = {
    "stylesheet_path": ["basic.css", "nature.css"]
}

title_style_matchers = {
    "=": re.compile("^=+$"),
    "-": re.compile("^-+$")
}
TOP_LEVEL = "="
SECOND_LEVEL = "-"
FILE_FORMAT_MATCHER = re.compile("^[0-9]+_[0-9]{2}[a-z]*_.*\.rst$")


def check_valid_section_old(filename, section):
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

def check_valid_section(section):
    pass


def get_rst(file_info, target):
    pass

def build_spec(target, out_filename):
    with open(out_filename, "wb") as outfile:
        for file_info in target["files"]:
            section = get_rst(file_info, target)
            check_valid_section(section)
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


def get_build_target(targets_listing, target_name):
    build_target = {
        "title_styles": [],
        "files": []
    }
    with open(targets_listing, "r") as targ_file:
        all_targets = yaml.load(targ_file.read())
        build_target["title_styles"] = all_targets["title_styles"]
        target = all_targets["targets"].get(target_name)
        if not target:
            raise Exception(
                "No target by the name '" + target_name + "' exists in '" +
                targets_listing + "'."
            )
        if not isinstance(target.get("files"), list):
            raise Exception(
                "Found target but 'files' key is not a list."
            )
        resolved_files = []
        for f in target["files"]:
            if isinstance(f, basestring) and f.startswith("group:"):
                # copy across the group of files specified
                group_name = f[len("group:"):]
                group = all_targets.get("groups", {}).get(group_name)
                if not isinstance(group, list):
                    raise Exception(
                        "Tried to find group '" + group_name + "' but either " +
                        "it doesn't exist or it isn't a list of files."
                    )
                resolved_files.extend(group)
            else:
                resolved_files.append(f)
        build_target["files"] = resolved_files
    return build_target


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


def main(target_name):
    prepare_env()
    target = get_build_target("../specification/targets.yaml", target_name)
    print target
    build_spec(target=target, out_filename="tmp/full_spec.rst")
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
    main("main")
