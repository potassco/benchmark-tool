#!/bin/bash
# https://github.com/arminbiere/runlim

cd "$(dirname $0)"

#top -n 1 -b > top.txt

[[ -e .finished ]] || "{run.root}/programs/runlim-2.0.0rc6" \
	--space-limit=20000 \
	--output-file=runsolver.watcher \
	--time-limit={run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args} {run.file} > runsolver.solver

touch .finished
