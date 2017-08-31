#!/usr/bin/env python3

try:
    from traceback import format_exc
    from refinery_core.main import *

    extractor = Refinery()
    extractor.mainloop()
except Exception:
    print(format_exc())
    input()
