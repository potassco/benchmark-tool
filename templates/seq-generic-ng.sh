#!/bin/bash
# http://www.cril.univ-artois.fr/~roussel/runsolver/

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

core=$(lscpu -p | "{run.root}/programs/map_core.py" $1 {run.job.parallel})

[[ -e .finished ]] || $CAT "{run.file}" | {run.root}/programs/runsolver-3.3.4 --phys-cores $core \
	-M 20000 \
	-w runsolver.watcher \
	-o runsolver.solver \
	-W {run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args}

touch .finished
