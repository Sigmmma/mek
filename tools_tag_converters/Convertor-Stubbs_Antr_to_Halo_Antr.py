#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

import os
import struct

from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.defs.constants import PATHDIV
from supyr_struct.defs.block_def import BlockDef
from reclaimer.hek.defs.antr    import antr_def
from reclaimer.stubbs.defs.antr import antr_def as stubbs_antr_def
from reclaimer.common_descs import tag_header_os


tag_header_def = BlockDef(tag_header_os)

PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV


def convert_antr_tag(antr_path):
    # make a new tag and load the stubbs one
    antr_tag = antr_def.build()
    tagdata  = antr_tag.data.tagdata
    stubbs_antr_tag = stubbs_antr_def.build(filepath=antr_path)
    stubbs_tagdata  = stubbs_antr_tag.data.tagdata

    # animation descriptor
    tagdata.animations.STEPTREE.append()
    animation = tagdata.animations.STEPTREE[-1]

    animation_desc   = animation.desc

    # copy all reflexives except the units, vehicles, and damages
    tagdata.objects    = stubbs_tagdata.objects
    tagdata.weapons    = stubbs_tagdata.weapons
    tagdata.devices    = stubbs_tagdata.devices
    tagdata.fp_animations         = stubbs_tagdata.fp_animations
    tagdata.sound_references      = stubbs_tagdata.effect_references
    tagdata.limp_body_node_radius = stubbs_tagdata.limp_body_node_radius
    tagdata.flags      = stubbs_tagdata.flags
    tagdata.nodes      = stubbs_tagdata.nodes
    tagdata.animations = stubbs_tagdata.animations

    # copy everything in the unit block except the stubbs stuff
    units        = tagdata.units.STEPTREE
    stubbs_units = stubbs_tagdata.units.STEPTREE
    units.extend(len(stubbs_units))
    for i in range(len(units)):
        unit = units[i]
        stubbs_unit = stubbs_units[i]
        for j in range(11):
            unit[j] = stubbs_unit[j]

        unit_weapons         = unit.weapons.STEPTREE
        stubbs_unit_weapons  = stubbs_unit.weapons.STEPTREE
        unit_weapons.extend(len(stubbs_unit_weapons))
        for j in range(len(unit_weapons)):
            unit_weapon = unit_weapons[j]
            stubbs_unit_weapon = stubbs_unit_weapons[j]

            for k in range(11):
                unit_weapon[k] = stubbs_unit_weapon[k]

            unit_weapon[12] = stubbs_unit_weapon[12]
            unit_weapon[13] = stubbs_unit_weapon[13]

    # copy everything in the vehicle block except the stubbs stuff
    vehicles        = tagdata.vehicles.STEPTREE
    stubbs_vehicles = stubbs_tagdata.vehicles.STEPTREE
    vehicles.extend(len(stubbs_vehicles))
    for i in range(len(vehicles)):
        vehicle = vehicles[i]
        stubbs_vehicle = stubbs_vehicles[i]
        for j in range(8):
            vehicle[j] = stubbs_vehicle[j]

        vehicle[8] = stubbs_vehicle[9]
        vehicle[9] = stubbs_vehicle[10]


    #swap the animation descriptors
    for animation in tagdata.animations.STEPTREE:
        animation.desc = animation_desc


    # replace the filepath
    antr_tag.filepath = stubbs_antr_tag.filepath
    return antr_tag


class StubbsAntrConverter(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Stubbs antr tag converter v1.0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)

        # make the frames
        self.tags_dir_frame = LabelFrame(
            self, text="Directory of model_animation tags")

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

    def convert(self):
        print('Converting model_animations\n')
        start = time()
        tags_dir = self.tags_dir.get()

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        for root, dirs, files in os.walk(tags_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if not os.path.splitext(filename)[-1].lower() == '.model_animations':
                    continue

                try:
                    blam_header = tag_header_def.build(filepath=filepath)
                    if blam_header.version != 5:
                        continue

                    print(filepath.split(tags_dir)[-1])

                    tag = convert_antr_tag(filepath)
                    if tag is None:
                        continue
                except Exception:
                    print(format_exc())
                    print("Could not convert:   %s" % filepath)
                    continue

                tag.serialize(temp=False, backup=False, int_test=False)
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = StubbsAntrConverter()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

