import os, sys, subprocess, traceback

info = sys.version_info

if info[0] < 3:
    input(
        "You must have python 3 or higher installed to run Mozzarilla.\n" +
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)

try:
    exec_str = "pip install mozzarilla"
    print("executing:  %s" % exec_str)
    subprocess.call(exec_str)
    print("executing:  python -m %s" % exec_str)
    subprocess.call("python -m " + exec_str)
except Exception:
    print(traceback.format_exc())

input()
raise SystemExit(0)
