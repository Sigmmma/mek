import os
from traceback import format_exc

try:
    from binilla.app_window import Binilla
    from binilla.handler import Handler

    if __name__ == "__main__":
        misc_handler = Handler(defs_path='reclaimer.misc.defs')
        main_window = Binilla(
            curr_dir=os.path.abspath(os.curdir).replace('/', '\\'),
            handler=misc_handler)
        main_window.mainloop()

except Exception:
    print(format_exc())
    input()
