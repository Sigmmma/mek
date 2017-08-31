#!/usr/bin/env python3

import os, struct

from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.defs.constants import fcc, PATHDIV, FieldParseError
from supyr_struct.defs.block_def import BlockDef
from reclaimer.os_v3_hek.defs.coll import fast_coll_def as coll_def
from reclaimer.stubbs.defs.coll    import fast_coll_def as stubbs_coll_def
from reclaimer.common_descs import tag_header_os


tag_header_def = BlockDef(tag_header_os)

PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV

# maps stubbs material numbers 0-34 to halo names to change them to
material_map = (
    "dirt",
    "sand",
    "stone",
    "snow",
    "wood",
    "metal_hollow",
    "metal_thin",
    "metal_thick",
    "rubber",
    "glass",
    "force_field",
    "grunt",
    "hunter_armor",
    "hunter_skin",
    "elite",
    "jackal",
    "jackal_energy_shield",
    "engineer_skin",
    "engineer_force_field",
    "flood_combat_form",
    "flood_carrier_form",
    "cyborg_armor",
    "cyborg_energy_shield",
    "human_armor",
    "human_skin",
    "sentinel",
    "moniter",
    "plastic",
    "water",
    "leaves",
    "elite_energy_shield",
    "ice",
    "hunter_shield",
    "dirt",
    "dirt",
    )


def convert_coll_tag(coll_path):
    # make a new tag and load the stubbs one
    coll_tag = coll_def.build()
    tagdata  = coll_tag.data.tagdata
    stubbs_coll_tag = stubbs_coll_def.build(filepath=coll_path)
    stubbs_tagdata  = stubbs_coll_tag.data.tagdata

    # move blocks from stubbs tag into the halo one
    for i in (0, 1, 2, 3, 6, 7, 8):
        tagdata[i] = stubbs_tagdata[i]

    # make materials to replace the stubbs ones
    materials = tagdata.materials.STEPTREE
    stubbs_materials = stubbs_tagdata.materials.STEPTREE
    materials.extend(len(stubbs_materials))
    for i in range(stubbs_tagdata.materials.size):
        material = materials[i]
        stubbs_material = stubbs_materials[i]
        for name in material.NAME_MAP:
            stubbs_block = stubbs_material[name]

            # change the material type using a mapping
            if name == 'material_type':
                material.material_type.set_to(material_map[stubbs_block.data])
                continue
            material[name] = stubbs_block

    # make regions to replace the stubbs ones
    regions = tagdata.regions.STEPTREE
    stubbs_regions = stubbs_tagdata.regions.STEPTREE
    regions.extend(len(stubbs_regions))
    for i in range(stubbs_tagdata.regions.size):
        region = regions[i]
        stubbs_region = stubbs_regions[i]
        for name in region.NAME_MAP:
            if 'permutation' in name:
                continue
            region[name] = stubbs_region[name]

        # make permutations to replace the stubbs ones
        permutations = region.permutations.STEPTREE
        stubbs_permutations = stubbs_region.permutations.STEPTREE
        permutations.extend(len(stubbs_permutations))
        for i in range(stubbs_region.permutations.size):
            permutations[i].name = stubbs_permutations[i].name

    # replace the filepath
    coll_tag.filepath = stubbs_coll_tag.filepath

    return coll_tag


class StubbsCollConverter(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Stubbs coll tag converter v1.0")
        self.geometry("400x80+0+0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)

        # make the frames
        self.tags_dir_frame = LabelFrame(
            self, text="Directory of model_collision_geometry tags")

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
        #raise SystemExit(0)
        os._exit(0)
        
    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def convert(self):
        print('Converting model_collision_geometrys\n')
        start = time()
        tags_dir = self.tags_dir.get()

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        for root, dirs, files in os.walk(tags_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if not os.path.splitext(filename)[-1].lower() == '.model_collision_geometry':
                    continue

                try:
                    blam_header = tag_header_def.build(filepath=filepath)
                    if blam_header.version != 11:
                        continue

                    print(filepath.split(tags_dir)[-1])

                    tag = convert_coll_tag(filepath)
                    if tag is None:
                        continue
                except Exception:
                    print(format_exc())
                    print("Could not convert:   %s" % filepath)
                    continue

                tag.serialize(temp=False, backup=False, int_test=False)
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = StubbsCollConverter()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

