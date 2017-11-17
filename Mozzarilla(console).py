#!/usr/bin/env python3

import os, sys

info = sys.version_info

if info[0] < 3:
    input(
        "You must have python 3 or higher installed to run Mozzarilla.\n" +
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)

from datetime import datetime
from traceback import format_exc

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

try:
    try:
        from mozzarilla.app_window import Mozzarilla
    except Exception:
        Mozzarilla = None
        input("Mozzarilla is not installed. Install it with the MEK installer to fix this.")

    if Mozzarilla:
        main_window = Mozzarilla(debug=3)
        main_window.mainloop()
except SystemExit:
    pass
except Exception:
    exception = format_exc()
    try:
        main_window.log_file.write('\n' + exception)
    except Exception:
        try:
            with open('startup_crash.log', 'a+') as cfile:
                time = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
                cfile.write("\n%s%s%s\n" % ("-"*30, time, "-"*(50-len(time))))
                cfile.write(time + exception)
        except Exception:
            pass
    print(exception)
    input()
