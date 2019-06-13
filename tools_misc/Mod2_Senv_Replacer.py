#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

import os
import supyr_struct

from math import sqrt
from struct import unpack, pack_into
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.defs.util import fcc
from supyr_struct.defs.constants import PATHDIV
from reclaimer.hek.defs.mod2 import fast_mod2_def as mod2_def
from reclaimer.hek.defs.senv import senv_def
from reclaimer.hek.defs.soso import soso_def


PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV


def replace_senv_in_mod2(mod2_tag, tags_dir, make_shaders=False, edit_gbxmodel=False):
    shaders = mod2_tag.data.tagdata.shaders.STEPTREE
    senv_shader_paths = set()
    for shader_ref in shaders:
        if (shader_ref.shader.tag_class.enum_name == "shader_environment"
            and shader_ref.shader.filepath):
            senv_shader_paths.add(shader_ref.shader.filepath.lower())

    make_shaders &= len(senv_shader_paths) != 0
    print("")
    print("%s senv in : %s" % (len(senv_shader_paths), mod2_tag.filepath))

    if not make_shaders:
        return senv_shader_paths

    print("    Creating soso shaders...")

    for shader_ref in shaders:
        if shader_ref.shader.tag_class.enum_name != "shader_environment":
            continue
        shader_fp = shader_ref.shader.filepath

        senv_tag = senv_def.build(
            filepath=os.path.join(
                tags_dir, shader_fp + ".shader_environment"))
        if senv_tag:
            # make a shader_model tag to replace the shader_environment tag with
            soso_tag = soso_def.build()
            soso_tag.filepath = os.path.join(
                tags_dir, shader_fp + "_soso.shader_model")

            # shorthand field alias's
            senv_attrs = senv_tag.data.tagdata.senv_attrs
            soso_attrs = soso_tag.data.tagdata.soso_attrs
            senv_flags = senv_attrs.environment_shader.flags
            soso_flags = soso_attrs.model_shader.flags

            senv_diffuse = senv_attrs.diffuse
            soso_maps = soso_attrs.maps

            senv_self_illum = senv_attrs.self_illumination
            soso_self_illum = soso_attrs.self_illumination

            senv_scrolling = senv_attrs.texture_scrolling
            soso_scrolling = soso_attrs.texture_scrolling

            senv_specular = senv_attrs.specular
            senv_reflection = senv_attrs.reflection
            soso_reflection = soso_attrs.reflection

            # copy shdr fields over
            soso_tag.data.tagdata.shdr_attrs = senv_tag.data.tagdata.shdr_attrs

            # copy similar flags
            soso_flags.not_alpha_tested = not senv_flags.alpha_tested
            soso_flags.true_atmospheric_fog = senv_flags.true_atmospheric_fog

            # copy diffuse and detail maps
            soso_maps.map_u_scale = soso_maps.map_v_scale = 1.0
            soso_maps.diffuse_map.filepath = senv_diffuse.base_map.filepath
            soso_maps.detail_function.data = senv_diffuse.detail_map_function.data
            soso_maps.detail_mask.set_to("red")

            if senv_diffuse.micro_detail_map.filepath:
                soso_maps.detail_map.filepath = senv_diffuse.micro_detail_map.filepath
                soso_maps.detail_map_scale = senv_diffuse.micro_detail_map_scale
            elif senv_diffuse.primary_detail_map.filepath:
                soso_maps.detail_map.filepath = senv_diffuse.primary_detail_map.filepath
                soso_maps.detail_map_scale = senv_diffuse.primary_detail_map_scale
            elif senv_diffuse.secondary_detail_map.filepath:
                soso_maps.detail_map.filepath = senv_diffuse.secondary_detail_map.filepath
                soso_maps.detail_map_scale = senv_diffuse.secondary_detail_map_scale

            # copy the self illumination
            soso_self_illum.flags.no_random_phase = True
            soso_self_illum.animation_function.data = senv_self_illum.primary_animation.function.data
            soso_self_illum.animation_period = senv_self_illum.primary_animation.period
            soso_self_illum.color_lower_bound[:] = senv_self_illum.primary_off_color[:]
            soso_self_illum.color_upper_bound[:] = senv_self_illum.primary_on_color[:]
            
            # copy the scrolling animation
            soso_scrolling.u_animation.function = senv_scrolling.u_animation.function
            soso_scrolling.u_animation.period = senv_scrolling.u_animation.period
            soso_scrolling.u_animation.scale = senv_scrolling.u_animation.scale
            
            soso_scrolling.v_animation.function = senv_scrolling.v_animation.function
            soso_scrolling.v_animation.period = senv_scrolling.v_animation.period
            soso_scrolling.v_animation.scale = senv_scrolling.v_animation.scale

            # copy the reflection and specular
            brightness = 1 + senv_specular.brightness
            soso_reflection.perpendicular_brightness = max(0, min(1, senv_reflection.perpendicular_brightness * brightness))
            soso_reflection.parallel_brightness = max(0, min(1, senv_reflection.parallel_brightness * brightness))
            soso_reflection.perpendicular_tint_color[:] = senv_specular.perpendicular_tint_color[:]
            soso_reflection.parallel_tint_color[:] = senv_specular.parallel_tint_color[:]
            soso_reflection.cube_map.filepath = senv_reflection.cube_map.filepath

            soso_tag.serialize(backup=False, temp=False, calc_pointers=False)

        shader_ref.shader.tag_class.set_to("shader_model")
        shader_ref.shader.filepath += "_soso"

    if not edit_gbxmodel:
        return senv_shader_paths

    print("    Editing gbxmodel...")

    for shader_ref in shaders:
        if shader_ref.shader.tag_class.enum_name == "shader_environment":
            shader_ref.shader.tag_class.set_to("shader_model")
            shader_ref.shader.filepath += "_soso"

    if not os.path.isfile(mod2_tag.filepath + '.ORIG'):
        os.rename(mod2_tag.filepath, mod2_tag.filepath + '.ORIG')

    mod2_tag.serialize(temp=False, backup=False, int_test=False,
                       calc_pointers=False)

    return senv_shader_paths


class Mod2SenvReplacer(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Gbxmodel environment replacer v1.0")
        self.resizable(0, 0)

        self.search_dir = StringVar(self)
        self.tags_dir = StringVar(self)
        self.restore_orig = IntVar(self)
        self.make_shaders = IntVar(self)
        self.edit_gbxmodel = IntVar(self)

        self.search_dir.set(curr_dir + 'tags' + PATHDIV)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)
        self.make_shaders.set(1)
        self.edit_gbxmodel.set(1)

        # make the frame
        self.search_dir_frame = LabelFrame(self, text="Search directory")
        self.tags_dir_frame = LabelFrame(self, text="Tags directory")
        self.checkbox_frame = LabelFrame(self, text="Conversion settings")

        # add the filepath boxes
        self.search_dir_entry = Entry(
            self.search_dir_frame, textvariable=self.search_dir)
        self.search_dir_entry.config(width=55, state=DISABLED)
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.convert_btn = Button(
            self, text="Convert shaders/gbxmodels", width=15, command=self.convert)
        self.search_dir_browse_btn = Button(
            self.search_dir_frame, text="Browse",
            width=6, command=self.search_dir_browse)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        self.restore_orig_checkbutton = Checkbutton(
            self.checkbox_frame, variable=self.restore_orig,
            text="Restore files with .ORIG extension(ignores settings below)")
        self.make_shaders_checkbutton = Checkbutton(
            self.checkbox_frame, variable=self.make_shaders,
            text="Make soso shaders from senv shaders")
        self.edit_gbxmodel_checkbutton = Checkbutton(
            self.checkbox_frame, variable=self.edit_gbxmodel,
            text=("Edit gbxmodels to point to the new soso shaders\n"
                  "(has no effect if not making soso shaders)"))

        # pack everything
        self.search_dir_entry.pack(expand=True, fill='x', side='left')
        self.search_dir_browse_btn.pack(fill='x', side='left')
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='x', side='left')
        
        self.restore_orig_checkbutton.pack(anchor='w', padx=10)
        self.make_shaders_checkbutton.pack(anchor='w', padx=10)
        self.edit_gbxmodel_checkbutton.pack(anchor='w', padx=10)

        self.search_dir_frame.pack(expand=True, fill='both')
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
        
    def search_dir_browse(self):
        dirpath = askdirectory(initialdir=self.search_dir.get())
        if dirpath:
            self.search_dir.set(dirpath)
        
    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def convert(self):
        print('Converting\n')
        start = time()
        search_dir = self.search_dir.get()
        tags_dir = self.tags_dir.get()

        found_shaders = set()
        restore_orig = self.restore_orig.get()
        make_shaders = self.make_shaders.get()
        edit_gbxmodel = self.edit_gbxmodel.get()

        if not search_dir.endswith(PATHDIV):
            search_dir += PATHDIV

        for root, dirs, files in os.walk(search_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if restore_orig:
                    if filepath.lower().endswith(".gbxmodel.orig"):
                        target_filepath = os.path.splitext(filepath)[0]
                        print("Restoring: %s" % filepath)
                        if os.path.isfile(target_filepath):
                            os.remove(target_filepath)
                        os.rename(filepath, target_filepath)
                    continue
                elif os.path.splitext(filename)[-1].lower() != '.gbxmodel':
                    continue
                elif os.path.isfile(filepath + '.ORIG'):
                    continue

                mod2_tag = mod2_def.build(filepath=filepath)
                if not mod2_tag:
                    return None

                print('.', end='')
                next_found_shaders = replace_senv_in_mod2(mod2_tag, tags_dir,
                                            make_shaders, edit_gbxmodel)
                if not next_found_shaders:
                    continue

                print('\n    Found senv in: %s' % filepath.split(tags_dir)[-1])
                found_shaders.update(next_found_shaders)

        print("\n\nThese shader_environment tags were found in gbxmodels:")
        for senv_shader in sorted(found_shaders):
            print("    %s" % senv_shader)

        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = Mod2SenvReplacer()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

