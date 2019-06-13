#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

import os
import supyr_struct

from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.defs.constants import PATHDIV
from reclaimer.hek.defs.sbsp import fast_sbsp_def as sbsp_def


PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV


def replace_sotr_in_sbsp(sbsp_tag, tags_dir, edit_sbsp=False):
    sotr_shader_paths = set()
    shader_blocks = []

    for shader_ref in sbsp_tag.data.tagdata.collision_materials.STEPTREE:
        shader_blocks.append(shader_ref.shader)

    for lightmap in sbsp_tag.data.tagdata.lightmaps.STEPTREE:
        for material in lightmap.materials.STEPTREE:
            shader_blocks.append(material.shader)

    for shader in shader_blocks:
        if (shader.tag_class.enum_name == "shader_transparent_generic" and shader.filepath):
            sotr_shader_paths.add(shader.filepath.lower())

    print("    %s sotr in : %s" % (len(sotr_shader_paths), sbsp_tag.filepath))
    if not edit_sbsp:
        return sotr_shader_paths

    save_bsp = False
    for shader in shader_blocks:
        shader_path = os.path.join(tags_dir, shader.filepath)
        if shader.tag_class.enum_name == "shader_transparent_generic":
            if os.path.isfile(shader_path + '.shader_transparent_chicago_extended'):
                shader.tag_class.set_to("shader_transparent_chicago_extended")
                save_bsp = True
            elif os.path.isfile(shader_path + '.shader_transparent_chicago'):
                shader.tag_class.set_to("shader_transparent_chicago")
                save_bsp = True
            else:
                print("    No scex/schi exists for: %s" % shader.filepath)
        elif (shader.tag_class.enum_name == "shader_transparent_chicago" and
              not os.path.isfile(shader_path + '.shader_transparent_chicago') and
              os.path.isfile(shader_path + '.shader_transparent_chicago_extended')):
            shader.tag_class.set_to("shader_transparent_chicago_extended")
            save_bsp = True

    if not save_bsp:
        return sotr_shader_paths

    print("        Editing sbsp...")

    if not os.path.isfile(sbsp_tag.filepath + '.ORIG'):
        os.rename(sbsp_tag.filepath, sbsp_tag.filepath + '.ORIG')

    sbsp_tag.serialize(temp=False, backup=False,
                       int_test=False, calc_pointers=False)

    return sotr_shader_paths


class SbspSotrReplacer(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Sbsp transparent_generic replacer v1.0")
        self.resizable(0, 0)

        self.search_dir = StringVar(self)
        self.tags_dir = StringVar(self)
        self.restore_orig = IntVar(self)
        self.edit_sbsp = IntVar(self)

        self.search_dir.set(curr_dir + 'tags' + PATHDIV)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)
        self.edit_sbsp.set(1)

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
            self, text="Replace references", width=15, command=self.convert)
        self.search_dir_browse_btn = Button(
            self.search_dir_frame, text="Browse",
            width=6, command=self.search_dir_browse)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        self.restore_orig_checkbutton = Checkbutton(
            self.checkbox_frame, variable=self.restore_orig,
            text="Restore files with .ORIG extension(ignores settings below)")
        self.edit_sbsp_checkbutton = Checkbutton(
            self.checkbox_frame, variable=self.edit_sbsp,
            text="Edit sbsp tags to point to the equivalent scex/schi shaders")

        # pack everything
        self.search_dir_entry.pack(expand=True, fill='x', side='left')
        self.search_dir_browse_btn.pack(fill='x', side='left')
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='x', side='left')
        
        self.restore_orig_checkbutton.pack(anchor='w', padx=10)
        self.edit_sbsp_checkbutton.pack(anchor='w', padx=10)

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
        edit_sbsp = self.edit_sbsp.get()

        if not search_dir.endswith(PATHDIV):
            search_dir += PATHDIV

        for root, dirs, files in os.walk(search_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if restore_orig:
                    if filepath.lower().endswith(".scenario_structure_bsp.orig"):
                        target_filepath = os.path.splitext(filepath)[0]
                        print("Restoring: %s" % filepath)
                        if os.path.isfile(target_filepath):
                            os.remove(target_filepath)
                        os.rename(filepath, target_filepath)
                    continue
                elif os.path.splitext(filename)[-1].lower() != '.scenario_structure_bsp':
                    continue
                elif os.path.isfile(filepath + '.ORIG'):
                    continue

                sbsp_tag = sbsp_def.build(filepath=filepath)
                if not sbsp_tag:
                    return None

                next_found_shaders = replace_sotr_in_sbsp(sbsp_tag, tags_dir, edit_sbsp)
                if not next_found_shaders:
                    continue

                found_shaders.update(next_found_shaders)

        print("\n\nThese shader_transparent_generic tags were found in scenario_structure_bsp:")
        for sotr_shader in sorted(found_shaders):
            print("    %s" % sotr_shader)

        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = SbspSotrReplacer()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()

