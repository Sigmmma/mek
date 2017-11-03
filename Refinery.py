#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

try:
    from refinery.main import *
    from traceback import format_exc

    extractor = Refinery()
    extractor.mainloop()
except Exception:
    print(format_exc())
    input()
