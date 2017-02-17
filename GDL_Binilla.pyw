import os
from traceback import format_exc

try:
    from reclaimer.gdl.gdl_binilla.app_window import GdlBinilla

    if __name__ == "__main__":
        main_window = GdlBinilla(debug=3, curr_dir=os.path.abspath(os.curdir))
        main_window.mainloop()

except Exception:
    print(format_exc())
    input()
