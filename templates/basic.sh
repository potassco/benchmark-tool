#!/bin/bash
cd "$(dirname $0)"
[[ -e .finished ]] || "{run.root}/programs/{run.solver}"  {run.memory} {run.timeout} {run.command} {run.file} {run.options}
touch .finished
