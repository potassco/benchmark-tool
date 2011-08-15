#!/bin/bash

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

#top -n 1 -b > top.txt

[[ -e .finished ]] || $CAT "{run.file}" | taskset 0xfe "{run.root}/programs/runsolver-3.2.5" \
	-M 20000 \
	-w runsolver.watcher \
	-o runsolver.solver \
	-W {run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args}

touch .finished
