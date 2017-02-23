import os, sys, subprocess

info = sys.version_info

if info[0] < 3:
    input(
        "You must have python 3 or higher installed to run Mozzarilla.\n" +
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)

for mod in ("arbytmap", "supyr_struct", "binilla", "reclaimer", "mozzarilla"):
    exec_str = "pip install %s --upgrade" % mod
    print("executing:  %s" % exec_str)
    subprocess.call(exec_str)
