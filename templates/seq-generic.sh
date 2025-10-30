#!/bin/bash
# https://github.com/arminbiere/runlim

cd "$(dirname $0)"

[[ -e .finished ]] || "{run.root}/programs/runlim" \
	--space-limit={run.memout} \
	--output-file=runsolver.watcher \
	--real-time-limit={run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args} {run.files} {run.encodings} > runsolver.solver

touch .finished
