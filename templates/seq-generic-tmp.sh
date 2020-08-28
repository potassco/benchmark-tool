#!/bin/bash
# http://www.cril.univ-artois.fr/~roussel/runsolver/

CAT="{run.root}/programs/gcat.sh"

cd "$(dirname $0)"

ID=`echo $PBS_JOBID | sed  's/\([0-9]*\).*/\1/g'`

MASK=`qstat -f $ID | python {run.root}/templates/mask.py`

TF=`mktemp -p .`
$CAT "{run.file}" > $TF 

[[ -e .finished ]] || taskset $MASK  "{run.root}/programs/runsolver-3.3.3" \
	-M 100000 \
	-w runsolver.watcher \
	-o runsolver.solver \
	-W {run.timeout} \
	"{run.root}/programs/{run.solver}" {run.args} $TF


rm $TF

echo $HOSTNAME > hostname.txt

[[ -e runsolver.watcher ]] && touch .finished

