#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

import os

from math import sqrt
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.defs.util import fcc
from supyr_struct.defs.constants import PATHDIV
from reclaimer.hek.defs.mod2    import fast_mod2_def as mod2_def
from reclaimer.stubbs.defs.mode import fast_mode_def as mode_def


PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV



def convert_model(src_tag, dst_tag, to_gbxmodel):
    src_tag_data = src_tag.data.tagdata
    dst_tag_data = dst_tag.data.tagdata

    # move the first 14 header fields from src tag into dst tag
    # (except for the flags since usually ZONER shouldnt be copied)
    dst_tag_data[1: 14] = src_tag_data[1: 14]
    for flag_name in src_tag_data.flags.NAME_MAP:
        if hasattr(dst_tag_data.flags, flag_name):
            dst_tag_data.flags[flag_name] = src_tag_data.flags[flag_name]

    # fix the fact the mode and mod2 store stuff related to lods
    # in reverse on most platforms(pc stubbs is an exception)
    if dst_tag_data.superhigh_lod_cutoff < dst_tag_data.superlow_lod_cutoff:
        tmp0 = dst_tag_data.superhigh_lod_cutoff
        tmp1 = dst_tag_data.high_lod_cutoff
        dst_tag_data.superhigh_lod_cutoff = dst_tag_data.superlow_lod_cutoff
        dst_tag_data.high_lod_cutoff      = dst_tag_data.low_lod_cutoff
        dst_tag_data.low_lod_cutoff       = tmp1
        dst_tag_data.superlow_lod_cutoff  = tmp0

        tmp0 = dst_tag_data.superhigh_lod_nodes
        tmp1 = dst_tag_data.high_lod_nodes
        dst_tag_data.superhigh_lod_nodes = dst_tag_data.superlow_lod_nodes
        dst_tag_data.high_lod_nodes      = dst_tag_data.low_lod_nodes
        dst_tag_data.low_lod_nodes       = tmp1
        dst_tag_data.superlow_lod_nodes  = tmp0

    # make all markers global ones
    if hasattr(src_tag, "globalize_local_markers"):
        src_tag.globalize_local_markers()

    # move the markers, nodes, regions, and shaders, from mode into mod2
    dst_tag_data.markers = src_tag_data.markers
    dst_tag_data.nodes = src_tag_data.nodes
    dst_tag_data.regions = src_tag_data.regions
    dst_tag_data.shaders = src_tag_data.shaders

    # give the mod2 as many geometries as the mode
    src_tag_geoms = src_tag_data.geometries.STEPTREE
    dst_tag_geoms = dst_tag_data.geometries.STEPTREE
    dst_tag_geoms.extend(len(src_tag_geoms))

    # copy the data from the src_tag_geoms into the dst_tag_geoms
    for i in range(len(dst_tag_geoms)):
        # give the dst_tag_geom as many parts as the src_tag_geom
        src_tag_parts = src_tag_geoms[i].parts.STEPTREE
        dst_tag_parts = dst_tag_geoms[i].parts.STEPTREE
        dst_tag_parts.extend(len(src_tag_parts))

        # copy the data from the src_tag_parts into the dst_tag_parts
        for j in range(len(dst_tag_parts)):
            src_tag_part = src_tag_parts[j]
            dst_tag_part = dst_tag_parts[j]

            # move the first 9 part fields from src_tag into dst_tag
            # (except for the flags since usually ZONER shouldnt be copied)
            dst_tag_part[1: 9] = src_tag_part[1: 9]

            src_local_nodes = getattr(src_tag_part, "local_nodes", None)
            dst_local_nodes = getattr(dst_tag_part, "local_nodes", None)
            if not getattr(src_tag_part.flags, "ZONER", False):
                src_local_nodes = None

            if dst_local_nodes and src_local_nodes:
                # converting from a gbxmodel with local nodes to a gbxmodel
                # with local nodes. copy the local nodes and node count
                dst_tag_part.flags.ZONER = True
                dst_tag_part.local_node_count = src_tag_part.local_node_count
                dst_tag_part.local_nodes[:] = src_local_nodes[:]
            elif src_local_nodes:
                # converting from a gbxmodel with local nodes to
                # something without them. make the nodes absolute.
                src_tag.delocalize_part_nodes(i, j)

            # move the vertices and triangles from the src_tag into the dst_tag
            dst_tag_part.triangles = src_tag_part.triangles
            dst_tag_part.uncompressed_vertices = src_tag_part.uncompressed_vertices
            dst_tag_part.compressed_vertices   = src_tag_part.compressed_vertices

            uncomp_verts = dst_tag_part.uncompressed_vertices
            comp_verts   = dst_tag_part.compressed_vertices

            if to_gbxmodel:
                # if the compressed vertices are valid or
                # the uncompressed are not then we don't have
                # any conversion to do(already uncompressed)
                if not uncomp_verts.size or comp_verts.size:
                    dst_tag.decompress_part_verts(i, j)
            elif not comp_verts.size or uncomp_verts.size:
                # the uncompressed vertices are valid or
                # the compressed are not, so we don't have
                # any conversion to do(already compressed)
                dst_tag.compress_part_verts(i, j)


class ModelConvertor(Tk):
    to_gbxmodel = None

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Halo model convertor v2.0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self, curr_dir + 'tags' + PATHDIV)
        self.to_gbxmodel = IntVar(self, 1)

        # make the frame
        self.tags_dir_frame = LabelFrame(self, text="Tags directory")
        self.checkbox_frame = LabelFrame(self, text="Conversion settings")


        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.convert_btn = Button(
            self, text="Convert models", width=15, command=self.convert_models)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        self.to_gbxmodel_checkbutton = Checkbutton(
            self.checkbox_frame, variable=self.to_gbxmodel,
            text="Model  -->  Gbxmodel")
        self.to_model_checkbutton = Checkbutton(
            self.checkbox_frame, variable=self.to_gbxmodel,
            text="Gbxmodel  -->  Model", onvalue=0, offvalue=1)

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='x', side='left')

        self.to_gbxmodel_checkbutton.pack(anchor='w', padx=10, side='left')
        self.to_model_checkbutton.pack(anchor='w', padx=10, side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.checkbox_frame.pack(fill='both', anchor='nw')
        self.convert_btn.pack(fill='both', padx=5, pady=5)

        self.update()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry("%sx%s" % (w, h))
        self.minsize(width=w, height=h)

    def destroy(self):
        Tk.destroy(self)
        raise SystemExit(0)

    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def convert_models(self):
        print('Converting models\n')
        start = time()
        tags_dir = self.tags_dir.get()

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        to_gbxmodel = self.to_gbxmodel.get()
        if self.to_gbxmodel.get():
            src_ext = ".model"
            dst_ext = ".gbxmodel"
        else:
            src_ext = ".gbxmodel"
            dst_ext = ".model"

        for root, dirs, files in os.walk(tags_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.splitext(filename)[-1].lower() != src_ext:
                    continue
                #elif os.path.isfile(os.path.splitext(filepath)[0] + dst_ext):
                #    continue

                print('Converting %s' % filepath.split(tags_dir)[-1])
                if to_gbxmodel:
                    src_tag = mode_def.build(filepath=filepath)
                    dst_tag = mod2_def.build()
                else:
                    src_tag = mod2_def.build(filepath=filepath)
                    dst_tag = mode_def.build()

                dst_tag.filepath = os.path.splitext(filepath)[0] + dst_ext

                convert_model(src_tag, dst_tag, to_gbxmodel)
                dst_tag.calc_internal_data()
                dst_tag.serialize(temp=False, backup=False, int_test=False)

        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = ModelConvertor()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

