#!/bin/bash -e
# Runs z-schema over all of the schema files (looking for matching examples)

if ! which z-schema; then
  echo >&2 "Need to install z-schema; run: sudo npm install -g z-schema"
  exit 1
fi

find schema/m.* | while read line
do
    split_path=(${line///// })
    event_type=(${split_path[2]})
    echo "Checking $event_type"
    echo "--------------------"
    # match exact name or exact name with a #<something>
    find examples -name $event_type -o -name "$event_type#*" | while read exline
    do
        echo "    against $exline"
        # run z-schema: because of bash -e if this fails we bail with exit code 1
        z-schema schema/$event_type $exline
    done
done
