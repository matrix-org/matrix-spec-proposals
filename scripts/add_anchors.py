#!/usr/bin/env python
#
# adds anchors before any <h1/h2/h3/h4/h5> tags with an id="..." - this is used
# for things like the FAQ where we want to have anchored links to every
# question (and this way you don't have to manually maintain it in the source
# doc).

from sys import argv
import re

filename = argv[1]

regex = r'(<h\d id="(.*?)">)'
regex2 = r'(<div class="section" id="(.*?)">)'

replacement = r'<p><a class="anchor" id="\2"></a></p>\n\1'

with open(filename, "r") as f:
    lines = list(f)

# check for <hX id="..." (used in the FAQ) and add anchors - and then check
# for <div class="section" id="..." and add anchors (used in the spec)

with open(filename, "w") as f:
    for line in lines:
        line = re.sub(regex, replacement, line)
        line = re.sub(regex2, replacement, line)
        f.write(line)
