import os, sys, subprocess

info = sys.version_info

if info[0] < 3:
    input(
        "You must have python 3 or higher installed to run Mozzarilla.\n" +
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)

exec_str = "pip install mozzarilla"
print("executing:  %s" % exec_str)
subprocess.call(exec_str)
