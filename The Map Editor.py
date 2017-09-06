#!/usr/bin/env python3

print("The Map Editor is warming up...")

try:
    from traceback import format_exc
    from refinery.main import *

    class TheMapEditor(Refinery):

        def __init__(self, *args, **kwargs):
            Refinery.__init__(self, *args, **kwargs)
            self.title("The Map Editor" +
                       self.title().lower().split('refinery')[-1])

    extractor = TheMapEditor()
    extractor.mainloop()
except Exception:
    print(format_exc())
    input()
