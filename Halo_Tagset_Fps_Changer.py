import os

from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc
from reclaimer.os_v4_hek.handler import OsV4HaloHandler
from reclaimer.common_descs import tag_header_os
from supyr_struct.defs.block_def import BlockDef

tag_header_def = BlockDef(tag_header_os)

curr_dir = os.path.join(os.path.abspath(os.curdir), '')

fps_related_tag_classes = (
    'actr', 'actv', 'bipd', 'cdmg', 'coll', 'cont', 'ctrl', 'deca',
    'devi', 'effe', 'eqip', 'flag', 'fog ', 'garb', 'glw!', 'grhi',
    'hudg', 'item', 'itmc', 'jpt!', 'lens', 'lifi', 'ligh', 'mach',
    'matg', 'obje', 'part', 'pctl', 'phys', 'plac', 'proj', 'rain',
    'scen', 'scex', 'schi', 'senv', 'shpg', 'sky ', 'snde',
    # 'scnr', #  We are NOT doing scenario tags for various reasons
    'sndl', 'soso', 'sotr', 'spla', 'ssce', 'swat', 'unhi', 'unit',
    'vehi', 'weap', 'wphi')

class TagsetFpsConvertor(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.handler = OsV4HaloHandler(valid_def_ids=fps_related_tag_classes)

        self.title("Tagset Fps Changer v1.0")
        self.geometry("400x140+0+0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.fps = IntVar(self)
        self.flag_only = IntVar(self)
        self.overwrite_old = IntVar(self)
        self.tags_dir.set(os.path.join(curr_dir + 'tags', ''))
        self.fps.set(60)

        # make the frames
        self.tags_dir_frame = LabelFrame(self, text="Tags directory")
        self.checkbox_frame = LabelFrame(self, text="Conversion settings")
        self.checkbox_inner_frame1 = Frame(self.checkbox_frame)
        self.checkbox_inner_frame2 = Frame(self.checkbox_frame)
        
        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.convert_btn = Button(
            self, text="Convert directory", width=22, command=self.convert)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        self.checkbox_30_to_60 = Checkbutton(
            self.checkbox_inner_frame1, variable=self.fps,
            offvalue=30, onvalue=60, text="30 to 60")
        self.checkbox_60_to_30 = Checkbutton(
            self.checkbox_inner_frame1, variable=self.fps,
            offvalue=60, onvalue=30, text="60 to 30")
        self.checkbox_overwrite_tags = Checkbutton(
            self.checkbox_inner_frame1, variable=self.overwrite_old,
            offvalue=0, onvalue=1, text="Overwrite old tags")
        self.checkbox_flag_all_only = Checkbutton(
            self.checkbox_inner_frame2, variable=self.flag_only,
            text="Do nothing except flag all tags as 30 or 60fps")

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='both', side='left')

        for w in (self.checkbox_30_to_60, self.checkbox_60_to_30,
                  self.checkbox_overwrite_tags, self.checkbox_flag_all_only):
            w.pack(fill='both', expand=True, side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.convert_btn.pack(fill='both', padx=5, pady=5)
        self.checkbox_frame.pack(fill='both', padx=5, pady=5)
        self.checkbox_inner_frame1.pack(fill='both')
        self.checkbox_inner_frame2.pack(fill='both')

    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def convert(self):
        start = time()
        total = 0

        fps = self.fps.get()
        overwrite_old = self.overwrite_old.get()
        convert_to_60 = (fps == 60)
        flag_only = self.flag_only.get()

        prefix = '%sfps_' % fps

        handler = self.handler
        tags_dir = os.path.join(self.tags_dir.get(), '')
        get_nodes_by_paths = handler.get_nodes_by_paths
        fps_dependent_cache = handler.fps_dependent_cache

        print('Locating tags in directory with fps reliant fields...')

        handler.tagsdir = tags_dir
        tags_found = handler.index_tags(tags_dir)

        print('Found %s tags' % tags_found)
        action = 'Convert'
        if flag_only:
            action = 'Flagg'

        if tags_found:
            print('%sing tags in directory to %s fps\n' % (action, fps))

            for def_id in sorted(handler.tags.keys()):
                tag_def = handler.defs[def_id]
                tag_coll = handler.tags[def_id]
                fps_field_paths = fps_dependent_cache[def_id]
                if not tag_coll:
                    continue

                print("    %sing '%s' tags" % (action, def_id))

                for tagpath in sorted(tag_coll.keys()):
                    try:
                        filepath = os.path.join(tags_dir, tagpath)

                        blam_header = tag_header_def.build(filepath=filepath)
                        if bool(blam_header.flags.fps_60) == convert_to_60:
                            # tag is already the correct fps, so skip it
                            continue

                        print('        %s' % tagpath)
                        if flag_only:
                            # set the flag and continue to the next tag
                            blam_header.flags.fps_60 = bool(convert_to_60)
                            with open(filepath, 'r+b') as f:
                                f.write(blam_header.serialize())
                            total += 1
                            continue

                        tag = tag_def.build(filepath=filepath)

                        # rename the tag to the converted filepath
                        if not overwrite_old:
                            dirpath, filename = os.path.split(filepath)
                            tag.filepath = os.path.join(
                                dirpath, prefix + filename)

                        fields_changed = 0
                        # scale the field according to the fps for each block
                        for b in get_nodes_by_paths(fps_field_paths, tag.data):
                            if not isinstance(b, tuple):
                                raise TypeError("YA DONE FUCKED UP MOSES")
                            parent, i = b[0], b[1]
                            f_type = parent.get_desc("TYPE", i)
                            node_cls = f_type.node_cls
                            s30, s60 = parent.get_desc(
                                "UNIT_SCALE", i)(get_scales=True)

                            if parent[i] == 0:
                                continue

                            # yes, this is the correct ordering
                            if convert_to_60:
                                parent[i] = (parent[i]*s30)/s60
                            else:
                                parent[i] = (parent[i]*s60)/s30

                            if issubclass(node_cls, int):
                                parent[i] = f_type.node_cls(round(parent[i]))

                            fields_changed += 1
    
                        if not fields_changed:
                            print('            Does not contain fps relaint fields')
                            continue

                        # set the flag defining it as 60fps or not
                        tag.data.blam_header.flags.fps_60 = bool(convert_to_60)
                        tag.serialize(temp=False, backup=False)

                        del tag
                        total += 1
                    except Exception:
                        print(format_exc())
                print()

        print("%sed %s tags" % (action, total))

        handler.reset_tags()
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = TagsetFpsConvertor()
    converter.mainloop()
except SystemExit:
    pass
except Exception:
    print(format_exc())
    input()

