#!/usr/bin/env python3
# Copyright 2021 The Matrix.org Foundation C.I.C.
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

# This script takes a google fonts CSS URL, downloads the referenced fonts locally
# and spits out a modified CSS file which now points to those local fonts.
#
# Purely for the purposes of converting a website to use local font files instead of
# making requests to Google Fonts.

import re
import requests
import subprocess
import sys

# Pull the font filename to process and output directory to point at
if len(sys.argv) < 4:
    print(f"""
Error: Not enough arguments.

Usage: {sys.argv[0]} google_fonts_url font_directory css_font_path
* google fonts url: A URL leading to a google font css file (i.e https://fonts.googleapis.com/css?family=Inter)
* font directory: The location that font files will be downloaded to (i.e ../../fonts)
* font path: The directory the resulting CSS will be pointing to, relative to site root (i.e /unstable/css/fonts).
             This is where the browser will look for fonts.
""")
    sys.exit(1)

google_fonts_url = sys.argv[1]
font_output_dir = sys.argv[2]
css_font_path = sys.argv[3]

# Get font name
if google_fonts_url.count(":") > 1:
    # Account for font weights specified in the URL
    # (i.e https://fonts.googleapis.com/css?family=Inter:300,300i,400,400i,700,700i)
    url_match = re.match(r".*family=(.*):", google_fonts_url)
else:
    url_match = re.match(r".*family=(.*)", google_fonts_url)

if not url_match:
    print("Unable to extract font name, invalid google fonts URL:", google_fonts_url)
    print("URL should look something like: https://fonts.googleapis.com/css?family=Inter...")
    sys.exit(1)

font_name = url_match.group(1)

# Ensure font paths end with a trailing slash
if not font_output_dir.endswith("/"):
    font_output_dir += "/"
if not css_font_path.endswith("/"):
    css_font_path += "/"

# Download the css file and split by newline
resp = requests.get(
    google_fonts_url,
    # We need to set a believable user-agent, else google fonts won't give us
    # all of the font weights we requested for some reason
    headers={
        "User-Agent": "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0"
    }
)
if resp.status_code != 200:
    print("Failed to download:", google_fonts_url, resp.status_code)
    sys.exit(1)

original_contents = resp.text.split("\n")

# Download all referenced font files and write out new font file
new_css_file_lines = []

# Store metadata for helping give friendly names to each font file
font_lang = None
font_family = None
font_style = None
font_weight = 0
for line in original_contents:
    # Check if this line contains a font URL
    match = re.match(r".*url\((.*)\) format.*", line)
    if match:
        # Download the font file
        font_url = match.group(1)
        print("Downloading font:", font_url)

        resp = requests.get(font_url)
        if resp.status_code == 200:
            # Save the font file
            filename = "%s-%s-%s-%d.woff2" % (
                font_family, font_lang, font_style, font_weight
            )
            font_filepath = font_output_dir + filename
            with open(font_filepath, "w") as f:
                print("Writing font file:", font_filepath)
                f.write(resp.text)

            # Replace google URL with local URL
            line = re.sub(r"url\(.+\)", f"url({css_font_path + filename})", line)
        else:
            print("Warning: failed to download font file:", font_url)

    # Check for font metadata. If there is some, we'll note it down and use it to help
    # name font files when we write them out.
    # Makes for nicer font filenames than fvQtMwCp50KnMw2boKod... etc.
    font_lang_match = re.match(r"^/\* (.+) \*/$", line)
    if font_lang_match:
        font_lang = font_lang_match.group(1)
    font_family_match = re.match(r".*font-family: '(.+)';$", line)
    if font_family_match:
        font_family = font_family_match.group(1)
    font_style_match = re.match(r".*font-style: (.+);$", line)
    if font_style_match:
        font_style = font_style_match.group(1)
    font_weight_match = re.match(r".*font-weight: (.+);$", line)
    if font_weight_match:
        font_weight = int(font_weight_match.group(1))

    # Append the potentially modified line to the new css file
    new_css_file_lines.append(line)

# Write out the new font css file
with open(font_name + ".css", "w") as f:
    new_css_file_contents = "\n".join(new_css_file_lines)
    f.write(new_css_file_contents)
