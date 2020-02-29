#!/usr/bin/env python3

import sys

info = sys.version_info

if info[0] < 3:
    input(
        "You must have python 3.5 or higher installed to run Mozzarilla.\n"
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)

try: import mek_lib  # setup sys.path properly if portably installed
except ImportError: pass

try:
    try:
        from mozzarilla.__main__ import main
        main()
    except ImportError:
        input("Mozzarilla is not (properly) installed. Install it with the MEK installer to fix this.")
except SystemExit:
    pass
