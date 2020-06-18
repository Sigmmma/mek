#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

import os
import struct

from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.defs.block_def import BlockDef
from reclaimer.hek.defs.antr    import antr_def
from reclaimer.stubbs.defs.antr import antr_def as stubbs_antr_def
from reclaimer.common_descs import tag_header_os


__version__ = (1, 1, 0)


tag_header_def = BlockDef(tag_header_os)

curr_dir = os.path.abspath(os.curdir)


def convert_antr_tag(antr_path):
    # make a new tag and load the stubbs one
    antr_tag = antr_def.build()
    tagdata  = antr_tag.data.tagdata
    stubbs_antr_tag = stubbs_antr_def.build(filepath=antr_path)
    stubbs_tagdata  = stubbs_antr_tag.data.tagdata

    # copy all reflexives except the units, vehicles, and damages
    tagdata.objects    = stubbs_tagdata.objects
    tagdata.weapons    = stubbs_tagdata.weapons
    tagdata.devices    = stubbs_tagdata.devices
    tagdata.fp_animations         = stubbs_tagdata.fp_animations
    tagdata.limp_body_node_radius = stubbs_tagdata.limp_body_node_radius
    tagdata.flags      = stubbs_tagdata.flags
    tagdata.nodes      = stubbs_tagdata.nodes

    sound_refs  = tagdata.sound_references.STEPTREE
    effect_refs = stubbs_tagdata.effect_references.STEPTREE
    sound_refs.extend(len(effect_refs))
    for i in range(len(sound_refs)):
        sound_ref  = sound_refs[i].sound
        effect_ref = effect_refs[i].effect
        if effect_ref.tag_class.enum_name == "sound":
            sound_ref.tag_class.set_to("sound")
            sound_ref.filepath = effect_ref.filepath

    # copy everything in the unit block except the stubbs stuff
    units        = tagdata.units.STEPTREE
    stubbs_units = stubbs_tagdata.units.STEPTREE
    units.extend(len(stubbs_units))
    for i in range(len(units)):
        unit = units[i]
        stubbs_unit = stubbs_units[i]

        # copy label, yaw, and pitch values
        unit.label                = stubbs_unit.label
        unit.right_yaw_per_frame  = stubbs_unit.right_yaw_per_frame
        unit.left_yaw_per_frame   = stubbs_unit.left_yaw_per_frame
        unit.right_frame_count    = stubbs_unit.right_frame_count
        unit.left_frame_count     = stubbs_unit.left_frame_count
        unit.down_pitch_per_frame = stubbs_unit.down_pitch_per_frame
        unit.up_pitch_per_frame   = stubbs_unit.up_pitch_per_frame
        unit.down_frame_count     = stubbs_unit.down_frame_count
        unit.up_frame_count       = stubbs_unit.up_frame_count

        # copy reflexives
        unit.animations = stubbs_unit.animations
        unit.ik_points  = stubbs_unit.ik_points


        unit_weapons         = unit.weapons.STEPTREE
        stubbs_unit_weapons  = stubbs_unit.weapons.STEPTREE
        unit_weapons.extend(len(stubbs_unit_weapons))
        for j in range(len(unit_weapons)):
            unit_weapon = unit_weapons[j]
            stubbs_unit_weapon = stubbs_unit_weapons[j]

            # copy name, yaw, and pitch values
            unit_weapon.name                 = stubbs_unit_weapon.name
            unit_weapon.grip_marker          = stubbs_unit_weapon.grip_marker
            unit_weapon.hand_marker          = stubbs_unit_weapon.hand_marker
            unit_weapon.right_yaw_per_frame  = stubbs_unit_weapon.right_yaw_per_frame
            unit_weapon.left_yaw_per_frame   = stubbs_unit_weapon.left_yaw_per_frame
            unit_weapon.right_frame_count    = stubbs_unit_weapon.right_frame_count
            unit_weapon.left_frame_count     = stubbs_unit_weapon.left_frame_count
            unit_weapon.down_pitch_per_frame = stubbs_unit_weapon.down_pitch_per_frame
            unit_weapon.up_pitch_per_frame   = stubbs_unit_weapon.up_pitch_per_frame
            unit_weapon.down_frame_count     = stubbs_unit_weapon.down_frame_count
            unit_weapon.up_frame_count       = stubbs_unit_weapon.up_frame_count

            # copy reflexives
            unit_weapon.ik_points    = stubbs_unit_weapon.ik_points
            unit_weapon.weapon_types = stubbs_unit_weapon.weapon_types


    # copy everything in the vehicle block except the stubbs stuff
    vehicles        = tagdata.vehicles.STEPTREE
    stubbs_vehicles = stubbs_tagdata.vehicles.STEPTREE
    vehicles.extend(len(stubbs_vehicles))
    for i in range(len(vehicles)):
        vehicle = vehicles[i]
        stubbs_vehicle = stubbs_vehicles[i]

        # copy yaw and pitch values
        vehicle.right_yaw_per_frame  = stubbs_vehicle.right_yaw_per_frame
        vehicle.left_yaw_per_frame   = stubbs_vehicle.left_yaw_per_frame
        vehicle.right_frame_count    = stubbs_vehicle.right_frame_count
        vehicle.left_frame_count     = stubbs_vehicle.left_frame_count
        vehicle.down_pitch_per_frame = stubbs_vehicle.down_pitch_per_frame
        vehicle.up_pitch_per_frame   = stubbs_vehicle.up_pitch_per_frame
        vehicle.down_frame_count     = stubbs_vehicle.down_frame_count
        vehicle.up_frame_count       = stubbs_vehicle.up_frame_count

        # copy reflexives
        vehicle.animations            = stubbs_vehicle.animations
        vehicle.suspension_animations = stubbs_vehicle.suspension_animations


    # copy the animations
    animations = tagdata.animations.STEPTREE
    stubbs_animations = stubbs_tagdata.animations.STEPTREE
    animations.extend(len(stubbs_animations))
    for i in range(len(animations)):
        anim = animations[i]
        stubbs_anim = stubbs_animations[i]

        anim.name = stubbs_anim.name
        anim.type = stubbs_anim.type
        anim.frame_count = stubbs_anim.frame_count
        anim.frame_size = stubbs_anim.frame_size
        anim.frame_info_type = stubbs_anim.frame_info_type
        anim.node_list_checksum = stubbs_anim.node_list_checksum
        anim.node_count = stubbs_anim.node_count
        anim.loop_frame_index = stubbs_anim.loop_frame_index

        anim.weight = stubbs_anim.weight
        anim.key_frame_index = stubbs_anim.key_frame_index
        anim.second_key_frame_index = stubbs_anim.second_key_frame_index

        anim.next_animation = stubbs_anim.next_animation
        anim.flags = stubbs_anim.flags
        anim.sound = stubbs_anim.sound

        anim.sound_frame_index = stubbs_anim.sound_frame_index
        anim.left_foot_frame_index = stubbs_anim.left_foot_frame_index
        anim.right_foot_frame_index = stubbs_anim.right_foot_frame_index
        anim.first_permutation_index = stubbs_anim.first_permutation_index

        anim.chance_to_play = stubbs_anim.chance_to_play

        anim.frame_info = stubbs_anim.frame_info
        anim.trans_flags0 = stubbs_anim.trans_flags0
        anim.trans_flags1 = stubbs_anim.trans_flags1
        anim.rot_flags0 = stubbs_anim.rot_flags0
        anim.rot_flags1 = stubbs_anim.rot_flags1
        anim.scale_flags0 = stubbs_anim.scale_flags0
        anim.scale_flags1 = stubbs_anim.scale_flags1
        anim.offset_to_compressed_data = stubbs_anim.offset_to_compressed_data
        anim.default_data = stubbs_anim.default_data
        anim.frame_data = stubbs_anim.frame_data


    # replace the filepath
    antr_tag.filepath = stubbs_antr_tag.filepath
    return antr_tag


class StubbsAntrConverter(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Stubbs antr tag converter v%s.%s.%s" % __version__)
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.tags_dir.set(os.path.join(curr_dir, 'tags'))

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

        for root, dirs, files in os.walk(tags_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
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

