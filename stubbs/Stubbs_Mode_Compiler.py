import os, struct, supyr_struct

from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from supyr_struct.field_types import FieldType, BytearrayRaw
from supyr_struct.defs.constants import fcc, PATHDIV
from supyr_struct.defs.block_def import BlockDef
from reclaimer.stubbs.defs.mode import mode_def

force_little = FieldType.force_little
force_normal = FieldType.force_normal

raw_block_def = BlockDef("raw_block",
    BytearrayRaw('data',
        SIZE=lambda node, *a, **kw: 0 if node is None else len(node))
    )

PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV


def make_mode_tag(meta_path, tags_dir=curr_dir + "tags" + PATHDIV):
    mode_tag = mode_def.build()
    try:
        # force reading in little endian since meta data is ALL little endian
        force_little()

        # make a new tag
        tagdata = mode_tag.data.tagdata

        # populate that new tag with the meta data
        tagdata.parse(filepath=meta_path)

        # get the verts, tris, and dependencies to put in the new tag
        verts, tris = get_verts_and_tris(
            os.path.splitext(meta_path)[0] + PATHDIV)
        tag_paths = get_tag_paths(meta_path + '.data')

        # replace the filepath
        mode_tag.filepath = tags_dir + tag_paths[0] + ".model"

        geoms = tagdata.geometries.STEPTREE
        shaders = tagdata.shaders.STEPTREE

        # insert the vertices and triangles
        for i in range(len(geoms)):
            geom = geoms[i].parts.STEPTREE
            for j in range(len(geom)):
                part = geom[j]
                key = "%s-%s" % (i, j)
                if key in verts:
                    raw_data = verts[key]
                    raw_block = raw_block_def.build()
                    raw_block.data = new_raw = bytearray(32*(len(raw_data)//32))

                    # byteswap each of the floats, ints, and shorts
                    for ii in range(0, len(new_raw), 32):
                        # byteswap the position floats and lighting vectors
                        for jj in (0,4,8,12,16,20):
                            jj += ii
                            new_raw[jj] = raw_data[jj+3]
                            new_raw[jj+1] = raw_data[jj+2]
                            new_raw[jj+2] = raw_data[jj+1]
                            new_raw[jj+3] = raw_data[jj]
                        # byteswap the texture coordinates
                        new_raw[ii+24] = raw_data[ii+25]
                        new_raw[ii+25] = raw_data[ii+24]
                        new_raw[ii+26] = raw_data[ii+27]
                        new_raw[ii+27] = raw_data[ii+26]
                        # copy over the node indices
                        new_raw[ii+28] = raw_data[ii+28]
                        new_raw[ii+29] = raw_data[ii+29]
                        # byteswap the node weight
                        new_raw[ii+30] = raw_data[ii+31]
                        new_raw[ii+31] = raw_data[ii+30]

                    part.compressed_vertices.size = len(raw_data)//32
                    part.compressed_vertices.STEPTREE = raw_block
                else:
                    print("Could not locate vertices for '%s' in %s" %
                          (key, mode_tag.filepath))

                if key in tris:
                    raw_data = tris[key]
                    raw_block = raw_block_def.build()
                    raw_block.data = new_raw = bytearray(6*(len(raw_data)//6))

                    # byteswap each of the shorts
                    for ii in range(0, len(new_raw), 2):
                        new_raw[ii] = raw_data[ii+1]
                        new_raw[ii+1] = raw_data[ii]

                    part.triangles.size = len(raw_data)//6
                    part.triangles.STEPTREE = raw_block
                else:
                    print("Could not locate triangles for '%s' in %s" %
                          (key, mode_tag.filepath))

        # insert the shader dependency strings
        for i in range(len(shaders)):
            shader = shaders[i]
            tag_path, tag_class = tag_paths[i+1]
            shader.shader.filepath = tag_path
            shader.shader.tag_class.data = tag_class

        # force fix the endianness
        force_normal()
    except Exception:
        force_normal()
        raise

    return mode_tag


def get_verts_and_tris(data_dir):
    # These are the raw bytes of the vertices and triangles. The keys are
    # "geom-part" where geom is the geometry index and part is the part index
    vertices = {}
    triangles = {}

    try:
        for root, dirs, files in os.walk(data_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                info = filename.lower().split('[')
                if len(info) != 2 or info[0] not in ("index", "verts"):
                    continue

                key = info[1].split(']')[0]

                with open(root + filename, 'rb') as f:
                    data = f.read()

                if info[0] == 'index':
                    if len(data)%6 == 4:
                        data += b'\xff\xff'
                    triangles[key] = data
                else:
                    vertices[key] = data
    except Exception:
        print(format_exc())

    return vertices, triangles


def get_tag_paths(data_path):
    # The first entry will always exist, and will be the
    # tagpath of the tag whose meta is being parsed, while
    # any others will be the dependencies of the tag
    tag_paths = ['']
    try:
        with open(data_path, 'r') as f:
            for line in f:
                if line.lower().startswith('filename'):
                    tag_paths[0] = line.split('|')[-1].split('\n')[0]
                elif line.lower().startswith('dependency'):
                    tag_path, tag_class = line.split('\n')[0].split('|')[2:]
                    tag_class = fcc(tag_class[:4], 'big')
                    tag_paths.append((tag_path, tag_class))
    except Exception:
        print(format_exc())
    return tag_paths


class StubbsModeCompiler(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Stubbs mode tag compiler v1.0")
        self.geometry("400x120+0+0")
        self.resizable(0, 0)

        self.meta_dir = StringVar(self)
        self.tags_dir = StringVar(self)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)

        # make the frames
        self.meta_dir_frame = LabelFrame(self, text="Directory of metadata")
        self.tags_dir_frame = LabelFrame(self, text="Output tags directory")
        
        # add the filepath boxes
        self.meta_dir_entry = Entry(
            self.meta_dir_frame, textvariable=self.meta_dir)
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.meta_dir_entry.config(width=55, state=DISABLED)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.compile_btn = Button(
            self, text="Compile", width=15, command=self.compile_models)
        self.meta_dir_browse_btn = Button(
            self.meta_dir_frame, text="Browse",
            width=6, command=self.meta_dir_browse)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        # pack everything
        self.meta_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.meta_dir_browse_btn.pack(fill='both', side='left')
        self.tags_dir_browse_btn.pack(fill='both', side='left')

        self.meta_dir_frame.pack(expand=True, fill='both')
        self.tags_dir_frame.pack(expand=True, fill='both')
        self.compile_btn.pack(fill='both', padx=5, pady=5)

    def destroy(self):
        Tk.destroy(self)
        #raise SystemExit(0)
        os._exit(0)

    def meta_dir_browse(self):
        dirpath = askdirectory(initialdir=self.meta_dir.get())
        if dirpath:
            self.meta_dir.set(dirpath)
        
    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def compile_models(self):
        print('Compiling models\n')
        start = time()
        meta_dir = self.meta_dir.get()
        tags_dir = self.tags_dir.get()

        if not meta_dir.endswith(PATHDIV):
            meta_dir += PATHDIV

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        for root, dirs, files in os.walk(meta_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if not filename.lower().endswith('[mode].meta'):
                    continue

                print('Compiling %s' % filepath.split(meta_dir)[-1])

                tag = make_mode_tag(filepath, tags_dir)
                tag.serialize(temp=False, backup=False)
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    compiler = StubbsModeCompiler()
    compiler.mainloop()
except Exception:
    print(format_exc())
    input()

