#!/bin/bash -e
# Runs z-schema over all of the schema files (looking for matching examples)
find schema/v1/m.* | while read line
do
    split_path=(${line///// })
    event_type=(${split_path[2]})
    echo "Checking $event_type"
    echo "--------------------"
    # match exact name or exact name with a #<something>
    find examples/v1 -name $event_type -o -name "$event_type#*" | while read exline
    do
        echo "    against $exline"
        # run z-schema: because of bash -e if this fails we bail with exit code 1
        z-schema schema/v1/$event_type $exline
    done
done
