#!/bin/bash
# https://github.com/arminbiere/runlim

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

#top -n 1 -b > top.txt

[[ -e .finished ]] || "{run.root}/programs/runlim" \
	--space-limit={run.memout} \
	--output-file=runsolver.watcher \
	--real-time-limit={run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args} {run.files} {run.encodings} > runsolver.solver

touch .finished
