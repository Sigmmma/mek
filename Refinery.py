#!/usr/bin/env python3

try:
    from traceback import format_exc
    from refinery.main import *

    extractor = Refinery()
    extractor.mainloop()
except Exception:
    print(format_exc())
    input()
