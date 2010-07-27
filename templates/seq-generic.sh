#!/bin/bash

cd "$(dirname $0)"

[[ -e .finished ]] || zcat "{run.file}" | "{run.root}/programs/runsolver-3.2.5" \
	-M 100000 \
	-w runsolver.watcher \
	-o runsolver.solver \
	1> runsolver.stderr \
	2> runsolver.stdout \
	-W {run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args}

touch .finished
