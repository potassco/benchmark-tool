# A simple script to dispatch jobs to a SLURM cluster.
# It checks the number of running jobs for a given user
# and dispatches jobs from a specified folder
# until the maximum number of jobs is reached.

# Arguments:
# -f, --folder: folder where the files to dispatch are (default: current directory)
# -u, --username: username to monitor (default: current user)
# -j, --maxjobs: maximum number of jobs running at once (default: 100)
# -w, --wait-time: time to wait between checks in seconds (default: 1)

# Example usage from inside the folder with the jobs:
# `python ../../../dispatcher.py -f . -j 100 -w 1`

# Notes:
# This script should be used in conjunction with "screen" to setup a long-running job dispatcher.
# First, start a screen session running the command(For more information on screen, see `man screen`):
# `screen`
# Or continue an existing session with:
# `screen -r`
# Then, run this script from within the screen session.
# To exit the screen session, use Ctrl+A followed by D.
# The jobs will continue to be dispatched in the background.


import argparse
import os
import subprocess
import time


def check_running_jobs(username: str) -> int:
    process = subprocess.run(["squeue", "-u", username], capture_output=True, encoding="UTF-8")
    return len(process.stdout.split("\n")) - 2


def dispatch(folder: str, maxjobs: int, username: str, wait_time: int = 1):
    dispatched_jobs = 0
    total_jobs = 0

    # read files to dispatch from folder
    jobs = []

    jobs = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.endswith(".dist")]
    jobs = sorted(jobs)
    total_jobs = len(jobs)
    print(f"Found {total_jobs} jobs to dispatch")

    # check if there are less than maxjobs
    # if so, dispatch enough jobs to get to the max
    while jobs:
        to_dispatch = min(maxjobs - check_running_jobs(username), len(jobs))
        if to_dispatch > 0:
            for i in range(to_dispatch):
                job = jobs.pop()
                dispatch_job(job)

            dispatched_jobs += to_dispatch
            print(f"Dispatched {dispatched_jobs} out of {total_jobs}.")

        time.sleep(wait_time)

    print("Finished!")


def dispatch_job(job):
    subprocess.run(["sbatch", os.path.abspath(job)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="dispatcher",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-f", "--folder", help="folder where the files to dispatch are", type=str, default=".")
    parser.add_argument("-u", "--username", help="Username to monitor", type=str, default=None)
    parser.add_argument("-j", "--maxjobs", help="Maximum number of jobs running at once", type=int, default=100)
    parser.add_argument("-w", "--wait-time", help="Time to wait between checks in seconds", type=int, default=1)

    args, _ = parser.parse_known_args()
    # Probably good to check that username is valid somehow (if given as argument)
    # if maxjobs provided is higher than actual allowance this script fails(probably)
    # give warning if wait time is too high? might not make sense to wait 1 day between checks...

    username = args.username
    if args.username is None:
        username = subprocess.run(["whoami"], capture_output=True, encoding="UTF-8").stdout.strip()
        print(f"Using username: {username}")

    dispatch(folder=args.folder, maxjobs=args.maxjobs, username=username, wait_time=args.wait_time)
