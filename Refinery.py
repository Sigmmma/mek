import tkinter as tk
import os
import zlib

from os.path import dirname, exists, join
from struct import unpack
from time import time
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
from tkinter.font import Font
from traceback import format_exc

#from refinery.resource_tagpaths import ce_resource_names, pc_resource_names
from refinery.byteswapping import raw_block_def, byteswap_animation,\
     byteswap_uncomp_verts, byteswap_comp_verts, byteswap_tris,\
     byteswap_coll_bsp, byteswap_sbsp_meta
from refinery.hashcacher_window import RESERVED_WINDOWS_FILENAME_MAP,\
     INVALID_PATH_CHARS, sanitize_filename, HashcacherWindow
from refinery.class_repair import class_repair_functions,\
     tag_cls_int_to_fcc, tag_cls_int_to_ext

from mozzarilla.tools.shared_widgets import HierarchyFrame

from binilla.widgets import BinillaWidget
from supyr_struct.buffer import BytearrayBuffer, PeekableMmap
from supyr_struct.defs.constants import *
from supyr_struct.field_types import FieldType

from reclaimer.os_v4_hek.handler import OsV4HaloHandler
from reclaimer.meta.halo1_map import get_map_version, get_map_header,\
     get_tag_index, get_index_magic, get_map_magic,\
     decompress_map, is_compressed
from reclaimer.meta.resource import resource_def
from reclaimer.os_hek.defs.gelc import gelc_def

from reclaimer.hek.defs.sbsp import sbsp_meta_header_def
from reclaimer.os_hek.defs.gelo    import gelo_def as old_gelo_def
from reclaimer.os_v4_hek.defs.gelo import gelo_def as new_gelo_def
from reclaimer.os_v4_hek.defs.antr import antr_def
from reclaimer.os_v4_hek.defs.bipd import bipd_def
from reclaimer.os_v4_hek.defs.cdmg import cdmg_def
from reclaimer.os_v4_hek.defs.coll import coll_def
from reclaimer.os_v4_hek.defs.jpt_ import jpt__def
from reclaimer.os_v4_hek.defs.mode import mode_def
from reclaimer.os_v4_hek.defs.soso import soso_def
from reclaimer.os_v4_hek.defs.unit import unit_def
from reclaimer.os_v4_hek.defs.vehi import vehi_def
from reclaimer.os_v4_hek.defs.sbsp import fast_sbsp_def
from reclaimer.os_v4_hek.defs.coll import fast_coll_def

from reclaimer.stubbs.defs.antr import antr_def as stubbs_antr_def
from reclaimer.stubbs.defs.cdmg import cdmg_def as stubbs_cdmg_def
from reclaimer.stubbs.defs.coll import coll_def as stubbs_coll_def
from reclaimer.stubbs.defs.jpt_ import jpt__def as stubbs_jpt__def
from reclaimer.stubbs.defs.mode import mode_def as stubbs_mode_def
from reclaimer.stubbs.defs.soso import soso_def as stubbs_soso_def
from reclaimer.stubbs.defs.sbsp import fast_sbsp_def as stubbs_fast_sbsp_def
from reclaimer.stubbs.defs.coll import fast_coll_def as stubbs_fast_coll_def
#from reclaimer.stubbs.defs.imef import imef_def
#from reclaimer.stubbs.defs.terr import terr_def
#from reclaimer.stubbs.defs.vege import vege_def

no_op = lambda *a, **kw: None

this_dir = dirname(__file__)

def run():
    return Refinery()


def is_protected(tagpath):
    return tagpath in RESERVED_WINDOWS_FILENAME_MAP or (
        not INVALID_PATH_CHARS.isdisjoint(set(tagpath)))


class Refinery(BinillaWidget, tk.Tk):
    map_path = None
    out_dir  = None
    handler  = None

    _map_loaded = False
    _running = False
    _display_mode = "hierarchy"

    last_load_dir = this_dir

    engine = None
    map_magic = None
    map_data    = None  # the complete uncompressed map
    bitmap_data = None
    sound_data  = None
    loc_data    = None

    ce_sound_offsets_by_path = None

    bitmap_rsrc_header = None
    sound_rsrc_header  = None
    loc_rsrc_header    = None

    bsp_magics = None
    bsp_sizes  = None
    bsp_headers = None
    bsp_header_offsets = None

    classes_repaired = False
    map_is_compressed = False
    stop_processing = False

    # these are the different pieces of the map as parsed blocks
    map_header = None
    tag_index = None

    matg_meta = None
    scnr_meta = None

    # a cache of all the different headers for
    # each type of tag to speed up writing tags
    tag_headers = {}

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("Refinery v1.0")
        self.minsize(width=640, height=480)
        self.geometry("%sx%s" % (640, 480))

        # make the tkinter variables
        self.map_path = tk.StringVar(self)
        self.out_dir = tk.StringVar(self)
        self.fix_tag_classes = tk.IntVar(self)
        self.use_old_gelo = tk.IntVar(self)
        self.use_resource_names = tk.IntVar(self)
        self.use_hashcaches = tk.IntVar(self)
        self.use_heuristics = tk.IntVar(self)
        self.fix_tag_classes.set(1)
        self.use_resource_names.set(1)
        self.out_dir.set(join(this_dir, "tags", ""))

        self.map_path.set("Click browse to load a map for extraction")

        # make the window pane
        self.panes = tk.PanedWindow(self, sashwidth=4)

        # make the frames
        self.map_frame        = tk.LabelFrame(self, text="Map to extract from")
        self.map_select_frame = tk.Frame(self.map_frame)
        self.map_info_frame   = tk.Frame(self.map_frame)
        self.map_action_frame = tk.Frame(self.map_frame)
        self.deprotect_frame  = tk.LabelFrame(self, text="Deprotection settings")
        self.out_dir_frame    = tk.LabelFrame(self, text="Location to extract to")

        self.explorer_frame = tk.LabelFrame(self.panes, text="Map contents")
        self.add_del_frame = tk.Frame(self.explorer_frame)
        self.queue_frame = tk.LabelFrame(self.panes, text="Extraction queue")

        self.hierarchy_frame = ExplorerHierarchyFrame(
            self.explorer_frame, app_root=self, select_mode='extended')

        # bind the queue_add to activating the hierarchy frame in some way
        self.hierarchy_frame.tags_tree.bind('<Double-Button-1>', self.queue_add)
        self.hierarchy_frame.tags_tree.bind('<Return>', self.queue_add)

        self.panes.add(self.explorer_frame)
        self.panes.add(self.queue_frame)

        # make the entries
        self.map_path_entry = tk.Entry(
            self.map_select_frame, textvariable=self.map_path, state='disabled')
        self.map_path_browse_button = tk.Button(
            self.map_select_frame, text="Browse",
            command=self.map_path_browse, width=6)

        self.out_dir_entry = tk.Entry(
            self.out_dir_frame, textvariable=self.out_dir, state='disabled')
        self.out_dir_browse_button = tk.Button(
            self.out_dir_frame, text="Browse",
            command=self.out_dir_browse, width=6)

        self.fixed_font = Font(family="Courier", size=8)
        self.map_info_text = tk.Text(self.map_info_frame, font=self.fixed_font,
                                     state='disabled', height=8)
        self.map_info_scrollbar = tk.Scrollbar(self.map_info_frame)
        self.map_info_text.config(yscrollcommand=self.map_info_scrollbar.set)
        self.map_info_scrollbar.config(command=self.map_info_text.yview)

        # make the buttons
        self.begin_button = tk.Button(
            self.map_action_frame, text="Start extraction",
            command=self.start_extraction)
        self.cancel_button = tk.Button(
            self.map_action_frame, text="Cancel extraction",
            command=self.cancel_extraction)

        self.fix_tag_classes_checkbutton = tk.Checkbutton(
            self.deprotect_frame, text="Fix tag classes",
            variable=self.fix_tag_classes)
        self.use_resource_names_checkbutton = tk.Checkbutton(
            self.deprotect_frame, text="Use resource names",
            variable=self.use_resource_names)
        self.use_hashcaches_checkbutton = tk.Checkbutton(
            self.deprotect_frame, text="Use hashcaches",
            variable=self.use_hashcaches)
        self.use_heuristics_checkbutton = tk.Checkbutton(
            self.deprotect_frame, text="Use heuristics",
            variable=self.use_heuristics)
        self.deprotect_button = tk.Button(
            self.deprotect_frame, text="Run deprotection",
            command=self.deprotect)

        self.add_button = tk.Button(self.add_del_frame, text="Add",
                                    width=4, command=self.queue_add)
        self.del_button = tk.Button(self.add_del_frame, text="Del",
                                    width=4, command=self.queue_del)

        self.add_all_button = tk.Button(
            self.add_del_frame, text="Add\nAll", width=4,
            command=self.queue_add_all)
        self.del_all_button = tk.Button(
            self.add_del_frame, text="Del\nAll", width=4,
            command=self.queue_del_all)

        # pack everything
        self.map_path_entry.pack(
            padx=(4, 0), pady=2, side='left', expand=True, fill='x')
        self.map_path_browse_button.pack(padx=(0, 4), pady=2, side='left')

        self.cancel_button.pack(side='right', padx=4, pady=4)
        self.begin_button.pack(side='right', padx=4, pady=4)

        self.fix_tag_classes_checkbutton.pack(side='left', padx=4, pady=4)
        #self.use_resource_names_checkbutton.pack(side='left', padx=4, pady=4)
        self.use_hashcaches_checkbutton.pack(side='left', padx=4, pady=4)
        self.use_heuristics_checkbutton.pack(side='left', padx=4, pady=4)
        self.deprotect_button.pack(side='right', padx=4, pady=4)

        self.map_select_frame.pack(fill='x', expand=True, padx=1)
        self.map_info_frame.pack(fill='x', expand=True, padx=1)
        self.map_info_scrollbar.pack(fill='y', side='right', padx=1)
        self.map_info_text.pack(fill='x', side='right', expand=True, padx=1)
        self.map_action_frame.pack(fill='x', expand=True, padx=1)

        self.out_dir_entry.pack(
            padx=(4, 0), pady=2, side='left', expand=True, fill='x')
        self.out_dir_browse_button.pack(padx=(0, 4), pady=2, side='left')

        self.add_button.pack(side='top', padx=2, pady=4)
        self.del_button.pack(side='top', padx=2, pady=(0, 20))
        self.add_all_button.pack(side='top', padx=2, pady=(20, 0))
        self.del_all_button.pack(side='top', padx=2, pady=4)

        self.explorer_frame.pack(fill='both', padx=1, expand=True)
        self.add_del_frame.pack(side='right', fill='y', anchor='center')
        self.hierarchy_frame.pack(side='right', fill='both', expand=True)
        self.queue_frame.pack(fill='y', padx=1, expand=True)

        self.map_frame.pack(fill='x', padx=1)
        self.out_dir_frame.pack(fill='x', padx=1)

        # Not gonna do anything with deprotecting for a while.
        # just gonna remove this from the ui for the time being
        #self.deprotect_frame.pack(fill='x', padx=1)
        self.panes.pack(fill='both', expand=True)

        self.panes.paneconfig(self.explorer_frame, sticky='nsew')
        self.panes.paneconfig(self.queue_frame, sticky='nsew')

        self.handler = handler = OsV4HaloHandler()
        self.handler.add_def(gelc_def)
        #self.handler.add_def(imef_def)
        #self.handler.add_def(terr_def)
        #self.handler.add_def(vege_def)
        
        # create a bunch of tag headers for each type of tag
        for def_id in sorted(handler.defs):
            if len(def_id) != 4:
                continue
            h_desc = handler.defs[def_id].descriptor[0]
            
            h_block = [None]
            h_desc['TYPE'].parser(h_desc, parent=h_block, attr_index=0)
            b_buffer = h_block[0].serialize(buffer=BytearrayBuffer(),
                                            calc_pointers=False)

            self.tag_headers[def_id] = bytes(b_buffer)
            del b_buffer[:]

    @property
    def running(self):
        return self._running

    @property
    def tags_dir(self):
        return self.out_dir.get()

    def destroy(self):
        self.unload_maps()
        FieldType.force_normal()
        tk.Tk.destroy(self)

        # I really didn't want to have to call this, but for some
        # reason the program wants to hang and not exit nicely.
        # I've decided to use os._exit until I can figure out the cause.
        os._exit(0)
        #sys.exit(0)

    def queue_add(self, e=None):
        if not self._map_loaded:
            return

        tags_tree = self.hierarchy_frame.tags_tree

        iids = tags_tree.selection()
        if not iids:
            return

        # make a popup window asking how to extract this tag/directory

    def queue_del(self, e=None):
        if not self._map_loaded:
            return

        tags_tree = self.queue_frame.queue_tree

        iids = queue_tree.selection()
        if not iids:
            return

    def queue_add_all(self, e=None):
        if not self._map_loaded:
            return

        tags_tree = self.hierarchy_frame.tags_tree

        # make a popup window asking how to extract this tag/directory

    def queue_del_all(self, e=None):
        if not self._map_loaded:
            return

        tags_tree = self.queue_frame.queue_tree

    def unload_maps(self):
        try: self.map_data.close()
        except Exception: pass
        try: self.bitmap_data.close()
        except Exception: pass
        try: self.sound_data.close()
        except Exception: pass
        try: self.loc_data.close()
        except Exception: pass
        self.tag_index = self.map_header = self.ce_sound_offsets_by_path = None
        
        self.bitmap_rsrc_header = None
        self.sound_rsrc_header  = None
        self.loc_rsrc_header    = None
        self.scnr_meta = self.matg_meta = None
        self.bitmap_data = self.sound_data = self.loc_data = self.map_data = None
        self.map_magic = self.index_magic = None
        self.bsp_magics = self.bsp_sizes = self.bsp_headers = None
        self.bsp_header_offsets = None
        self._map_loaded = self._running = False
        self.stop_processing = True
        self.classes_repaired = False

    def set_defs(self):
        '''Switch definitions based on which game the map is for'''
        defs = self.handler.defs
        if "stubbs" in self.engine:
            defs["antr"] = stubbs_antr_def
            defs["bipd"] = None
            defs["cdmg"] = stubbs_cdmg_def
            defs["jpt!"] = stubbs_jpt__def
            defs["mode"] = stubbs_mode_def
            defs["soso"] = stubbs_soso_def
            defs["unit"] = None
            defs["vehi"] = None
            defs["sbsp"] = stubbs_fast_sbsp_def
            defs["coll"] = stubbs_fast_coll_def
            #defs["imef"] = imef_def
            #defs["vege"] = vege_def
            #defs["terr"] = terr_def
        else:
            defs["antr"] = antr_def
            defs["bipd"] = bipd_def
            defs["cdmg"] = cdmg_def
            defs["jpt!"] = jpt__def
            defs["mode"] = mode_def
            defs["soso"] = soso_def
            defs["unit"] = unit_def
            defs["vehi"] = vehi_def
            defs["sbsp"] = fast_sbsp_def
            defs["coll"] = fast_coll_def
            defs.pop("imef", None)
            defs.pop("vege", None)
            defs.pop("terr", None)

        self.handler.reset_tags()

    def load_map(self, map_path=None):
        try:
            if map_path is None:
                map_path = self.map_path.get()
            if not exists(map_path):
                return
            elif self.running:
                return

            self._running = True
            self.map_path.set(map_path)

            with open(map_path, 'rb+') as f:
                comp_data = PeekableMmap(f.fileno(), 0)

            self.map_header = get_map_header(comp_data)
            self.engine     = get_map_version(self.map_header)
            self.map_is_compressed = is_compressed(comp_data, self.map_header)

            decomp_path = None
            if self.map_is_compressed:
                decomp_path = asksaveasfilename(
                    initialdir=dirname(map_path), parent=self,
                    title="Choose where to save the decompressed map",
                    filetypes=(("mapfile", "*.map"), ("All", "*")))
            self.map_data   = decompress_map(
                comp_data, self.map_header, decomp_path)

            self.index_magic = get_index_magic(self.map_header)
            self.map_magic = get_map_magic(self.map_header)
            self.tag_index = get_tag_index(self.map_data, self.map_header)
            tag_index_array = self.tag_index.tag_index

            self.set_defs()
            self._map_loaded = True

            # make all contents of the map parasble
            self.basic_deprotection()

            # get the scenario meta
            try:
                self.bsp_magics = bsp_magics = {}
                self.bsp_sizes  = bsp_sizes  = {}
                self.bsp_header_offsets = bsp_offsets = {}
                self.bsp_headers = {}

                self.scnr_meta = self.get_meta(self.tag_index.scenario_tag_id[0])
                for b in self.scnr_meta.structure_bsps.STEPTREE:
                    bsp = b.structure_bsp
                    bsp_offsets[bsp.id[0]] = b.bsp_pointer
                    bsp_magics[bsp.id[0]]  = b.bsp_magic
                    bsp_sizes[bsp.id[0]]   = b.bsp_size

                # read the sbsp headers
                for tag_id in self.bsp_header_offsets:
                    header = sbsp_meta_header_def.build(
                        rawdata=self.map_data, offset=bsp_offsets[tag_id])
                    self.bsp_headers[tag_id] = header
                    if header.sig != header.get_desc("DEFAULT", "sig"):
                        print("Sbsp header is invalid for '%s'" %
                              tag_index_array[tag_id].tag.tag_path)

                if self.scnr_meta is None:
                    print("Could not read scenario tag")
            except Exception:
                print(format_exc())
                print("Could not read scenario tag")

            # get the globals meta
            try:
                for b in tag_index_array:
                    if tag_cls_int_to_fcc.get(b.class_1.data) == "matg":
                        self.matg_meta = self.get_meta(b.id[0])
                        break
                if self.matg_meta is None:
                    print("Could not read globals tag")
            except Exception:
                print(format_exc())
                print("Could not read globals tag")

            self.display_map_info()
            self.hierarchy_frame.map_magic = self.map_magic
            self.reload_map_explorer()

            maps_dir = dirname(map_path)

            bitmap_data = sound_data = loc_data = None
            bitmap_path = sound_path = loc_path = None
            bitmap_rsrc = sound_rsrc = loc_rsrc = None

            if self.engine in ("pc", "pcdemo"):
                bitmap_path = join(maps_dir, "bitmaps.map")
                sound_path  = join(maps_dir, "sounds.map")
            elif self.engine in ("ce", "yelo"):
                bitmap_path = join(maps_dir, "bitmaps.map")
                sound_path  = join(maps_dir, "sounds.map")
                loc_path    = join(maps_dir, "loc.map")

            while bitmap_data is None and bitmap_path:
                print("Loading bitmaps.map...")
                try:
                    with open(bitmap_path, 'rb+') as f:
                        bitmap_data = PeekableMmap(f.fileno(), 0)
                        maps_dir = dirname(bitmap_path)
                        bitmap_rsrc = resource_def.build(rawdata=bitmap_data)
                        bitmap_data.seek(0)
                        print("    Finished")
                except Exception:
                    bitmap_path = askopenfilename(
                        initialdir=maps_dir, parent=self,
                        title="Select the %s bitmaps.map" % self.engine,
                        filetypes=(("bitmaps.map", "*.map"), ("All", "*")))
                if not bitmap_path:
                    print("    You will be unable to extract " +
                          "bitmaps stored in bitmaps.map")

            while sound_data is None and sound_path:
                print("Loading sounds.map...")
                try:
                    with open(sound_path, 'rb+') as f:
                        sound_data = PeekableMmap(f.fileno(), 0)
                        maps_dir = dirname(sound_path)
                        sound_rsrc = resource_def.build(rawdata=sound_data)
                        sound_data.seek(0)
                        print("    Finished")

                        if self.engine in ("ce", "yelo"):
                            # ce resource sounds are recognized by tag_path
                            # so we must cache their offsets by their paths
                            self.ce_sound_offsets_by_path = sound_map = {}
                            for i in range(len(sound_rsrc.tag_paths)):
                                tag_path   = sound_rsrc.tag_paths[i].tag_path
                                tag_offset = sound_rsrc.tag_headers[i].offset
                                sound_map[tag_path] = tag_offset

                except Exception:
                    sound_path = askopenfilename(
                        initialdir=maps_dir, parent=self,
                        title="Select the %s sounds.map" % self.engine,
                        filetypes=(("sounds.map", "*.map"), ("All", "*")))
                if not sound_path:
                    print("    You will be unable to extract " +
                          "sounds stored in sounds.map")

            while loc_data is None and loc_path:
                print("Loading loc.map...")
                try:
                    with open(loc_path, 'rb+') as f:
                        loc_data = PeekableMmap(f.fileno(), 0)
                        maps_dir = dirname(loc_path)
                        loc_rsrc = resource_def.build(rawdata=loc_data)
                        loc_data.seek(0)
                        print("    Finished")
                except Exception:
                    loc_path = askopenfilename(
                        initialdir=maps_dir,
                        title="Select the loc.map", parent=self,
                        filetypes=(("loc.map", "*.map"), ("All", "*")))
                if not loc_path:
                    print("    You will be unable to extract " +
                          "tags stored in loc.map")

            self.bitmap_data = bitmap_data
            self.sound_data  = sound_data
            self.loc_data    = loc_data
            self.bitmap_rsrc_header = bitmap_rsrc
            self.sound_rsrc_header  = sound_rsrc
            self.loc_rsrc_header    = loc_rsrc

            try:
                if comp_data is not self.map_data:
                    comp_data.close()
            except Exception:
                pass
        except Exception:
            try: comp_data.close()
            except Exception: pass
            self.display_map_info(
                "Could not load map.\nCheck console window for error.")
            self.reload_map_explorer()
            raise

        self._running = False

    def display_map_info(self, string=None):
        if string is None:
            if not self._map_loaded:
                return
            try:
                header = self.map_header
                index = self.tag_index
                decomp_size = "uncompressed"
                if self.map_is_compressed:
                    decomp_size = len(self.map_data)

                map_type = header.map_type.enum_name
                if   map_type == "sp": map_type = "singleplayer"
                elif map_type == "mp": map_type = "multiplayer"
                elif map_type == "ui": map_type = "user interface"
                else: map_type = "unknown"
                string = ((
                    "Header:\n" +
                    "    map name            == '%s'\n" +
                    "    build date          == '%s'\n" +
                    "    map type            == %s\n" +
                    "    decompressed size   == %s\n" +
                    "    index header offset == %s\n") %
                (header.map_name, header.build_date, map_type,
                 decomp_size, header.tag_index_header_offset))

                string += ((
                    "\nCalculated information:\n" +
                    "    engine version == %s\n" +
                    "    index magic    == %s\n" +
                    "    map magic      == %s\n") %
                (self.engine, self.index_magic, self.map_magic))

                tag_index_offset = index.tag_index_offset
                string += ((
                    "\nTag index:\n" +
                    "    tag count           == %s\n" +
                    "    scenario tag id     == %s\n" +
                    "    index array offset  == %s   non-magic == %s\n" +
                    "    meta data length    == %s\n" +
                    "    vertex parts count  == %s\n" +
                    "    index  parts count  == %s\n" ) %
                (index.tag_count, index.scenario_tag_id[0],
                 tag_index_offset, tag_index_offset - self.map_magic,
                 header.tag_index_meta_len,
                 index.vertex_parts_count, index.index_parts_count))

                if index.SIZE == 36:
                    string += ((
                        "    vertex parts offset == %s   non-magic == %s\n" +
                        "    index  parts offset == %s   non-magic == %s\n") %
                    (index.vertex_parts_offset,
                     index.vertex_parts_offset - self.map_magic,
                     index.index_parts_offset,
                     index.index_parts_offset - self.map_magic))
                else:
                    string += ((
                        "    vertex data size    == %s\n" +
                        "    index  data size    == %s\n") %
                    (index.vertex_data_size, index.index_data_size))

                if self.engine == "yelo":
                    yelo = header.yelo_header
                    flags = yelo.flags
                    info = yelo.build_info
                    min_os = info.minimum_os_build
                    version = yelo.tag_versioning
                    cheape = yelo.cheape_definitions
                    rsrc = yelo.resources
                    string += ((
                        "\n\nYelo information:\n" +
                        "    Mod name              == '%s'\n" +
                        "    Memory upgrade amount == %sx\n" +
                        "\n    Flags:\n" +
                        "        uses memory upgrades       == %s\n" +
                        "        uses mod data files        == %s\n" +
                        "        is protected               == %s\n" +
                        "        uses game state upgrades   == %s\n" +
                        "        has compression parameters == %s\n" +
                        "\n    Build info:\n" +
                        "        build string  == '%s'\n" +
                        "        timestamp     == %s\n" +
                        "        stage         == %s\n" +
                        "        revision      == %s\n" +
                        "\n    Cheape:\n" +
                        "        build string      == '%s'\n" +
                        "        version           == %s.%s.%s\n" +
                        "        size              == %s\n" +
                        "        offset            == %s\n" +
                        "        decompressed size == %s\n" +
                        "\n    Versioning:\n" +
                        "        minimum open sauce     == %s.%s.%s\n" +
                        "        project yellow         == %s\n" +
                        "        project yellow globals == %s\n" +
                        "\n    Resources:\n" +
                        "        compression parameters header offset   == %s\n" +
                        "        tag symbol storage header offset       == %s\n" +
                        "        string id storage header offset        == %s\n" +
                        "        tag string to id storage header offset == %s\n"
                        ) %
                    (yelo.mod_name, yelo.memory_upgrade_multiplier,
                     bool(flags.uses_memory_upgrades),
                     bool(flags.uses_mod_data_files),
                     bool(flags.is_protected),
                     bool(flags.uses_game_state_upgrades),
                     bool(flags.has_compression_params),
                     info.build_string, info.timestamp, info.stage.enum_name,
                     info.revision, cheape.build_string,
                     info.cheape.maj, info.cheape.min, info.cheape.build,
                     cheape.size, cheape.offset, cheape.decompressed_size,
                     min_os.maj, min_os.min, min_os.build,
                     version.project_yellow, version.project_yellow_globals,
                     rsrc.compression_params_header_offset,
                     rsrc.tag_symbol_storage_header_offset,
                     rsrc.string_id_storage_header_offset,
                     rsrc.tag_string_to_id_storage_header_offset,
                    ))

                string += "\nSbsp magic and headers:\n"
                for tag_id in self.bsp_magics:
                    header = self.bsp_headers[tag_id]
                    magic  = self.bsp_magics[tag_id]
                    string += ((
                        "    %s.structure_scenario_bsp\n" +
                        "        bsp base pointer               == %s\n" +
                        "        bsp magic                      == %s\n" +
                        "        bsp size                       == %s\n" +
                        "        bsp metadata pointer           == %s   non-magic == %s\n" +
                        "        uncompressed lightmaps count   == %s\n" +
                        "        uncompressed lightmaps pointer == %s   non-magic == %s\n" +
                        "        compressed   lightmaps count   == %s\n" +
                        "        compressed   lightmaps pointer == %s   non-magic == %s\n") %
                    (index.tag_index[tag_id].tag.tag_path,
                     self.bsp_header_offsets[tag_id],
                     magic, self.bsp_sizes[tag_id],
                     header.meta_pointer, header.meta_pointer - magic,
                     header.uncompressed_lightmap_materials_count,
                     header.uncompressed_lightmap_materials_pointer,
                     header.uncompressed_lightmap_materials_pointer - magic,
                     header.compressed_lightmap_materials_count,
                     header.compressed_lightmap_materials_pointer,
                     header.compressed_lightmap_materials_pointer - magic,
                     ))
            except Exception:
                string = ""
                print(format_exc())
        try:
            self.map_info_text.config(state='normal')
            self.map_info_text.delete('1.0', 'end')
            self.map_info_text.insert('end', string)
        finally:
            self.map_info_text.config(state='disabled')

    def is_indexed(self, tag_index_ref):
        if self.engine in ("ce", "yelo"):
            return bool(tag_index_ref.indexed)
        else:
            return False

    def basic_deprotection(self):
        if not self._map_loaded:
            return
        print("Running basic deprotection...")
        # rename all invalid names to usable ones
        i = 0
        for b in self.tag_index.tag_index:
            if is_protected(b.tag.tag_path):
                b.tag.tag_path = "protected_%s" % i
                i += 1
        print("    Finished")

    def deprotect(self, e=None):
        if not self._map_loaded:
            return
        elif self.running:
            return

        start = time()
        self.stop_processing = False
        self._running = True

        tag_index = self.tag_index
        tag_index_array = tag_index.tag_index
        map_data = self.map_data

        if self.fix_tag_classes.get() and (not self.classes_repaired and
                                           "stubbs" not in self.engine):
            print("Repairing tag classes")
            repaired = set()
            magic = self.map_magic
            bsp_magic = self.bsp_magic

            # call a recursive deprotect on the globals, scenario, all
            # tag_collections, and all ui_widget_definitions
            class_repair_functions["scnr"](map_data, tag_index_array, repaired,
                                           magic, bsp_magic,
                                           tag_index.scenario_tag_id[0],
                                           self.engine)
            if self.stop_processing:
                print("    Deprotection stopped by user.")
                self._running = False
                return

            self.scnr_meta = self.get_meta(tag_index.scenario_tag_id[0])

            for b in tag_index_array:
                if self.stop_processing:
                    print("    Deprotection stopped by user.")
                    self._running = False
                    return

                if tag_cls_int_to_fcc.get(b.class_1.data) == "tagc":
                    class_repair_functions["tagc"](map_data, tag_index_array,
                                                   repaired, magic, bsp_magic,
                                                   b.id[0], self.engine)
                elif tag_cls_int_to_fcc.get(b.class_1.data) == "Soul":
                    class_repair_functions["Soul"](map_data, tag_index_array,
                                                   repaired, magic, bsp_magic,
                                                   b.id[0], self.engine)
                elif tag_cls_int_to_fcc.get(b.class_1.data) == "matg":
                    class_repair_functions["matg"](map_data, tag_index_array,
                                                   repaired, magic, bsp_magic,
                                                   b.id[0], self.engine)
                    # replace self.matg_meta with the deprotected one
                    self.matg_meta = self.get_meta(b.id[0])

            self.classes_repaired = True
            # make sure the changes are committed
            map_data.flush()
        '''
        if self.use_resource_names.get() and self.engine in ("pc","ce","yelo"):
            print("Detecting resource tags...")
            i = 0
            resource_names = pc_resource_names
            if self.engine in ("yelo", "ce"):
                resource_names = ce_resource_names

            for b in tag_index_array:
                if self.stop_processing:
                    print("    Deprotection stopped by user.")
                    self._running = False
                    return

                cls_fcc = tag_cls_int_to_fcc.get(b.class_1.data)
                if cls_fcc == "matg" and self.engine != "yelo":
                    b.tag.tag_path == "globals\\globals"
                    continue

                if not self.is_indexed(b):
                    continue
                try:
                    b.tag.tag_path = resource_names[cls_fcc][b.meta_offset]
                except (IndexError, KeyError):
                    try:
                        curr_path = b.tag.tag_path
                        if is_protected(curr_path):
                            b.tag.tag_path = "indexed_protected_%s" % i
                            i += 1
                    except Exception:
                        print(format_exc())
        '''
        print("    Finished")

        self._running = False
        print("Completed. Took %s seconds." % round(time()-start, 1))
        self.display_map_info()
        self.reload_map_explorer()

    def start_extraction(self, e=None):
        if not self._map_loaded:
            return
        elif self.running:
            return

        self._running = True
        out_dir = self.out_dir.get()
        handler = self.handler

        tag_index = self.tag_index
        tag_index_array = tag_index.tag_index
        start = time()
        self.stop_processing = False

        for i in range(len(tag_index_array)):
            try:
                self.update()
                tag_path = "<could not get tag path>"
                if self.stop_processing:
                    print("Extraction stopped by user\n")
                    self._running = False
                    return
                tag_index_ref = tag_index_array[i]

                tag_cls = tag_cls_int_to_fcc.get(tag_index_ref.class_1.data)
                tag_ext = tag_cls_int_to_ext.get(
                    tag_index_ref.class_1.data, "INVALID")
                tag_path = "%s.%s" % (tag_index_ref.tag.tag_path, tag_ext)
                abs_tag_path = join(out_dir, tag_path)
                if tag_cls is None:
                    print(("    Unknown tag class for '%s'\n" +
                           "    Run deprotection to fix this.") % tag_path)
                    continue

                meta = self.get_meta(i)
                if not meta:
                    continue

                meta = self.meta_to_tag_data(meta, tag_cls, tag_index_ref)
                self.update()
                if not meta:
                    continue

                print(tag_path)

                if not exists(dirname(abs_tag_path)):
                    os.makedirs(dirname(abs_tag_path))

                FieldType.force_big()
                with open(abs_tag_path, "wb") as f:
                    f.write(self.tag_headers[tag_cls])
                    f.write(meta.serialize(calc_pointers=False))
            except Exception:
                print(format_exc())
                print("Error ocurred while extracting '%s'" % tag_path)
                
            FieldType.force_normal()

        self._running = False
        print("Extraction complete. Took %s seconds\n" % round(time()-start, 1))

    def get_ce_resource_tag(self, tag_cls, tag_index_ref):
        '''Returns just the meta of the tag without any raw data.'''
        # read the meta data from the map
        if self.handler.defs.get(tag_cls) is None:
            return
        elif self.engine not in ("ce", "yelo"):
            return

        kwargs = dict(parsing_resource=True)
        if tag_cls == "snd!":
            map_data = self.sound_data

            sound_map = self.ce_sound_offsets_by_path
            tag_path  = tag_index_ref.tag.tag_path
            if sound_map is None or tag_path not in sound_map:
                return

            meta_offset = sound_map[tag_path]
        else:
            if tag_cls == "bitm":
                map_data  = self.bitmap_data
                rsrc_head = self.bitmap_rsrc_header
            else:
                map_data  = self.loc_data
                rsrc_head = self.loc_rsrc_header

            meta_offset = tag_index_ref.meta_offset
            meta_offset = rsrc_head.tag_headers[meta_offset].offset
            kwargs = dict(magic=0)

        h_desc  = self.handler.defs[tag_cls].descriptor[1]
        h_block = [None]

        try:
            FieldType.force_little()
            h_desc['TYPE'].parser(
                h_desc, parent=h_block, attr_index=0, rawdata=map_data,
                tag_index=self.tag_index, root_offset=meta_offset, **kwargs)
            FieldType.force_normal()
        except Exception:
            print(format_exc())
            FieldType.force_normal()
            for line in h_block[0].__str__().split("\n"):
                try:
                    print(line)
                except Exception:
                    print("Could not print line")
            return

        return h_block[0]

    def get_meta(self, tag_id):
        '''
        Takes a tag reference id as the sole argument.
        Returns that tags meta data as a parsed block.
        '''
        tag_index = self.tag_index
        map_data = self.map_data
        magic = self.map_magic

        # if we are given a 32bit tag id, mask it off
        tag_id &= 0xFFFF

        tag_index_ref = tag_index.tag_index[tag_id]
        if tag_id != tag_index.scenario_tag_id[0]:
            tag_cls = tag_cls_int_to_fcc.get(tag_index_ref.class_1.data)
        else:
            tag_cls = "scnr"

        # if we dont have a defintion for this tag_cls, then return nothing
        if self.handler.defs.get(tag_cls) is None:
            return

        if tag_cls is None:
            # couldn't determine the tag class
            return
        elif tag_id == tag_index.scenario_tag_id[0] and self.scnr_meta:
            return self.scnr_meta
        elif tag_cls == "matg" and self.matg_meta:
            return self.matg_meta
        elif self.is_indexed(tag_index_ref) and self.engine in ("ce", "yelo"):
            # tag exists in a resource cache
            return self.get_ce_resource_tag(tag_cls, tag_index_ref)

        if tag_cls != "gelo":
            h_desc = self.handler.defs[tag_cls].descriptor[1]
        elif self.use_old_gelo.get():
            h_desc = old_gelo_def.descriptor[1]
        else: 
            h_desc = new_gelo_def.descriptor[1]
        
        h_block = [None]
        offset = tag_index_ref.meta_offset - magic
        if tag_cls == "sbsp":
            # bsps use their own magic because they are stored in
            # their own section of the map, directly after the header
            magic = self.bsp_magics[tag_id] - self.bsp_header_offsets[tag_id]
            offset = self.bsp_headers[tag_id].meta_pointer - magic

        try:
            # read the meta data from the map
            FieldType.force_little()
            h_desc['TYPE'].parser(
                h_desc, parent=h_block, attr_index=0, magic=magic,
                tag_index=tag_index, rawdata=map_data, offset=offset)
            FieldType.force_normal()
        except Exception:
            print(format_exc())
            FieldType.force_normal()
            return

        return h_block[0]

    def meta_to_tag_data(self, meta, tag_cls, tag_index_ref):
        tag_index = self.tag_index
        magic = self.map_magic
        engine = self.engine

        map_data = self.map_data
        bitmap_data = self.bitmap_data
        sound_data  = self.sound_data
        loc_data    = self.loc_data
        tag_index   = tag_index.tag_index

        # need to treat all a8r8g8b8 values in each tag as a UInt32
        # so it can be byteswapped when going from meta to tag
        if tag_cls == "antr":
            # byteswap animation data
            for anim in meta.animations.STEPTREE:
                byteswap_animation(anim)

        elif tag_cls == "bitm":
            # grab bitmap data correctly from map and set the
            # size of the compressed plate data to nothing

            new_pixels = BytearrayBuffer()
            meta.compressed_color_plate_data.STEPTREE = BytearrayBuffer()

            if engine in ("ce", "yelo") and not self.is_indexed(tag_index_ref):
                bitmap_data = map_data
            elif engine in ("stubbs", "pcstubbs", "xbox"):
                bitmap_data = map_data
            elif engine in ("pc", "ce") and bitmap_data is None:
                return

            is_xbox = engine == "stubbs" or "xbox" in engine

            # uncheck the prefer_low_detail flag, get the pixel data
            # from the map, and set up the pixels_offset correctly.
            for bitmap in meta.bitmaps.STEPTREE:
                bitmap.flags.xbox_bitmap = False
                new_pixels_offset = len(new_pixels)

                # grab the bitmap data from this map(no magic used)
                bitmap_data.seek(bitmap.pixels_offset)
                new_pixels += bitmap_data.read(bitmap.pixels_meta_size)

                bitmap.pixels_offset = new_pixels_offset
                # clear some meta-only fields
                bitmap.pixels_meta_size = 0
                bitmap.bitmap_id_unknown1 = bitmap.bitmap_id_unknown2 = 0
                bitmap.bitmap_data_pointer = bitmap.base_address = 0

            meta.processed_pixel_data.STEPTREE = new_pixels
        elif tag_cls == "coll":
            # byteswap the raw bsp collision data
            for node in meta.nodes.STEPTREE:
                for perm_bsp in node.bsps.STEPTREE:
                    byteswap_coll_bsp(perm_bsp)
        elif tag_cls == 'effe':
            # mask away the meta-only flags
            meta.flags.data &= 3
        elif tag_cls in ("mode", "mod2"):

            if engine in ("yelo", "ce", "pc", "pcdemo", "pcstubbs"):
                # model_magic seems to be the same for all pc maps
                # need to figure out what that magic is though.........
                model_magic = 0
            else:
                model_magic = magic
            # grab vertices and indices from the map
            if tag_cls == "mode":
                verts_attr_name = "compressed_vertices"
                byteswap_verts = byteswap_comp_verts
                vert_size = 32
            else:
                verts_attr_name = "uncompressed_vertices"
                byteswap_verts = byteswap_uncomp_verts
                vert_size = 68

                # need to swap the lod cutoff and nodes values around
                cutoffs = (meta.superlow_lod_cutoff, meta.low_lod_cutoff,
                           meta.high_lod_cutoff, meta.superhigh_lod_cutoff)
                nodes = (meta.superlow_lod_nodes, meta.low_lod_nodes,
                         meta.high_lod_nodes, meta.superhigh_lod_nodes)
                meta.superlow_lod_cutoff  = cutoffs[3]
                meta.low_lod_cutoff       = cutoffs[2]
                meta.high_lod_cutoff      = cutoffs[1]
                meta.superhigh_lod_cutoff = cutoffs[0]
                meta.superlow_lod_nodes  = nodes[3]
                meta.low_lod_nodes       = nodes[2]
                meta.high_lod_nodes      = nodes[1]
                meta.superhigh_lod_nodes = nodes[0]

            for geom in meta.geometries.STEPTREE:
                for part in geom.parts.STEPTREE:
                    input(part)
                    verts_block = part[verts_attr_name]
                    tris_block  = part.triangles
                    info  = part.model_meta_info

                    # null out certain things in the part
                    part.previous_part_index = part.next_part_index = 0
                    part.centroid_primary_node = 0
                    part.centroid_secondary_node = 0
                    part.centroid_primary_weight = 0.0
                    part.centroid_secondary_weight = 0.0

                    # make the new blocks to hold the raw data
                    verts_block.STEPTREE = raw_block_def.build()
                    tris_block.STEPTREE  = raw_block_def.build()

                    # read the offsets of the vertices and indices from the map
                    map_data.seek(info.vertices_reflexive_offset+4-model_magic)
                    verts_off = unpack("<I", map_data.read(4))[0]
                    map_data.seek(info.indices_reflexive_offset +4-model_magic)
                    tris_off  = unpack("<I", map_data.read(4))[0]

                    # read the raw data from the map
                    map_data.seek(verts_off - model_magic)
                    raw_verts = map_data.read(vert_size*info.vertex_count)
                    map_data.seek(tris_off - model_magic)
                    raw_tris  = map_data.read(2*info.index_count)

                    # put the raw data in the verts and tris blocks
                    verts_block.STEPTREE.data = raw_verts
                    tris_block.STEPTREE.data  = raw_tris

                    # call the byteswappers
                    byteswap_verts(verts_block)
                    byteswap_tris(tris_block)

                    # null out the model_meta_info
                    info.index_type.data  = info.index_count  = 0
                    info.vertex_type.data = info.vertex_count = 0
                    info.indices_offset   = info.indices_reflexive_offset  = 0
                    info.vertices_offset  = info.vertices_reflexive_offset = 0
        elif tag_cls == "scnr":
            # need to remove the references to the child scenarios
            del meta.child_scenarios.STEPTREE[:]
        elif tag_cls == 'pphy':
            # set the meta-only values to 0
            meta.wind_coefficient = 0
            meta.wind_sine_modifier = 0
            meta.z_translation_rate = 0
        elif tag_cls == "sbsp":
            byteswap_sbsp_meta(meta)
            # null the first 8 bytes of each leaf

            # null the last 28 bytes of each breakable_surface
        elif tag_cls == "scnr":
            # set the bsp pointers and stuff to 0
            for b in meta.structure_bsps.STEPTREE:
                b.bsp_pointer = b.bsp_size = b.bsp_magic = 0
        elif tag_cls == "snd!":
            # might need to get samples and permutations from the resource map

            if not(self.is_indexed(tag_index_ref) or engine in ("pc","pcdemo")):
                return meta

            # ce tagpaths are in the format:  path__permutations
            #     ex: sound\sfx\impulse\coolant\enter_water__permutations
            #
            # pc tagpaths are in the format:  path__pitch_range__permutation
            #     ex: sound\sfx\impulse\coolant\enter_water__0__0
            for pitches in meta.pitch_ranges.STEPTREE:
                for perm in pitches.permutations.STEPTREE:
                    for b in (perm.samples, perm.mouth_data, perm.subtitle_data):
                        if not b.size:
                            continue
                        sound_data.seek(b.raw_pointer)
                        b.STEPTREE = sound_data.read(b.size)
        return meta

    def cancel_extraction(self, e=None):
        if not self._map_loaded:
            return
        self.stop_processing = True

    def reload_map_explorer(self):
        if not self._map_loaded:
            return
        print("Reloading map explorer...")
        self.hierarchy_frame.reload(self.tag_index)
        self.update()
        print("    Finished")

    def map_path_browse(self):
        if self.running:
            return
        fp = askopenfilename(
            initialdir=self.last_load_dir,
            title="Select map to load", parent=self,
            filetypes=(("Halo mapfile", "*.map"),
                       ("Halo mapfile(extra sauce)", "*.yelo"),
                       ("All", "*")))

        if not fp:
            return

        fp = sanitize_path(fp)
        self.last_load_dir = dirname(fp)
        self.map_path.set(fp)
        self.unload_maps()
        self.load_map()

    def out_dir_browse(self):
        if self.running:
            return
        dirpath = askdirectory(initialdir=self.out_dir.get(), parent=self,
                               title="Select the extraction directory")

        if not dirpath:
            return

        dirpath = sanitize_path(dirpath)
        if not dirpath.endswith(PATHDIV):
            dirpath += PATHDIV

        self.out_dir.set(dirpath)


class ExplorerHierarchyFrame(HierarchyFrame):
    map_magic = None
    tag_index = None

    def __init__(self, *args, **kwargs):
        HierarchyFrame.__init__(self, *args, **kwargs)

    def reload(self, tag_index=None):
        self.tag_index = tag_index
        tags_tree = self.tags_tree
        if not tags_tree['columns']:
            # dont want to do this more than once
            tags_tree['columns'] = ('class1', 'class2', 'class3',
                                    'magic', 'pointer', 'index_id')
            tags_tree.heading("#0", text='')
            tags_tree.heading("class1", text='class 1')
            tags_tree.heading("class2", text='class 2')
            tags_tree.heading("class3", text='class 3')
            tags_tree.heading("magic",  text='magic')
            tags_tree.heading("pointer", text='pointer')
            tags_tree.heading("index_id",  text='index id')

            tags_tree.column("#0", minwidth=100, width=100)
            tags_tree.column("class1", minwidth=5, width=40, stretch=False)
            tags_tree.column("class2", minwidth=5, width=40, stretch=False)
            tags_tree.column("class3", minwidth=5, width=40, stretch=False)
            tags_tree.column("magic",  minwidth=5, width=70, stretch=False)
            tags_tree.column("pointer", minwidth=5, width=70, stretch=False)
            tags_tree.column("index_id", minwidth=5, width=50, stretch=False)

        if tag_index:
            # remove any currently existing children
            for child in tags_tree.get_children():
                tags_tree.delete(child)

            # generate the hierarchy
            self.generate_subitems()

    def activate_item(self, e=None):
        dir_tree = self.tags_tree
        tag_path = dir_tree.focus()
        if tag_path is None:
            return

    def generate_subitems(self, dir_name='', hierarchy=None):
        tags_tree = self.tags_tree

        if hierarchy is None:
            hierarchy = self.get_hierarchy_map()

        dirs, files = hierarchy
        if dir_name:        
            prefix = dir_name + "\\"

        for subdir_name in sorted(dirs):
            abs_dir_name = dir_name + subdir_name
            if self.tags_tree.exists(abs_dir_name):
                continue

            # add the directory to the treeview
            self.tags_tree.insert(
                dir_name, 'end', iid=abs_dir_name, text=subdir_name)

            # generate the subitems for this directory
            self.generate_subitems(abs_dir_name, dirs[subdir_name])

        map_magic = self.map_magic

        for filename in sorted(files):
            # add the file to the treeview
            b = files[filename]
            if b.indexed:
                pointer = "not in map"
            else:
                pointer = b.meta_offset - map_magic

            self.tags_tree.insert(
                dir_name, 'end', iid=b.id[0], text=filename,
                values=(tag_cls_int_to_fcc.get(b.class_1.data, ''),
                        tag_cls_int_to_fcc.get(b.class_2.data, ''),
                        tag_cls_int_to_fcc.get(b.class_3.data, ''),
                        b.meta_offset, pointer, b.id[0], b))

    def get_hierarchy_map(self):
        # the keys are the names of the directories and files.
        # the values for the files are that tags index block, whereas
        # the values for the directories are a hierarchy of that folder.

        # the keys will always be lowercased to make things less complicated
        dirs = {}
        files = {}

        # loop over each tag in the index and add it to the hierarchy map
        for b in self.tag_index.tag_index:
            tagpath = b.tag.tag_path.replace("/", "\\").lower()
            if is_protected(tagpath):
                tagpath = "protected"
            
            # make sure the tagpath has only valid path characters in it
            self._add_to_hierarchy_map(dirs, files, tagpath.split("\\"), b)

        return dirs, files

    def _add_to_hierarchy_map(self, dirs, files, tagpath, tagblock):
        this_name = tagpath[0]
        if len(tagpath) == 1:
            i = 1
            try:
                ext = "." + tag_cls_int_to_ext[tagblock.class_1.data]
            except Exception:
                ext = ".INVALID"

            this_unique_name = this_name + ext
            # in case certain tags end up having the same name
            while this_unique_name in files:
                this_unique_name = "%s_%s%s" % (this_name, i, ext)
                i += 1

            files[this_unique_name] = tagblock
        else:
            # get the dirs dict for this folder, making one if necessary
            dirs[this_name] = sub_dirs, sub_files = dirs.get(this_name, ({},{}))

            self._add_to_hierarchy_map(sub_dirs, sub_files,
                                       tagpath[1:], tagblock)

    open_selected = close_selected = no_op

    set_root_dir = add_root_dir = insert_root_dir = del_root_dir = no_op

    destroy_subitems = no_op

    get_item_tags_dir = highlight_tags_dir = no_op


if __name__ == "__main__":
    try:
        '''print("This program is still highly experimental and should\n" +
              "not be used except for open sauce tags(since there\n" +
              "is currently no other extractor for those tags).\n\n" +
              "Refinery currently cant extract models, gbxmodels, or\n" +
              "bsps, and certain fields are incorrectly extracted.\n" +
              "If something seems wrong, it might be. Use with care.\n")
        input("Press enter to continue.")'''
        input("Refinery is not ready for public use yet. Ignore it for now.")
        #extractor = run()
        #extractor.mainloop()
    except Exception:
        print(format_exc())
        input()
