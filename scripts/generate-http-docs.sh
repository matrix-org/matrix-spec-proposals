#!/bin/bash -eu

# This script generates an HTML page containing all of the client-server API docs.
# It takes all of the swagger YAML files for the client-server API, and turns
# them into API docs, with none of the narrative found in the rst files which
# normally wrap these API docs.

cd "$(dirname $0)"

mkdir -p tmp gen

cat >tmp/http_apis <<EOF
Matrix Client-Server API Reference
==================================

This contains the client-server API for the reference implementation of the home server.


EOF

for f in ../api/client-server/*/*.yaml; do
  f="$(basename "${f/.yaml/_http_api}")"
  echo "{{${f/-/_}}}" >> tmp/http_apis
done

(cd ../templating ; python build.py -i matrix_templates -o ../scripts/gen ../scripts/tmp/http_apis)
rst2html.py --stylesheet-path=$(echo css/*.css | tr ' ' ',') gen/http_apis > gen/http_apis.html
