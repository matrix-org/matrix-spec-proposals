#! /bin/bash

set -ex

virtualenv env
. env/bin/activate
pip install -r scripts/requirements.txt

# do sanity checks on the examples and swagger
(cd event-schemas/ && ./check_examples.py)
(cd api && ./check_examples.py)
(cd api && npm install && node validator.js -s "client-server")

: ${GOPATH:=${WORKSPACE}/.gopath}
mkdir -p "${GOPATH}"
export GOPATH
go get github.com/hashicorp/golang-lru
go get gopkg.in/fsnotify.v1

# make sure that the scripts build
(cd scripts/continuserv && go build)
(cd scripts/speculator && go build)

# build the spec and collect the supporting docs for matrix.org.  (we aren't
# actually going to use them, since we're on travis, but we may as well check
# that the build works correctly).
./scripts/generate-matrix-org-assets
