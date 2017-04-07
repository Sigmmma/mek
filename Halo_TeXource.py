import os, zlib

from time import time
from tkinter import *
from struct import unpack, pack_into
from tkinter.filedialog import askdirectory
from traceback import format_exc

curr_dir = os.path.abspath(os.curdir)


class TeXource(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Halo TeXource v2.0")
        self.geometry("400x120+0+0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.data_dir = StringVar(self)
        self.tags_dir.set(os.path.join(curr_dir, 'tags'))
        self.data_dir.set(os.path.join(curr_dir, 'data'))

        # make the frames
        self.tags_dir_frame = LabelFrame(self, text="Tags directory")
        self.data_dir_frame = LabelFrame(self, text="Data directory")
        
        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)
        self.data_dir_entry = Entry(
            self.data_dir_frame, textvariable=self.data_dir)
        self.data_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.extract_btn = Button(
            self, text="Extract source files", width=22,
            command=self.extract_files)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)
        self.data_dir_browse_btn = Button(
            self.data_dir_frame, text="Browse",
            width=6, command=self.data_dir_browse)

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.data_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='both', side='left')
        self.data_dir_browse_btn.pack(fill='both', side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.data_dir_frame.pack(expand=True, fill='both')
        self.extract_btn.pack(fill='both', padx=5, pady=5)

    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def data_dir_browse(self):
        dirpath = askdirectory(initialdir=self.data_dir.get())
        if dirpath:
            self.data_dir.set(dirpath)

    def extract_files(self):
        print('Extracting source files...\n')
        start = time()
        tags_dir = self.tags_dir.get()
        data_dir = self.data_dir.get()

        for root, dirs, files in os.walk(tags_dir):
            for tag_name in files:
                if os.path.splitext(tag_name)[-1].lower() != '.bitmap':
                    continue
                tag_path = os.path.join(root, tag_name)

                source_path = data_dir + tag_path.split(tags_dir)[-1]
                source_path = os.path.splitext(source_path)[0] + ".tga"
                source_dir = os.path.dirname(source_path)

                print('Extracting:  %s' % tag_path.split(tags_dir)[-1][1:])

                try:
                    with open(tag_path, 'rb') as f:
                        data = f.read()

                    tag_id = data[36:40]
                    engine_id = data[60:64]
                    
                    # make sure this is a bitmap tag
                    if tag_id == b'bitm' and engine_id == b'blam':
                        dims_off = 64+24
                        size_off = 64+28
                        data_off = 64+108
                        end = ">"
                    elif tag_id == b'mtib' and engine_id == b'!MLB':
                        dims_off = 64+16+24
                        size_off = 64+16+28
                        data_off = 64+16+112
                        end = "<"
                    else:
                        print("    This file doesnt appear to be a bitmap tag.")
                        continue

                    width, height = unpack(end+"HH", data[dims_off:dims_off+4])
                    data_size = unpack(end+"i", data[size_off:size_off+4])[0]
                    data = data[data_off:data_off+data_size]
                except Exception:
                    #print(format_exc())
                    print("    Could not load bitmap tag.")
                    continue

                if not len(data):
                    print("    No source image to extract.")
                    continue

                try:
                    data_size = unpack(">I", data[:4])[0]
                    if not data_size:
                        print('    Source data is blank.')
                        continue

                    data = bytearray(zlib.decompress(data[4:]))
                except Exception:
                    #print(format_exc())
                    print('    Could not decompress data.')
                    continue

                try:
                    if not os.path.isdir(source_dir):
                        os.makedirs(source_dir)
                    with open(source_path, 'wb') as f:
                        a_depth = len(data) // (width*height) - 3

                        head = bytearray(18)
                        pack_into('B',  head, 2,  2)
                        pack_into('<H', head, 12, width)
                        pack_into('<H', head, 14, height)
                        pack_into('B',  head, 16, 32)
                        pack_into('B',  head, 17, 32 + ((a_depth*8)&15))
                        f.write(head)
                        f.write(data)
                except Exception:
                    #print(format_exc())
                    print("    Couldnt make Tga file.")
                
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    extractor = TeXource()
    extractor.mainloop()
except Exception:
    print(format_exc())
    input()
