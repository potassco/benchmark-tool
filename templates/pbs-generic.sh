#!/bin/bash

cd "$(dirname $0)"

[[ .finished -nt start.sh ]] || "{run.root}/programs/runsolver-3.2.5" \
	-w runsolver.watcher \
	-o runsolver.solver \
	1> runsolver.stderr \
	2> runsolver.stdout \
	-W {run.timeout} \
	mpiexec -machinefile $PBS_NODEFILE -n $PBS_NODES \
	"{run.root}/programs/{run.solver}" {run.args} \
	< "{run.file}"

touch .finished
