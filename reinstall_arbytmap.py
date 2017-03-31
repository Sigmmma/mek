import os, sys, subprocess, traceback

info = sys.version_info

if info[0] < 3:
    input(
        "You must have python 3 or higher installed to run Mozzarilla.\n" +
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)


try:
    print("executing:  pip uninstall arbytmap -y")
    subprocess.call("pip uninstall arbytmap -y")

    print("executing: pip install arbytmap")
    subprocess.call("pip install arbytmap")

    input("Finished")
    raise SystemExit(0)
except Exception:
    print(traceback.format_exc())

try:
    print("executing:  python -m pip uninstall arbytmap -y")
    subprocess.call("pip uninstall arbytmap -y")

    print("executing:  python -m pip install arbytmap")
    subprocess.call("python -m pip install arbytmap")
except Exception:
    print(traceback.format_exc())

input("Finished")
raise SystemExit(0)
