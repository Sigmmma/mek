#!/usr/bin/env python3

import os
from traceback import format_exc
try:
    import mek_lib  # sets up sys.path properly
    import arbytmap
    from mek_lib.hboc.bitmap_optimizer_and_converter import *

    # setting debug to 1 or higher will disable log file creation,
    # and instead make it so it is always printed to the console.
    converter = BitmapConverter(debug = 0)
    if arbytmap.fast_arbytmap:
        print("C accelerator modules are installed and will be used.")
    else:
        print("C accelerator modules are not installed and cannot be used.")

    #loop the main window
    converter.root_window.mainloop()
except SystemExit:
    pass
except Exception:
    print(format_exc())
    input()