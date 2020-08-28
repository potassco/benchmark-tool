#!/bin/bash

# $1:  name of the experiment
name=$1

# set this
btool=$HOME/git/benchmark-tool

# this has to be the same as project name in run-benchmark.xml
project=project

# this has to be the command used in run-benchmark.xml
command=$PWD/solver.sh

# set mode: sequential=1 or cluster=2
mode=2

# if mode==2, set username to your login in the cluster
username=""

# email to send the results
email=""

dir=$PWD
bench=$dir/run-benchmark.xml

echo "start execution..."
rm -rf $dir/results/$name
mkdir -p $dir/results/$name 
cd $btool
rm -rf output/$project

echo "bgen..."
./bgen $bench

if [ $mode -eq 1 ]; then
    echo "$btool/output/$project/zuse/start.py..."
    ./output/$project/zuse/start.py
else
    echo "$btool/output/$project/zuse/start.sh..."
    ./output/$project/zuse/start.sh
    while squeue | grep -q $username; do
        sleep 1
    done
fi

echo "beval..."
./beval $bench > $dir/results/$name/$name.beval 2> $dir/results/$name/$name.error

echo "bconv..."
cat $dir/results/$name/$name.beval | ./bconv -m time,ctime,csolve,ground0,groundN,models,timeout,restarts,conflicts,choices,domain,vars,cons,mem,error,memout > $dir/results/$name/$name.ods 2>> $dir/results/$name/$name.error

echo "tar..."
tar -czf $name.tar.gz output/$project
mv $name.tar.gz $dir/results/$name
cp $bench $dir/results/$name
cp $command $dir/results/$name
rm -rf output/$project

echo "done"
echo $dir/results/$name/$name.ods
# send an email to report that the experiments are done
echo "done $1" | mail -s "[benchmark_finished] $1 " -A $dir/results/$name/$name.ods $email

