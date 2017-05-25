import tkinter as tk

from os.path import join
from threading import Thread
from tkinter.filedialog import askdirectory
from traceback import format_exc

from reclaimer.os_v4_hek.handler import OsV4HaloHandler
from supyr_struct.defs.constants import *


RESERVED_WINDOWS_FILENAME_MAP = {}
INVALID_PATH_CHARS = set([str(i.to_bytes(1, 'little'), 'ascii')
                          for i in range(32)])
for name in ('CON', 'PRN', 'AUX', 'NUL'):
    RESERVED_WINDOWS_FILENAME_MAP[name] = '_' + name
for i in range(1, 9):
    RESERVED_WINDOWS_FILENAME_MAP['COM%s' % i] = '_COM%s' % i
    RESERVED_WINDOWS_FILENAME_MAP['LPT%s' % i] = '_LPT%s' % i
INVALID_PATH_CHARS.update('<>:"|?*')

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


class HashcacherWindow(tk.Toplevel):
    handler = None
    app_root = None
    tags_dir = None
    hash_name = None

    _hashing = False

    def __init__(self, app_root, *args, **kwargs):
        self.app_root = app_root
        self.handler = kwargs.pop("handler", None)
        kwargs.update(width=400, height=300, bd=0, highlightthickness=0)
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)

        if self.handler is None:
            self.handler = OsV4HaloHandler(
                id_ext_map=id_ext_map, defs=defs, reload_defs=not defs)

        self.title("Hashcacher")
        self.minsize(width=400, height=300)

        self.tags_dir = tk.StringVar(self)
        self.hash_dir = tk.StringVar(self)
        self.hash_name = tk.StringVar(self)
        try:
            tags_dir = app_root.tags_dir
            if tags_dir:
                self.tags_dir.set(tags_dir)
                self.hash_dir.set(tags_dir)
        except Exception:
            pass

        # add the tags folder path box
        self.tags_dir_frame = tk.LabelFrame(
            self, text="Select the root tags directory")
        self.tags_dir_entry = tk.Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=47, state='disabled')

        # add the hash folder path box
        self.hash_dir_frame = tk.LabelFrame(
            self, text="Select the subdirectory to hash")
        self.hash_dir_entry = tk.Entry(
            self.hash_dir_frame, textvariable=self.hash_dir)
        self.hash_dir_entry.config(width=47, state='disabled')

        # add the hashcache name box
        self.hash_name_frame = tk.LabelFrame(
            self, text="Enter a valid hashcache name")
        self.hash_name_entry = tk.Entry(
            self.hash_name_frame, textvariable=self.hash_name)
        self.hash_name_entry.config(width=47)

        # add the hashcache description box
        self.hash_desc_frame = tk.LabelFrame(
            self, text="Enter a hashcache description")
        self.hash_desc_text = tk.Text(self.hash_desc_frame)
        self.hash_desc_text.config(height=50, wrap='word')

        # add the buttons
        self.tags_dir_button = tk.Button(
            self.tags_dir_frame, text="Browse", width=15,
            command=self.select_tags_dir)
        self.hash_dir_button = tk.Button(
            self.hash_dir_frame, text="Browse", width=15,
            command=self.select_hash_dir)
        self.btn_build_cache = tk.Button(
            self.hash_name_frame, text="Build hashcache",
            width=15, command=self.build_hashcache)

        # pack everything
        self.tags_dir_frame.pack(padx=4, pady=4, fill='x')
        self.hash_dir_frame.pack(padx=4, pady=4, fill='x')
        self.hash_name_frame.pack(padx=4, pady=4, fill='x')
        self.hash_desc_frame.pack(padx=4, pady=4, fill='x')
        self.hash_desc_text.pack(padx=4, pady=4, expand=True, fill='both')

        for entry in (self.tags_dir_entry, self.hash_dir_entry,
                      self.hash_name_entry):
            entry.pack(side='left', padx=4, pady=2, expand=True, fill='x')

        for button in (self.tags_dir_button, self.hash_dir_button,
                       self.btn_build_cache):
            button.pack(side='right', padx=4, pady=2)

        # REMOVE THESE LINES WHEN READY FOR PUBLIC USAGE
        self.hash_name.set('Halo_1_Default')
        self.hash_desc_text.insert(
            'end', 'All the tags that are used in the original Halo 1 ' +
            'singleplayer, multiplayer, and ui maps.\n' +
            'This should always be used, and as the base cache.')
        # REMOVE THESE LINES WHEN READY FOR PUBLIC USAGE

        self.transient(app_root)

    def destroy(self):
        self.app_root.tool_windows.pop("hashcacher_window", None)
        tk.Toplevel.destroy(self)
        self.app_root.hashcacher.stop_hashing = True

    def select_tags_dir(self):
        tags_dir = askdirectory(initialdir=self.tags_dir.get(), parent=self,
                                title="Select the root tags directory...")
        if tags_dir:
            tags_dir = sanitize_path(tags_dir) 
            if not tags_dir.endswith(PATHDIV):
                tags_dir += PATHDIV
            self.tags_dir.set(tags_dir)
            self.hash_dir.set(tags_dir)

    def select_hash_dir(self):
        hash_dir = askdirectory(initialdir=self.hash_dir.get(), parent=self,
                                title="Select the subdirectory to hash...")
        if hash_dir:
            hash_dir = sanitize_path(hash_dir)
            if not hash_dir.endswith(PATHDIV):
                hash_dir += PATHDIV

            tags_dir = self.tags_dir.get()
            if not (is_in_dir(hash_dir, tags_dir, 0) or
                    join(hash_dir.lower()) == join(tags_dir.lower())):
                print("Hash directory must be within the root tags directory")
                return
            self.hash_dir.set(hash_dir)

    def build_hashcache(self):
        if self._hashing:
            return
        try: self.build_thread.join(1.0)
        except Exception: pass
        self.build_thread = Thread(target=self._build_hashcache)
        self.build_thread.daemon = True
        self.build_thread.start()

    def _build_hashcache(self):
        self._hashing = True
        try:
            try:
                hash_name = sanitize_filename(self.hash_name.get())
            except Exception:
                hash_name = ''

            hash_desc = self.hash_desc_text.get(1.0, 'end')
            hasher, tag_lib = self.app_root.hashcacher, self.handler
            hasher.stop_hashing = False

            if not hash_name:
                print('enter a valid hashcache name.')
            elif not hash_desc:
                print('enter a hashcache description.')
            else:
                # set the hashcachers tag_lib to the currently selected handler
                tag_lib.tagsdir = self.tags_dir.get()
                hasher.tag_lib = tag_lib
                hasher.build_hashcache(hash_name, hash_desc,
                                       self.hash_dir.get())
        except Exception:
            print(format_exc())
        self._hashing = False
