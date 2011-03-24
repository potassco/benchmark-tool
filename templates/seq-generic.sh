#!/bin/bash

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

[[ -e .finished ]] || $CAT "{run.file}" | "{run.root}/programs/runsolver-3.2.5" \
	-M 100000 \
	-w runsolver.watcher \
	-o runsolver.solver \
	-W {run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args}

touch .finished
