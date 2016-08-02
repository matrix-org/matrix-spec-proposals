#! /bin/bash

git rev-parse --abbrev-ref HEAD 2>/dev/null; git describe --exact-match 2>/dev/null; git rev-parse --short HEAD 2>/dev/null; 

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

(cd scripts/continuserv && go build)
(cd scripts/speculator && go build)

