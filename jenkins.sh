#! /bin/bash

set -ex

(cd event-schemas/ && ./check_examples.py)
(cd api && ./check_examples.py)
(cd scripts && ./gendoc.py -v)
(cd api && npm install && node validator.js -s "client-server")

: ${GOPATH:=${WORKSPACE}/.gopath}
mkdir -p "${GOPATH}"
export GOPATH
go get github.com/hashicorp/golang-lru
go get gopkg.in/fsnotify.v1

# make sure that the scripts build
(cd scripts/continuserv && go build)
(cd scripts/speculator && go build)

# update the jekyll site
./scripts/generate-jekyll.sh

# create a tarball of the generated site
tar -czf site.tar.gz _site
