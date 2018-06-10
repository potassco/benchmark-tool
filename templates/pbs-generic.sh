#!/bin/bash

function abort()
{{
	echo TIMEOUT!
	kill $MPI_PID > /dev/null 2>&1
}}

function run()
{{
	# does not work because this will only kill mpiexec
	trap abort SIGUSR1
	/usr/bin/time -f "Real time (s): %e" -o runsolver.watcher \
	{run.command} {run.file} {run.options} \
	> runsolver.solver 2>&1 &
	export MPI_PID=$!
	export BASH_PID=$$
	(sleep $[{run.timeout}+10]; kill -SIGUSR1 $BASH_PID) &
	sleep_pid=$!
	wait $MPI_PID > /dev/null 2>&1
	kill $sleep_pid
}}

function run2()
{{
    echo PBS_NODEFILE $PBS_NODEFILE
    echo PBS_NODES $PBS_NODES
    MPIEXEC_TIMEOUT={run.timeout} \
		mpiexec -machinefile $PBS_NODEFILE -n $PBS_NODES \
         {run.command} {run.file} {run.options} \ 
		> runsolver.solver 2>&1
}}


case $1 in 
	run)
		run
		;;
	run2)
		run2
		;;
	*)    
        cd "$(dirname $0)"
		#zcat "{run.file}" > instance
		cat "{run.file}" > instance
		[[ -e .finished ]] || /usr/bin/time -f "Real time (s): %e" -o runsolver.watcher "./$(basename $0)" run2
		touch .finished
		rm -f instance
		;;
esac
