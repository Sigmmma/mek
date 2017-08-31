#!/usr/bin/env python3

import os
from traceback import format_exc
from arbytmap import arbytmap
try:
    from hboc.bitmap_optimizer_and_converter import *

    # setting debug to 1 or higher will disable log file creation,
    # and instead make it so it is always printed to the console.
    converter = BitmapConverter(debug = 0)
    if arbytmap.fast_raw_packer and arbytmap.fast_raw_unpacker:
        print("C accelerator modules are installed and will be used.")
    else:
        print("C accelerator modules are not installed and cannot be used.")
        
    #loop the main window
    converter.root_window.mainloop()

    os._exit(0)
except SystemExit:
    pass
except Exception:
    print(format_exc())
    input()
