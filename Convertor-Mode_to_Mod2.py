import os, supyr_struct

from math import sqrt
from struct import pack_into
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.field_types import FieldType, BytearrayRaw
from supyr_struct.defs.constants import fcc, PATHDIV
from supyr_struct.defs.block_def import BlockDef
from reclaimer.hek.defs.mod2 import mod2_def
from reclaimer.stubbs.defs.mode import mode_def

def undef_size(node, *a, **kwa):
    if node is None:
        return 0
    return len(node)

raw_block_def = BlockDef("raw_block",
    BytearrayRaw('data', SIZE=undef_size)
    )

PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV


def mode_to_mod2(mode_path):
    mode_tag = mode_def.build(filepath=mode_path)
    mod2_tag = mod2_def.build()
    mod2_tag.filepath = os.path.splitext(mode_path)[0] + '.gbxmodel'

    mode_data = mode_tag.data.tagdata
    mod2_data = mod2_tag.data.tagdata

    # move the first 14 header fields from mode into mod2
    for i in range(14):
        mod2_data[i] = mode_data[i]
    # fix the fact the mode and mod2 store stuff related to lods in reverse
    mod2_data.superhigh_lod_cutoff = mode_data.superhigh_lod_cutoff
    mod2_data.high_lod_cutoff = mode_data.high_lod_cutoff
    mod2_data.low_lod_cutoff = mode_data.low_lod_cutoff
    mod2_data.superlow_lod_cutoff = mode_data.superlow_lod_cutoff

    mod2_data.superhigh_lod_nodes = mode_data.superhigh_lod_nodes
    mod2_data.high_lod_nodes = mode_data.high_lod_nodes
    mod2_data.low_lod_nodes = mode_data.low_lod_nodes
    mod2_data.superlow_lod_nodes = mode_data.superlow_lod_nodes

    # move the markers, nodes, regions, and shaders, from mode into mod2
    mod2_data.markers = mode_data.markers
    mod2_data.nodes = mode_data.nodes
    mod2_data.regions = mode_data.regions
    mod2_data.shaders = mode_data.shaders

    # give the mod2 as many geometries as the mode
    mode_geoms = mode_data.geometries.STEPTREE
    mod2_geoms = mod2_data.geometries.STEPTREE
    mod2_geoms.extend(len(mode_geoms))

    # copy the data from the mode_geoms into the mod2_geoms
    for i in range(len(mod2_geoms)):

        # give the mod2_geom as many parts as the mode_geom
        mode_parts = mode_geoms[i].parts.STEPTREE
        mod2_parts = mod2_geoms[i].parts.STEPTREE
        mod2_parts.extend(len(mode_parts))

        # copy the data from the mode_parts into the mod2_parts
        for j in range(len(mod2_parts)):
            mode_part = mode_parts[j]
            mod2_part = mod2_parts[j]

            # move the first 9 part fields from mode into mod2
            for k in range(9):
                mod2_part[k] = mode_part[k]

            # move the triangles from the mode into the mod2
            mod2_part.triangles = mode_part.triangles

            mode_comp_verts = mode_part.compressed_vertices
            mod2_uncomp_verts = mod2_part.uncompressed_vertices

            uncomp_buffer = bytearray(b'\x00'*68*mode_comp_verts.size)
            mod2_uncomp_verts.STEPTREE = raw_block_def.build()
            mod2_uncomp_verts.STEPTREE.data = uncomp_buffer

            offset = 0
            # uncompress each of the verts and write them to the buffer
            for vert in mode_comp_verts.STEPTREE:
                norm = vert[3]
                binorm = vert[4]
                tangent = vert[5]
                ni = norm&2047
                nj = (norm>>11)&2047
                nk = (norm>>22)&1023
                bi = binorm&2047
                bj = (binorm>>11)&2047
                bk = (binorm>>22)&1023
                ti = tangent&2047
                tj = (tangent>>11)&2047
                tk = (tangent>>22)&1023
                if ni&1024: ni = -1*((~ni) & 2047)
                if nj&1024: nj = -1*((~nj) & 2047)
                if nk&512:  nk = -1*((~nk) & 1023)
                if bi&1024: bi = -1*((~bi) & 2047)
                if bj&1024: bj = -1*((~bj) & 2047)
                if bk&512:  bk = -1*((~bk) & 1023)
                if ti&1024: ti = -1*((~ti) & 2047)
                if tj&1024: tj = -1*((~tj) & 2047)
                if tk&512:  tk = -1*((~tk) & 1023)
                ni /= 1023
                nj /= 1023
                nk /= 511
                bi /= 1023
                bj /= 1023
                bk /= 511
                ti /= 1023
                tj /= 1023
                tk /= 511

                nmag = max(sqrt(ni**2 + nj**2 + nk**2), 0.00000001)
                bmag = max(sqrt(bi**2 + bj**2 + bk**2), 0.00000001)
                tmag = max(sqrt(ti**2 + tj**2 + tk**2), 0.00000001)

                # write the uncompressed data
                pack_into('>ffffffffffffffhhff', uncomp_buffer, offset,
                          vert[0], vert[1], vert[2],
                          ni/nmag, nj/nmag, nk/nmag,
                          bi/bmag, bj/bmag, bk/bmag,
                          ti/tmag, tj/tmag, tk/tmag,
                          vert[6]/32767, vert[7]/32767,
                          vert[8]//3, vert[9]//3,
                          vert[10]/32767, 1.0 - vert[10]/32767)
                offset += 68

            # give the mod2_part as many uncompressed_vertices
            # as the mode_part has compressed_vertices
            mod2_uncomp_verts.size = mode_comp_verts.size

    return mod2_tag


class ModeToMod2Convertor(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Model to Gbxmodel Convertor v1.0")
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
        self.convert_btn = Button(
            self, text="Convert models", width=15, command=self.convert_models)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='both', side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.convert_btn.pack(fill='both', padx=5, pady=5)
        
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

        for root, dirs, files in os.walk(tags_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if os.path.splitext(filename)[-1].lower() != '.model':
                    continue

                print('Converting %s' % filepath.split(tags_dir)[-1])

                mod2_tag = mode_to_mod2(filepath)
                mod2_tag.serialize(temp=False, backup=False)
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = ModeToMod2Convertor()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

