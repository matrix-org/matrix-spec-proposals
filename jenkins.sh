#! /bin/bash

set -ex

(cd event-schemas/ && ./check_examples.py)
(cd api && ./check_examples.py)
(cd scripts && ./gendoc.py)
(cd api && npm install && node validator.js -s "client-server/v1")
(cd event-schemas/ && ./check.sh)
