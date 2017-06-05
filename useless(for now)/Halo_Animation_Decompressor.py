import os, supyr_struct

from math import sqrt
from struct import pack_into
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.defs.constants import PATHDIV, MOST_SHOW
from supyr_struct.defs.block_def import BlockDef
from reclaimer.hek.defs.antr import antr_def

PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV


class AnimationDecompressor(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Animation Decompressor v1.0")
        self.geometry("400x70+0+0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)

        # make the frame
        self.tags_dir_frame = LabelFrame(self, text="Tags directory")
        
        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.decompress_btn = Button(
            self, text="Decompress animations", width=22,
            command=self.decompress_animations)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='both', side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.decompress_btn.pack(fill='both', padx=5, pady=5)

    def destroy(self):
        Tk.destroy(self)
        #raise SystemExit(0)
        os._exit(0)

    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def decompress_animations(self):
        print('Decompressing animations\n')
        start = time()
        tags_dir = self.tags_dir.get()

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        for root, dirs, files in os.walk(tags_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if os.path.splitext(filename)[-1].lower() != '.model_animations':
                    continue
                elif filename.startswith('DECOMP_'):
                    continue

                print('Decompressing %s' % filepath.split(tags_dir)[-1])

                antr_tag = antr_def.build(filepath=filepath)

                # rename the tag to the decompressed filepath
                dirpath, filename = os.path.split(filepath)
                antr_tag.filepath = dirpath + PATHDIV + "DECOMP_" + filename

                anims = antr_tag.data.tagdata.animations.STEPTREE
                decomp_count = 0
                for i in range(len(anims)):
                    if not anims[i].flags.compressed_data:
                        continue
                    try:
                        decomp_count += antr_tag.decompress_anim(i)
                    except Exception:
                        anims[i].flags.compressed_data = False
                        print(format_exc())
                        print("    Could not decompress %s" % anims[i].name)
                        anims[i].name = ('CORRUPT_' + anims[i].name)[:31]

                if decomp_count:
                    antr_tag.serialize(temp=False, backup=False)

                del antr_tag
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = AnimationDecompressor()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

