print("The Map Editor is warming up...")
from Refinery import *


class TheMapEditor(Refinery):

    def __init__(self, *args, **kwargs):
        Refinery.__init__(self, *args, **kwargs)
        self.title("The Map Editor" +
                   self.title().lower().split('refinery')[-1])


if __name__ == "__main__":
    try:
        extractor = TheMapEditor()
        extractor.mainloop()
    except Exception:
        print(format_exc())
        input()
