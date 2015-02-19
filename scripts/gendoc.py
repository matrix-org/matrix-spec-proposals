#! /usr/bin/env python

from docutils.core import publish_file
import glob
import os
import shutil
import sys

stylesheets = {
    "stylesheet_path": ["basic.css", "nature.css"]
}

def glob_spec(out_file_name):
    with open(out_file_name, "wb") as outfile:
        for f in sorted(glob.glob("../specification/*.rst")):
            with open(f, "rb") as infile:
                outfile.write(infile.read())
    

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
    shutil.rmtree("./tmp")

def main():
    prepare_env()
    glob_spec("tmp/full_spec.rst")
    rst2html("tmp/full_spec.rst", "gen/specification.html")
    rst2html("../howtos/client-server.rst", "gen/howtos.html")
    cleanup_env()

if __name__ == '__main__':
    main()
