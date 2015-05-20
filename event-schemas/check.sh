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
        # run z-schema and dump stdout/err to the terminal (good for Jenkin's Console Output) and grep for fail messages
        if [[ -n $(z-schema schema/v1/$event_type $exline 2>&1 | tee /dev/tty | grep -Ei "error|failed") ]]; then
            echo "    Failed."
            exit 1
        fi
    done
done
