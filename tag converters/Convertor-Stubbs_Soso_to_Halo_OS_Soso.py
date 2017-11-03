#!/usr/bin/env python3

import os, struct

from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

from supyr_struct.defs.util import fcc, FieldParseError
from supyr_struct.defs.constants import PATHDIV
from supyr_struct.defs.block_def import BlockDef
from reclaimer.os_v3_hek.defs.soso import soso_def
from reclaimer.stubbs.defs.soso    import soso_def as stubbs_soso_def
from reclaimer.common_descs import tag_header_os


tag_header_def = BlockDef(tag_header_os)

PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV


def convert_soso_tag(soso_path):
    # make a new tag and load the stubbs one
    soso_tag   = soso_def.build()
    soso_attrs = soso_tag.data.tagdata.soso_attrs
    stubbs_soso_tag   = stubbs_soso_def.build(filepath=soso_path)
    stubbs_soso_attrs = stubbs_soso_tag.data.tagdata.soso_attrs

    soso_tag.data.tagdata.shdr_attrs = stubbs_soso_tag.data.tagdata.shdr_attrs

    soso_attrs.model_shader          = stubbs_soso_attrs.model_shader
    soso_attrs.color_change_source   = stubbs_soso_attrs.color_change_source
    soso_attrs.self_illumination     = stubbs_soso_attrs.self_illumination
    soso_attrs.maps                  = stubbs_soso_attrs.maps
    soso_attrs.texture_scrolling     = stubbs_soso_attrs.texture_scrolling
    soso_attrs.reflection_properties = stubbs_soso_attrs.reflection_properties

    # make a new shader extension for the bump map
    soso_ext = soso_attrs.os_shader_model_ext.STEPTREE
    soso_ext.extend(1)
    b = soso_ext[-1]
    bump_props = stubbs_soso_attrs.bump_properties
    b.base_normal_coefficient  = bump_props.bump_scale
    b.base_normal_map.filepath = bump_props.bump_map.filepath

    # replace the filepath
    soso_tag.filepath = stubbs_soso_tag.filepath

    return soso_tag


class StubbsSosoConverter(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Stubbs soso tag converter v1.0")
        self.geometry("400x80+0+0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)

        # make the frames
        self.tags_dir_frame = LabelFrame(
            self, text="Directory of shader_model tags")

        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.convert_btn = Button(
            self, text="Convert", width=15, command=self.convert)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='x', side='left')
        self.tags_dir_frame.pack(expand=True, fill='both')
        self.convert_btn.pack(fill='both', padx=5, pady=5)

    def destroy(self):
        Tk.destroy(self)
        raise SystemExit(0)
        
    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def convert(self):
        print('Converting shader_models\n')
        start = time()
        tags_dir = self.tags_dir.get()

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        for root, dirs, files in os.walk(tags_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if not os.path.splitext(filename)[-1].lower() == '.shader_model':
                    continue

                try:
                    blam_header = tag_header_def.build(filepath=filepath)
                    if blam_header.version != 3:
                        continue

                    print(filepath.split(tags_dir)[-1])

                    tag = convert_soso_tag(filepath)
                    if tag is None:
                        continue
                except Exception:
                    print(format_exc())
                    print("Could not convert:   %s" % filepath)
                    continue

                tag.serialize(temp=False, backup=False, int_test=False)
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = StubbsSosoConverter()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

