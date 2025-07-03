#!/bin/bash

# usage
help() {
    echo "This script can be used to check benchmark results for runlim errors and re-run such instances."
    echo "Make sure, the environment where the benchmark-tool is installed is active."
    echo "Check the benchmark-tool documentation for more information"
    echo
    echo "Syntax: ${0##*/} [-h] <runscript.xml>"
    echo "options:"
    echo "h    Print this Help."
    echo
}

# parse options
while getopts ":h" option; do
    case $option in
    	h) # display Help
    		help
    		exit 0
            ;;
    	\?) # invalid option
    		echo "Error: Invalid option" >&2
		    exit 1
            ;;
    esac
done

# invalid input
if ! [ -f $1 ]; then
    echo "Error: provided runscript doesn't exist" >&2
    exit 1
fi

# search runlim erros
echo "Look for runlim errors..."
DIR=$(cat $1 | sed -nr 's/^.*output="(\S+)".*$/\1/p')
readarray -d '' < <(find $DIR -name "runsolver.watcher" -exec grep -q "runlim error" {} \; -print0)

# exit if nothing found
if [ -z ${MAPFILE[@]} ]; then
    echo "No runlim erros found"
    exit 0
fi

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
