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
    "stylesheet_path": ["basic.css", "nature.css", "codehighlight.css"]
}


def _list_get(l, index, default=None):
    try:
        return l[index]
    except IndexError:
        return default


def load_with_adjusted_titles(filename, file_stream, title_level, title_styles):
    rst_lines = []
    title_chars = "".join(title_styles)
    title_regex = re.compile("^[" + re.escape(title_chars) + "]+$")

    curr_title_level = title_level
    for i, line in enumerate(file_stream, 1):
        if title_regex.match(line):
            line_title_level = title_styles.index(line[0])
            # Allowed to go 1 deeper or any number shallower
            if curr_title_level - line_title_level < -1:
                raise Exception(
                    ("File '%s' line '%s' has a title " +
                    "style '%s' which doesn't match one of the " +
                    "allowed title styles of %s because the " +
                    "title level before this line was '%s'") %
                    (filename, (i + 1), line[0], title_styles,
                    title_styles[curr_title_level])
                )
            curr_title_level = line_title_level
            rst_lines.append(line)
        else:
            rst_lines.append(line)
    return "".join(rst_lines)


def get_rst(file_info, title_level, title_styles, spec_dir):
    # string are file paths to RST blobs
    if isinstance(file_info, basestring):
        print "%s %s" % (">" * (1 + title_level), file_info)
        with open(spec_dir + file_info, "r") as f:
            return load_with_adjusted_titles(file_info, f, title_level, title_styles)
    # dicts look like {0: filepath, 1: filepath} where the key is the title level
    elif isinstance(file_info, dict):
        levels = sorted(file_info.keys())
        rst = []
        for l in levels:
            rst.append(get_rst(file_info[l], l, title_styles, spec_dir))
        return "".join(rst)
    # lists are multiple file paths e.g. [filepath, filepath]
    elif isinstance(file_info, list):
        rst = []
        for f in file_info:
            rst.append(get_rst(f, title_level, title_styles, spec_dir))
        return "".join(rst)
    raise Exception(
        "The following 'file' entry in this target isn't a string, list or dict. " +
        "It really really should be. Entry: %s" % (file_info,)
    )


def build_spec(target, out_filename):
    with open(out_filename, "wb") as outfile:
        for file_info in target["files"]:
            section = get_rst(
                file_info=file_info,
                title_level=0,
                title_styles=target["title_styles"],
                spec_dir="../specification/"
            )
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
                if not group:
                    raise Exception(
                        "Tried to find group '" + group_name + "' but it " +
                        "doesn't exist."
                    )
                if isinstance(group, list):
                    resolved_files.extend(group)
                else:
                    resolved_files.append(group)
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
    print "Building spec [target=%s]" % target_name
    target = get_build_target("../specification/targets.yaml", target_name)
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
