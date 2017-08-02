#!/bin/sh
#
# this script runs 'jekyll' to turn the 'supporting-docs' into HTML.
#
# jekyll requires the `docutils` and `pygments` python packages, so install
# them or run from a virtualenv which includes them.


set -e

# tell jekyll to parse things as utf-8
export LANG="en_GB.UTF-8"

cd `dirname $0`/..

mkdir -p _site
jekyll build -s jekyll
./scripts/add_anchors.py _site/guides/faq.html >tmp && mv tmp _site/guides/faq.html
./scripts/add_anchors.py _site/projects/try-matrix-now.html >tmp && mv tmp _site/projects/try-matrix-now.html

