#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

try:
    from traceback import format_exc
    try:
        from refinery.main import *
    except Exception:
        Refinery = None
        input("Refinery is not installed. Install it with the MEK installer to fix this.")

    if Refinery:
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
