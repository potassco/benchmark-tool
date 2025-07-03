#!/bin/bash

# usage
help() {
    echo "This script can be used to check benchmark results for runlim errors and re-run such instances."
    echo "Make sure, the environment where the benchmark-tool is installed is active."
    echo
    echo "Syntax: ${0##*/} <runscript> [-h]"
    echo "options:"
    echo "h    Print this Help."
    echo
}

# parse options
while getopts ":h" option; do
    case $option in
    	h) # display Help
    		help
    		exit;;
    	\?) # invalid option
    		echo "Error: Invalid option" >&2
		exit;;
    esac
done

# search runlim erros
echo "Look for runlim errors..."
DIR=$(cat $1 | sed -nr 's/^.*output="(\S+)".*$/\1/p')
readarray -d '' < <(find $DIR -name "runsolver.watcher" -exec grep -q "runlim error" {} \; -print0)

# delete .finished
for FILE in ${MAPFILE[@]}
do
    TODEL="${FILE%/*}/.finished"
    if [ -f $TODEL ]; then
        rm -v "$TODEL"
    fi
done

# create new start script
echo "Create new start script..."
if ! [ -x "$(command -v bgen)" ]; then
    echo "Error: benchmark-tool is not installed." >&2
    exit 1
fi
bgen -e $1

