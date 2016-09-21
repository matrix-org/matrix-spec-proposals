#! /usr/bin/env python

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

from argparse import ArgumentParser
from docutils.core import publish_file
import copy
import fileinput
import glob
import os
import os.path
import re
import shutil
import subprocess
import sys
import yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))

stylesheets = {
    "stylesheet_path": glob.glob("css/*.css"),
}

VERBOSE = False

"""
Read a RST file and replace titles with a different title level if required.
Args:
    filename: The name of the file being read (for debugging)
    file_stream: The open file stream to read from.
    title_level: The integer which determines the offset to *start* from.
    title_styles: An array of characters detailing the right title styles to use
                  e.g. ["=", "-", "~", "+"]
Returns:
    string: The file contents with titles adjusted.
Example:
    Assume title_styles = ["=", "-", "~", "+"], title_level = 1, and the file
    when read line-by-line encounters the titles "===", "---", "---", "===", "---".
    This function will bump every title encountered down a sub-heading e.g.
    "=" to "-" and "-" to "~" because title_level = 1, so the output would be
    "---", "~~~", "~~~", "---", "~~~". There is no bumping "up" a title level.
"""
def load_with_adjusted_titles(filename, file_stream, title_level, title_styles):
    rst_lines = []
    title_chars = "".join(title_styles)
    title_regex = re.compile("^[" + re.escape(title_chars) + "]{3,}$")

    prev_line_title_level = 0 # We expect the file to start with '=' titles
    file_offset = None
    prev_non_title_line = None
    for i, line in enumerate(file_stream, 1):
        # ignore anything which isn't a title (e.g. '===============')
        if not title_regex.match(line):
            rst_lines.append(line)
            prev_non_title_line = line
            continue
        # The title underline must match at a minimum the length of the title
        if len(prev_non_title_line) > len(line):
            rst_lines.append(line)
            prev_non_title_line = line
            continue

        line_title_style = line[0]
        line_title_level = title_styles.index(line_title_style)

        # Not all files will start with "===" and we should be flexible enough
        # to allow that. The first title we encounter sets the "file offset"
        # which is added to the title_level desired.
        if file_offset is None:
            file_offset = line_title_level
            if file_offset != 0:
                logv(("     WARNING: %s starts with a title style of '%s' but '%s' " +
                    "is preferable.") % (filename, line_title_style, title_styles[0]))

        # Sanity checks: Make sure that this file is obeying the title levels
        # specified and bail if it isn't.
        # The file is allowed to go 1 deeper or any number shallower
        if prev_line_title_level - line_title_level < -1:
            raise Exception(
                ("File '%s' line '%s' has a title " +
                "style '%s' which doesn't match one of the " +
                "allowed title styles of %s because the " +
                "title level before this line was '%s'") %
                (filename, (i + 1), line_title_style, title_styles,
                title_styles[prev_line_title_level])
            )
        prev_line_title_level = line_title_level

        adjusted_level = (
            title_level + line_title_level - file_offset
        )

        # Sanity check: Make sure we can bump down the title and we aren't at the
        # lowest level already
        if adjusted_level >= len(title_styles):
            raise Exception(
                ("Files '%s' line '%s' has a sub-title level too low and it " +
                "cannot be adjusted to fit. You can add another level to the " +
                "'title_styles' key in targets.yaml to fix this.") %
                (filename, (i + 1))
            )

        if adjusted_level == line_title_level:
            # no changes required
            rst_lines.append(line)
            continue

        # Adjusting line levels
        logv(
            "File: %s Adjusting %s to %s because file_offset=%s title_offset=%s" %
            (filename, line_title_style, title_styles[adjusted_level],
                file_offset, title_level)
        )
        rst_lines.append(line.replace(
            line_title_style,
            title_styles[adjusted_level]
        ))

    return "".join(rst_lines)


def get_rst(file_info, title_level, title_styles, spec_dir, adjust_titles):
    # string are file paths to RST blobs
    if isinstance(file_info, basestring):
        log("%s %s" % (">" * (1 + title_level), file_info))
        with open(os.path.join(spec_dir, file_info), "r") as f:
            rst = None
            if adjust_titles:
                rst = load_with_adjusted_titles(
                    file_info, f, title_level, title_styles
                )
            else:
                rst = f.read()

            rst += "\n\n"
            return rst
    # dicts look like {0: filepath, 1: filepath} where the key is the title level
    elif isinstance(file_info, dict):
        levels = sorted(file_info.keys())
        rst = []
        for l in levels:
            rst.append(get_rst(file_info[l], l, title_styles, spec_dir, adjust_titles))
        return "".join(rst)
    # lists are multiple file paths e.g. [filepath, filepath]
    elif isinstance(file_info, list):
        rst = []
        for f in file_info:
            rst.append(get_rst(f, title_level, title_styles, spec_dir, adjust_titles))
        return "".join(rst)
    raise Exception(
        "The following 'file' entry in this target isn't a string, list or dict. " +
        "It really really should be. Entry: %s" % (file_info,)
    )


def build_spec(target, out_filename):
    log("Building templated file %s" % out_filename)
    with open(out_filename, "wb") as outfile:
        for file_info in target["files"]:
            section = get_rst(
                file_info=file_info,
                title_level=0,
                title_styles=target["title_styles"],
                spec_dir="../specification/",
                adjust_titles=True
            )
            outfile.write(section)


"""
Replaces relative title styles with actual title styles.

The templating system has no idea what the right title style is when it produces
RST because it depends on the build target. As a result, it uses relative title
styles defined in targets.yaml to say "down a level, up a level, same level".

This function replaces these relative titles with actual title styles from the
array in targets.yaml.
"""
def fix_relative_titles(target, filename, out_filename):
    log("Fix relative titles, %s -> %s" % (filename, out_filename))
    title_styles = target["title_styles"]
    relative_title_chars = [
        target["relative_title_styles"]["subtitle"],
        target["relative_title_styles"]["sametitle"],
        target["relative_title_styles"]["supertitle"]
    ]
    relative_title_matcher = re.compile(
        "^[" + re.escape("".join(relative_title_chars)) + "]{3,}$"
    )
    title_matcher = re.compile(
        "^[" + re.escape("".join(title_styles)) + "]{3,}$"
    )
    current_title_style = None
    with open(filename, "r") as infile:
        with open(out_filename, "w") as outfile:
            for line in infile.readlines():
                if not relative_title_matcher.match(line):
                    if title_matcher.match(line):
                        current_title_style = line[0]
                    outfile.write(line)
                    continue
                line_char = line[0]
                replacement_char = None
                current_title_level = title_styles.index(current_title_style)
                if line_char == target["relative_title_styles"]["subtitle"]:
                    if (current_title_level + 1) == len(title_styles):
                        raise Exception(
                            "Encountered sub-title line style but we can't go " +
                            "any lower."
                        )
                    replacement_char = title_styles[current_title_level + 1]
                elif line_char == target["relative_title_styles"]["sametitle"]:
                    replacement_char = title_styles[current_title_level]
                elif line_char == target["relative_title_styles"]["supertitle"]:
                    if (current_title_level - 1) < 0:
                        raise Exception(
                            "Encountered super-title line style but we can't go " +
                            "any higher."
                        )
                    replacement_char = title_styles[current_title_level - 1]
                else:
                    raise Exception(
                        "Unknown relative line char %s" % (line_char,)
                    )

                outfile.write(
                    line.replace(line_char, replacement_char)
                )



def rst2html(i, o):
    log("rst2html %s -> %s" % (i, o))
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


def addAnchors(path):
    log("add anchors %s" % path)

    with open(path, "r") as f:
        lines = f.readlines()

    replacement = replacement = r'<p><a class="anchor" id="\3"></a></p>\n\1'
    with open(path, "w") as f:
        for line in lines:
            line = re.sub(r'(<h\d id="#?(.*?)">)', replacement, line.rstrip())
            line = re.sub(r'(<div class="section" (id)="(.*?)">)', replacement, line.rstrip())
            f.write(line + "\n")


def run_through_template(input_files, set_verbose, substitutions):
    args = [
        'python', 'build.py',
        "-o", "../scripts/tmp",
        "-i", "matrix_templates",
    ]

    for k, v in substitutions.items():
        args.append("--substitution=%s=%s" % (k, v))

    if set_verbose:
        args.insert(2, "-v")

    args.extend("../scripts/"+f for f in input_files)

    log("EXEC: %s" % " ".join(args))
    log(" ==== build.py output ==== ")
    subprocess.check_call(
        args,
        cwd="../templating"
    )

"""
Extract and resolve groups for the given target in the given targets listing.
Args:
    all_targets (dict): The parsed YAML file containing a list of targets
    target_name (str): The name of the target to extract from the listings.
Returns:
    dict: Containing "filees" (a list of file paths), "relative_title_styles"
          (a dict of relative style keyword to title character) and "title_styles"
          (a list of characters which represent the global title style to follow,
           with the top section title first, the second section second, and so on.)
"""
def get_build_target(all_targets, target_name):
    build_target = {
        "title_styles": [],
        "relative_title_styles": {},
        "files": []
    }

    build_target["title_styles"] = all_targets["title_styles"]
    build_target["relative_title_styles"] = all_targets["relative_title_styles"]
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

    def get_group(group_id, depth):
        group_name = group_id[len("group:"):]
        group = all_targets.get("groups", {}).get(group_name)
        if not group:
            raise Exception(
                "Tried to find group '%s' but it doesn't exist." % group_name
            )
        if not isinstance(group, list):
            raise Exception(
                "Expected group '%s' to be a list but it isn't." % group_name
            )
        # deep copy so changes to depths don't contaminate multiple uses of this group
        group = copy.deepcopy(group)
        # swap relative depths for absolute ones
        for i, entry in enumerate(group):
            if isinstance(entry, dict):
                group[i] = {
                    (rel_depth + depth): v for (rel_depth, v) in entry.items()
                }
        return group

    resolved_files = []
    for file_entry in target["files"]:
        # file_entry is a group id
        if isinstance(file_entry, basestring) and file_entry.startswith("group:"):
            group = get_group(file_entry, 0)
            # The group may be resolved to a list of file entries, in which case
            # we want to extend the array to insert each of them rather than
            # insert the entire list as a single element (which is what append does)
            if isinstance(group, list):
                resolved_files.extend(group)
            else:
                resolved_files.append(group)
        # file_entry is a dict which has more file entries as values
        elif isinstance(file_entry, dict):
            resolved_entry = {}
            for (depth, entry) in file_entry.iteritems():
                if not isinstance(entry, basestring):
                    raise Exception(
                        "Double-nested depths are not supported. Entry: %s" % (file_entry,)
                    )
                if entry.startswith("group:"):
                    resolved_entry[depth] = get_group(entry, depth)
                else:
                    # map across without editing (e.g. normal file path)
                    resolved_entry[depth] = entry
            resolved_files.append(resolved_entry)
            continue
        # file_entry is just a plain ol' file path
        else:
            resolved_files.append(file_entry)
    build_target["files"] = resolved_files
    return build_target

def log(line):
    print "gendoc: %s" % line

def logv(line):
    if VERBOSE:
        print "gendoc:V: %s" % line


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


def main(targets, keep_intermediates, substitutions):
    prepare_env()

    with open("../specification/targets.yaml", "r") as targ_file:
        target_defs = yaml.load(targ_file.read())

    if targets == ["all"]:
        targets = target_defs["targets"].keys()

    log("Building spec [target=%s]" % targets)

    templated_files = []
    for target_name in targets:
        templated_file = "tmp/templated_%s.rst" % (target_name,)

        target = get_build_target(target_defs, target_name)
        build_spec(target=target, out_filename=templated_file)
        templated_files.append(templated_file)

    # we do all the templating at once, because it's slow
    run_through_template(templated_files, VERBOSE, substitutions)

    for target_name in targets:
        target = target_defs["targets"].get(target_name)
        version_label = None
        if target:
            version_label = target.get("version_label")
            if version_label:
                for old, new in substitutions.items():
                    version_label = version_label.replace(old, new)

        templated_file = "tmp/templated_%s.rst" % (target_name,)
        rst_file = "tmp/spec_%s.rst" % (target_name,)
        if version_label:
            d = os.path.join("gen", target_name)
            if not os.path.exists(d):
                os.mkdir(d)
            html_file = os.path.join(d, "%s.html" % version_label)
        else:
            html_file = "gen/%s.html" % (target_name, )

        fix_relative_titles(
            target=target_defs, filename=templated_file,
            out_filename=rst_file,
        )
        rst2html(rst_file, html_file)
        addAnchors(html_file)

    if not keep_intermediates:
        cleanup_env()


def list_targets():
    with open("../specification/targets.yaml", "r") as targ_file:
        target_defs = yaml.load(targ_file.read())
    targets = target_defs["targets"].keys()
    print "\n".join(targets)


def extract_major(s):
    major_version = s
    match = re.match("^(r\d)+(\.\d+)*$", s)
    if match:
        major_version = match.group(1)
    return major_version


if __name__ == '__main__':
    parser = ArgumentParser(
        "gendoc.py - Generate the Matrix specification as HTML to the gen/ folder."
    )
    parser.add_argument(
        "--nodelete", "-n", action="store_true",
        help="Do not delete intermediate files. They will be found in tmp/"
    )
    parser.add_argument(
        "--target", "-t", action="append",
        help="Specify the build target to build from specification/targets.yaml. " +
             "The value 'all' will build all of the targets therein."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Turn on verbose mode."
    )
    parser.add_argument(
        "--client_release", "-c", action="store", default="unstable",
        help="The client-server release tag to generate, e.g. r1.2"
    )
    parser.add_argument(
        "--server_release", "-s", action="store", default="unstable",
        help="The server-server release tag to generate, e.g. r1.2"
    )
    parser.add_argument(
        "--list_targets", action="store_true",
        help="Do not update the specification. Instead print a list of targets.",
    )

    args = parser.parse_args()
    VERBOSE = args.verbose

    if args.list_targets:
        list_targets()
        exit(0)

    substitutions = {
        "%CLIENT_RELEASE_LABEL%": args.client_release,
        "%CLIENT_MAJOR_VERSION%": extract_major(args.client_release),
        "%SERVER_RELEASE_LABEL%": args.server_release,
        "%SERVER_MAJOR_VERSION%": extract_major(args.server_release),
    }
    main(args.target or ["all"], args.nodelete, substitutions)
