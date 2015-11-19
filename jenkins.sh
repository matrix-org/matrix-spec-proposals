#! /bin/bash

set -ex

(cd event-schemas/ && ./check_examples.py)
(cd api && ./check_examples.py)
(cd scripts && ./gendoc.py -v)
(cd api && npm install && node validator.js -s "client-server/v1" && node validator.js -s "client-server/v2_alpha")
(cd event-schemas/ && ./check.sh)

if which go >/dev/null 2>/dev/null; then
  (cd scripts/continuserv && go build)
  (cd scripts/speculator && go build)
fi
