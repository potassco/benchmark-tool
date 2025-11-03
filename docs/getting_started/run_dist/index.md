---
title: "Dispatcher for distributed jobs"
icon: "material/play-outline"
---

The `run-dist` subcommand can be used to dispatch distributed jobs of a
generated benchmark to a cluster to avoid exceeding the maximum number of
jobs running or in queue. To run the command simply provide the folder,
which contains the distributed job files (*.dist).

```bash
btool run-dist <folder>
```

The `-u, --user` option can be used to specify the user to monitor
(default: current user).

`-j, --jobs` can be used specify the maximum number of jobs running at once
(default: 100)

The `-w, --wait` option sets the number of seconds between checking the number
of jobs on the cluster (default: 1)

!!!info
    Make sure to use a `run-dist` inside a persistent shell (tmux, screen, ...)
    or using nohub.
