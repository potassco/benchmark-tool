$!"#"+"!/bin/bash"!$

cd $(dirname $0)

$!run.root()!$/programs/runsolver \
	-w runsolver.watcher \
	-o runsolver.solver \
	1> runsolver.stderr \
	2> runsolver.stdout \
	-W $!run.timeout().seconds()!$ \
	$!run.root()!$/programs/$!run.solver()!$ $!run.args()!$ \
	< $!run.file()!$
