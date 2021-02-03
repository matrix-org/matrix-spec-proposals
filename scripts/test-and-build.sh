#! /bin/bash

set -ex

cd `dirname $0`/..

virtualenv -p python3 env
. env/bin/activate

# Print out the python versions for debugging purposes
python --version
pip --version

pip install -r scripts/requirements.txt

# do sanity checks on the examples and swagger
scripts/check-event-schema-examples.py
scripts/check-swagger-sources.py
(cd event-schemas/api && npm install && node validator.js -s "client-server")

: ${GOPATH:=${WORKSPACE}/.gopath}
mkdir -p "${GOPATH}"
export GOPATH
go get github.com/hashicorp/golang-lru
go get gopkg.in/fsnotify/fsnotify.v1

# make sure that the scripts build
(cd scripts/continuserv && go build)
(cd scripts/speculator && go build)

# build the spec for matrix.org.
# (we don't actually use it on travis, but it's still useful to check we
# can build it. On Buildkite, this is then used to deploy to matrix.org).
./scripts/generate-matrix-org-assets
