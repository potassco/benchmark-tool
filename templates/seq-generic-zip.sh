#!/bin/bash
# https://github.com/arminbiere/runlim

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

#top -n 1 -b > top.txt

[[ -e .finished ]] || $CAT {run.files} {run.encodings} | "{run.root}/programs/runlim" \
	--space-limit=20000 \
	--output-file=runsolver.watcher \
	--real-time-limit={run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args} > runsolver.solver

touch .finished
