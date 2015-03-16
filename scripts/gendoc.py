#! /usr/bin/env python

from docutils.core import publish_file
import fileinput
import glob
import os
import shutil
import subprocess
import sys

stylesheets = {
    "stylesheet_path": ["basic.css", "nature.css"]
}


def get_git_ver_string():
    null = open(os.devnull, 'w')
    cwd = os.path.dirname(os.path.abspath(__file__))
    try:
        git_branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=null,
            cwd=cwd,
        ).strip()
    except subprocess.CalledProcessError:
        git_branch = ""
    try:
        git_tag = subprocess.check_output(
            ['git', 'describe', '--exact-match'],
            stderr=null,
            cwd=cwd,
        ).strip()
        git_tag = "tag=" + git_tag
    except subprocess.CalledProcessError:
        git_tag = ""
    try:
        git_commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=null,
            cwd=cwd,
        ).strip()
    except subprocess.CalledProcessError:
        git_commit = ""
    try:
        dirty_string = "-this_is_a_dirty_checkout"
        is_dirty = subprocess.check_output(
            ['git', 'describe', '--dirty=' + dirty_string, "--all"],
            stderr=null,
            cwd=cwd,
        ).strip().endswith(dirty_string)
        git_dirty = "dirty" if is_dirty else ""
    except subprocess.CalledProcessError:
        git_dirty = ""

    if git_branch or git_tag or git_commit or git_dirty:
        git_version = ",".join(
            s for s in
            (git_branch, git_tag, git_commit, git_dirty,)
            if s
        )
        return git_version.encode("ascii")
    return "Unknown rev"


def glob_spec_to(out_file_name):
    with open(out_file_name, "wb") as outfile:
        for f in sorted(glob.glob("../specification/*.rst")):
            with open(f, "rb") as infile:
                outfile.write(infile.read())

def set_git_version(filename):
    git_ver = get_git_ver_string()
    # inplace search and replace, stdout is redirected to the output
    # file, hence the "print" lines here.
    for line in fileinput.input(filename, inplace=True):
        if "$GIT_VERSION" in line:
            line = line.replace("$GIT_VERSION", git_ver)
        print line.rstrip("\n")
    

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
    pass
    #shutil.rmtree("./tmp")

def main():
    prepare_env()
    glob_spec_to("tmp/full_spec.rst")
    shutil.copy("../supporting-docs/howtos/client-server.rst", "tmp/howto.rst")
    set_git_version("tmp/full_spec.rst")
    set_git_version("tmp/howto.rst")
    rst2html("tmp/full_spec.rst", "gen/specification.html")
    rst2html("tmp/howto.rst", "gen/howtos.html")
    cleanup_env()

if __name__ == '__main__':
    main()
