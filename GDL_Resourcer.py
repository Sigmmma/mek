import os
import tkinter.filedialog
import tkinter as tk

from tkinter import *
from traceback import format_exc
from copy import copy
from os.path import basename, dirname, splitext, exists, join

curr_dir = os.path.abspath(os.curdir)

try:
    from reclaimer.gdl.defs.objects import objects_ps2_def
    from reclaimer.gdl.g3d_compiler import G3dCompiler

    class GdlResourcer(Tk):

        objects_ps2_def = objects_ps2_def
        curr_dir = curr_dir
        
        def __init__(self, **options):
            Tk.__init__(self, **options )
            self.compiler = G3dCompiler()
            
            self.title("GDL Resourcer V1.0")
            self.geometry("280x78+0+0")
            self.resizable(0, 0)
            
            self.data_folderpath = StringVar(self)
            
            self.folder_field = Entry(self, textvariable=self.data_folderpath)
            self.folder_field.config(width=45, state=DISABLED)
            
            #Add the buttons
            self.btn_select = Button(self, text="Select resource folder",
                                   width=20, command=self.select_folder)
            self.btn_compile = Button(self, text="Compile objects",
                                   width=16, command=self.compile_objects)
            self.btn_decompile = Button(self, text="Decompile objects",
                                   width=16, command=self.decompile_objects)
            self.btn_compile_g3d = Button(self, text="Compile g3d models",
                                   width=20, command=self.compile_g3d_models)

            #place the widgets
            self.folder_field.place(x=5, y=4, anchor=NW)
            
            self.btn_select.place(x=9, y=25, anchor=NW)
            self.btn_compile_g3d.place(x=141, y=25, anchor=NW)
            
            self.btn_compile.place(x=33, y=50, anchor=NW)
            self.btn_decompile.place(x=141, y=50, anchor=NW)

            
        def select_folder(self):
            folderpath = filedialog.askdirectory(
                initialdir=self.curr_dir, title="Select resource folder...")
            folderpath = folderpath.replace('/','\\')
            if folderpath:
                self.data_folderpath.set(folderpath)
                self.curr_dir = folderpath
        
        def compile_objects(self):
            folderpath = self.data_folderpath.get()
            if folderpath:
                try:
                    print('----------Compiling---------')
                    objects_tag = self.objects_ps2_def.build(def_id='objects')
                    objects_tag.filepath = folderpath+'\\objects.ps2'
                    objects_tag.import_data()
                    objects_tag.serialize(temp=False)
                    print('----------Finished----------')
                except Exception:
                    print(format_exc())
                    print('Could not compile objects file.')
                    print('\n'+'-'*80+'\n')


        def compile_g3d_models(self):
            obj_filepaths = []
            c = self.compiler
            
            obj_folder = self.data_folderpath.get()+'\\data\\mod\\obj'
            g3d_path_base = dirname(obj_folder)+'\\%s.g3d'
            
            if not exists(obj_folder):
                return

            print('----------Compiling---------')
            '''collect all obj files in the directory'''
            for root, directories, files in os.walk(obj_folder):
                for filepath in files:            
                    if splitext(filepath)[-1].lower() == ".obj":
                        obj_filepaths.append(join(root, filepath))

            #loop over all objs, load them, convert them, and write the g3d
            for filepath in sorted(obj_filepaths):
                g3d_filepath = g3d_path_base % splitext(basename(filepath))[0]
                try:
                    print('\n' + g3d_filepath)
                    c.import_obj(filepath)

                    print('  vert_count:%s, tri_count:%s, bnd_rad:%s ' %
                          (len(c.verts),
                           sum([len(t) for t in c.all_tris.values()]),
                           c.bnd_rad))
                    
                    c.make_strips()
                    
                    for i in c.all_tris:
                        strips = c.stripifier.all_strips[i]
                        degens = c.stripifier.all_degens[i]
                        v_maxs = c.all_vert_maxs[i]
                        uv_maxs = c.all_uv_maxs[i]
                        print('\n  tex_index:%s, strip_count:%s' %
                              (i, len(strips)))
                        for j in range(len(strips)):
                            print(('    #:%s, degens:%s, v_max:%s, ' +
                                   'uv_max:%s, tri_count:%s') %
                                  (j, len(degens[j]), v_maxs[j],
                                   uv_maxs[j], len(strips[j])-2))
                    c.write_g3d(g3d_filepath)
                except Exception:
                    print(format_exc())
                    print('Could not compile model.')
                    print('\n'+'-'*80+'\n')
                print()
            print('----------Finished----------')
        

        def decompile_objects(self):
            folderpath = self.data_folderpath.get()
            if folderpath:
                try:
                    print('---------Decompiling--------')
                    objects_tag = self.objects_ps2_def.build(
                        filepath=folderpath+'\\OBJECTS.PS2')
                    objects_tag.extract_data(
                        defs=1, g3d=1, obj=1, tex=1, anim=1, mips=1,
                        individual=1, overwrite=0, alpha_pal=1)
                    print('----------Finished----------')
                except Exception:
                    print(format_exc())
                    print('Could not extract data.')
                    print('\n'+'-'*80+'\n')


    if __name__ == '__main__':
        compiler = GdlResourcer()
        compiler.mainloop()

except Exception:
    print(format_exc())
    input()
