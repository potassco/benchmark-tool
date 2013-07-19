#!/bin/bash
# http://www.cril.univ-artois.fr/~roussel/runsolver/

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

#top -n 1 -b > top.txt

core=$(($1+2))

[[ -e .finished ]] || $CAT "{run.file}" | taskset -c $core "{run.root}/programs/runsolver-3.3.3" \
	-M 4000 \
	-w runsolver.watcher \
	-o runsolver.solver \
	-W {run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args}

touch .finished
