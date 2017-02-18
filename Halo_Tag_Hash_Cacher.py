import tkinter.filedialog
import time

from os.path import dirname
from tkinter import *
from traceback import format_exc

from ripper.hash_cacher import HashCacher

curr_dir = dirname(__file__)
DEF_NAME = 'enter cache name'
DEF_DESC = 'enter cache description'

RESERVED_WINDOWS_FILENAME_MAP = {}
INVALID_PATH_CHARS = set([str(i.to_bytes(1, 'little'), 'ascii')
                          for i in range(32)])
for name in ('CON', 'PRN', 'AUX', 'NUL'):
    RESERVED_WINDOWS_FILENAME_MAP[name] = '_' + name
for i in range(1, 9):
    RESERVED_WINDOWS_FILENAME_MAP['COM%s' % i] = '_COM%s' % i
    RESERVED_WINDOWS_FILENAME_MAP['LPT%s' % i] = '_LPT%s' % i
INVALID_PATH_CHARS.add(('<', '>', ':', '"', '/', '\\', '|', '?', '*'))

def sanitize_filename(name):
    # make sure to rename reserved windows filenames to a valid one
    if name in RESERVED_WINDOWS_FILENAME_MAP:
        return RESERVED_WINDOWS_FILENAME_MAP[name]
    final_name = ''
    for c in name:
        if c not in INVALID_PATH_CHARS:
            final_name += c
    if final_name == '':
        raise Exception('BAD %s CHAR FILENAME' % len(name))
    return final_name


class Hashcacher(Tk):
    tags_path = None
    hash_name = None

    cacher = None

    def __init__(self, **kwargs):
        tags_path = kwargs.pop('tags_path', curr_dir + '\\tags')
        hash_name = kwargs.pop('hash_name', '')
        hash_desc = kwargs.pop('hash_desc', '')

        Tk.__init__(self, **kwargs)

        self.title("Halo Hashcacher v1.0")
        self.geometry("400x300+0+0")
        self.resizable(0, 0)

        self.tags_path = StringVar(self, tags_path)
        self.hash_name = StringVar(self, hash_name)

        self.cacher = HashCacher()

        # add the tags folder path box
        self.tags_path_entry = Entry(self, textvariable=self.tags_path)
        self.tags_path_entry.config(width=47, state=DISABLED)

        # add the hashcache name box
        self.hash_name_entry = Entry(self, textvariable=self.hash_name)
        self.hash_name_entry.config(width=47)

        # add the hashcache description box
        self.hash_desc_text = Text(self)
        self.hash_desc_text.config(height=15, width=55, wrap='word')
        self.hash_desc_text.insert('end', hash_desc)

        # add the buttons
        self.btn_select_tags = Button(self, text="Select tags folder",
                                      width=15, command=self.select_tags_folder)
        self.btn_build_cache = Button(self, text="Build hashcache",
                                      width=15, command=self.build_cache)

        # place the buttons and tags path field
        self.tags_path_entry.place(x=5, y=7, anchor=NW)
        self.hash_name_entry.place(x=5, y=37, anchor=NW)
        self.hash_desc_text.place(x=5, y=65, anchor=NW)

        self.btn_select_tags.place(x=295, y=5, anchor=NW)
        self.btn_build_cache.place(x=295, y=35, anchor=NW)

    def select_tags_folder(self):
        tags_path = filedialog.askdirectory(
            initialdir=self.tags_path.get(), title="Select tags folder...")
        tags_path = tags_path.replace('/','\\') + '\\'
        if tags_path:
            self.tags_path.set(tags_path)

    def build_cache(self):
        try:
            hash_name = sanitize_filename(self.hash_name.get())
        except Exception:
            hash_name = ''

        hash_desc = self.hash_desc_text.get(1.0, 'end')

        if hash_name in (DEF_NAME, ''):
            print('enter a valid hashcache name.')
        elif hash_desc == DEF_DESC:
            print('enter a hashcache description.')
        else:
            start = time.time()
            self.cacher.build_hashcache(
                hash_name, hash_desc, self.tags_path.get())
            print('Hashing completed. Took %s seconds' % (time.time() - start))

try:
    if __name__ == '__main__':
        extractor = Hashcacher(
            hash_name='Halo_1_Default',
            #hash_name=DEF_NAME, hash_desc=DEF_DESC,
            tags_path=(curr_dir +
                "\\reclaimer\\halo\\hek\\programs\\ripper\\all_h1_tags\\"),
            hash_desc=('All the tags that are used in the original Halo 1 ' +
                       'singleplayer, multiplayer, and ui maps.\n' +
                       'This should always be used, and as the base cache.')
            )
        extractor.mainloop()
except:
    print(format_exc())
    input()
