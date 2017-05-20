#! /bin/bash

set -ex

ln -s v1-event-schema/core-event-schema ./api/client-server/v1/core-event-schema
ln -s ../../../event-schemas/schema/v1 ./api/client-server/v1/v1-event-schema
ln -s ../../../event-schemas/schema/v1/core-event-schema ./api/client-server/v2_alpha/core-event-schema
ln -s . ./api/client-server/v2_alpha/definitions/definitions
ln -s . ./event-schemas/schema/v1/core-event-schema/core-event-schema
ln -s . ./event-schemas/schema/v1/v1-event-schema

trap "rm ./api/client-server/v1/core-event-schema ./api/client-server/v1/v1-event-schema ./api/client-server/v2_alpha/core-event-schema ./api/client-server/v2_alpha/definitions/definitions ./event-schemas/schema/v1/core-event-schema/core-event-schema ./event-schemas/schema/v1/v1-event-schema" EXIT

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

