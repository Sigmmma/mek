#!/usr/bin/env python3

import os, sys

info = sys.version_info

if info[0] < 3:
    input(
        "You must have python 3 or higher installed to run HekPool.\n" +
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)

from datetime import datetime
from traceback import format_exc

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

try:
    try:
        from hek_pool.app_window import HekPool
    except ImportError:
        HekPool = None
        input("HEK Pool is not installed. Install it with the MEK installer to fix this.")

    if HekPool:
        main_window = HekPool()
        main_window.mainloop()
except SystemExit:
    pass
except Exception:
    exception = format_exc()
    try:
        with open('STARTUP_CRASH.LOG', 'a+') as cfile:
            time = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            cfile.write("\n%s%s%s\n" % ("-"*30, time, "-"*(50-len(time))))
            cfile.write(time + exception)
    except Exception:
        pass
    print(exception)
    input()
