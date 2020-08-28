#!/usr/bin/python

import sys

CPU=0
CORE=1
SOCKET=2
NODE=3

sockets = {}
nodes = {}
cpus = {}

for line in sys.stdin:
    if not line.startswith("#"):
        row = line.split(",")
        sockets.setdefault(int(row[SOCKET]), {}).setdefault(int(row[CORE]), []).append(int(row[CPU]))
        nodes.setdefault(int(row[NODE]), []).append((int(row[CORE]),int(row[CPU])))

for socket_id in sorted(sockets.keys()):
    socket = sockets[socket_id]
    i = 0
    found = True
    while found:
        found = False
        for core_id in sorted(sockets[socket_id].keys(), reverse=True):
            core = socket[core_id]
            if i < len(core):
                found = True
                cpus[core[i]] = len(cpus)
        i+= 1

p = int(sys.argv[1])
n = int(sys.argv[2])

node_keys = sorted(nodes.keys())
node_id = p % len(node_keys)
selected_cpus = nodes[node_keys[node_id]]
selected_cpus.sort(key = lambda (core_id, cpu_id): (cpus[cpu_id], core_id, cpu_id))

per_node = max(1, n / len(node_keys))
selected_cpus = selected_cpus[:per_node]
selected_cpu = selected_cpus[((p + node_id) / len(node_keys)) % per_node][1]

print selected_cpu
