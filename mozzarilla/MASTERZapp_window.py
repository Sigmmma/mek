import os
import tkinter as tk
import zipfile

from os.path import dirname, exists, isdir, splitext, realpath
from time import time
from threading import Thread
from traceback import format_exc

from reclaimer.constants import *

# before we do anything, we need to inject these constants so any definitions
# that are built that use them will have them in their descriptor entries.
inject_halo_constants()

from binilla.app_window import *
from reclaimer.hek.handler import HaloHandler
from reclaimer.meta.handler import MapLoader
from reclaimer.os_v3_hek.handler import OsV3HaloHandler
from reclaimer.os_v4_hek.handler import OsV4HaloHandler
from reclaimer.misc.handler import MiscHaloLoader
from reclaimer.stubbs.handler import StubbsHandler
from .config_def import config_def, guerilla_workspace_def
from .widget_picker import *
from .tag_window import HaloTagWindow

default_hotkeys.update({
    '<F1>': "show_dependency_viewer",
    '<F2>': "show_tag_scanner",

    '<F5>': "switch_tags_dir",
    '<F6>': "set_tags_dir",
    '<F7>': "add_tags_dir",
    '<F8>': "remove_tags_dir",
    })

this_curr_dir = os.path.abspath(os.curdir) + PATHDIV

def sanitize_path(path):
    return path.replace('\\', '/').replace('/', PATHDIV)

class Mozzarilla(Binilla):
    app_name = 'Mozzarilla'
    version = '0.9.3.A'
    log_filename = 'mozzarilla.log'
    debug = 0

    _mozzarilla_initialized = False

    styles_dir = dirname(__file__) + s_c.PATHDIV + "styles"
    config_path = dirname(__file__) + '%smozzarilla.cfg' % PATHDIV
    config_def = config_def

    handlers = (
        HaloHandler,
        OsV3HaloHandler,
        OsV4HaloHandler,
        MapLoader,
        MiscHaloLoader,
        StubbsHandler,
        )

    handler_names = (
        "Halo 1",
        "Halo 1 OS v3",
        "Halo 1 OS v4",
        "Halo 1 Map",
        "Halo 1 Misc",
        "Stubbs the Zombie",
        )

    # names of the handlers that MUST load tags from within their tags_dir
    tags_dir_relative = (
        "Halo 1",
        "Halo 1 OS v3",
        "Halo 1 OS v4",
        "Stubbs the Zombie",
        )

    tags_dir = ()

    _curr_handler_index = 0
    _curr_tags_dir_index = 0

    widget_picker = def_halo_widget_picker

    dependency_window = None
    tag_scanner_window = None
    f_and_r_window = None

    window_panes = None
    directory_frame = None
    directory_frame_width = 200

    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', self.debug)

        # gotta give it a default handler or else the
        # config file will fail to be created as updating
        # the config requires using methods in the handler.
        kwargs['handler'] = MiscHaloLoader(debug=self.debug)
        self.tags_dir_relative = set(self.tags_dir_relative)
        self.tags_dirs = [("%stags%s" % (this_curr_dir,  s_c.PATHDIV)).lower()]

        Binilla.__init__(self, *args, **kwargs)

        self.file_menu.insert_command("Exit", label="Load guerilla config",
                                      command=self.load_guerilla_config)
        self.file_menu.insert_separator("Exit")

        self.settings_menu.delete(0, "end")  # clear the menu
        self.settings_menu.add_command(label="Set tags directory",
                                       command=self.set_tags_dir)
        self.settings_menu.add_command(label="Add tags directory",
                                       command=self.add_tags_dir)
        self.settings_menu.add_command(label="Remove tags directory",
                                       command=self.remove_tags_dir)

        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="Edit config", command=self.show_config_file)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="Load style", command=self.apply_style)
        self.settings_menu.add_command(
            label="Save current style", command=self.make_style)

        # make the tools and tag set menus
        self.tools_menu = tk.Menu(self.main_menu, tearoff=0)
        self.defs_menu = tk.Menu(self.main_menu, tearoff=0)

        self.main_menu.add_cascade(label="Tag set", menu=self.defs_menu)
        self.main_menu.add_cascade(label="Tools", menu=self.tools_menu)

        for i in range(len(self.handler_names)):
            self.defs_menu.add_command(command=lambda i=i:
                                       self.select_defs(i, manual=True))

        self.tools_menu.add_command(
            label="Dependency viewer", command=self.show_dependency_viewer)
        self.tools_menu.add_command(
            label="Scan tags directory", command=self.show_tag_scanner)
        self.tools_menu.add_command(
            label="Find and replace", command=self.show_find_and_replace)

        self.defs_menu.add_separator()
        self.handlers = list(self.handlers)
        self.handler_names = list(self.handler_names)

        self.select_defs(manual=False)
        self._mozzarilla_initialized = True

        try:
            if self.config_file.data.header.flags.load_last_workspace:
                self.load_last_workspace()
        except Exception:
            pass

        self.make_window_panes()
        self.make_directory_frame(self.window_panes)
        self.make_io_text(self.window_panes)

        if self.directory_frame is not None:
            self.directory_frame.highlight_tags_dir(self.tags_dir)
        self.update_window_settings()

    def load_last_workspace(self):
        if self._mozzarilla_initialized:
            Binilla.load_last_workspace(self)

    @property
    def tags_dir(self):
        try:
            return self.tags_dirs[self._curr_tags_dir_index]
        except IndexError:
            return None

    @tags_dir.setter
    def tags_dir(self, new_val):
        handler = self.handlers[self._curr_handler_index]
        new_val = sanitize_path(new_val)
        self.tags_dirs[self._curr_tags_dir_index] = handler.tagsdir = new_val

    def load_guerilla_config(self):
        fp = askopenfilename(
            initialdir=self.last_load_dir, title="Select the tag to load",
            filetypes=(('Guerilla config', '*.cfg'), ('All', '*')))

        if not fp:
            return

        self.last_load_dir = dirname(fp)
        workspace = guerilla_workspace_def.build(filepath=fp)

        pad_x = self.io_text.winfo_rootx() - self.winfo_x()
        pad_y = self.io_text.winfo_rooty() - self.winfo_y()

        tl_corner = workspace.data.window_header.top_left_corner
        br_corner = workspace.data.window_header.bottom_right_corner

        self.geometry("%sx%s+%s+%s" % (
            br_corner.x - tl_corner.x - pad_x,
            br_corner.y - tl_corner.y - pad_y,
            tl_corner.x, tl_corner.y))

        for tag in workspace.data.tags:
            if not tag.is_valid_tag:
                continue

            windows = self.load_tags(tag.filepath)
            if not windows:
                continue

            w = windows[0]

            tl_corner = tag.window_header.top_left_corner
            br_corner = tag.window_header.bottom_right_corner

            self.place_window_relative(w, pad_x + tl_corner.x,
                                          pad_y + tl_corner.y)
            w.geometry("%sx%s" % (br_corner.x - tl_corner.x,
                                  br_corner.y - tl_corner.y))

    def load_tags(self, filepaths=None, def_id=None):
        tags_dir = self.tags_dir
        # if there is not tags directory, this can be loaded normally
        if tags_dir is None:
            return Binilla.load_tags(self, filepaths, def_id)

        if isinstance(filepaths, tk.Event):
            filepaths = None
        if filepaths is None:
            filetypes = [('All', '*')]
            defs = self.handler.defs
            for id in sorted(defs.keys()):
                filetypes.append((id, defs[id].ext))
            filepaths = askopenfilenames(initialdir=self.last_load_dir,
                                         filetypes=filetypes,
                                         title="Select the tag to load")
            if not filepaths:
                return

        if isinstance(filepaths, str):
            # account for a stupid bug with certain versions of windows
            if filepaths.startswith('{'):
                filepaths = re.split("\}\W\{", filepaths[1:-1])
            else:
                filepaths = (filepaths, )

        sani = sanitize_path
        handler_name = self.handler_names[self._curr_handler_index]

        sanitized_paths = [sani(path).lower() for path in filepaths]

        # make sure all the chosen tag paths are relative
        # to the current tags directory if they must be
        if handler_name in self.tags_dir_relative:
            for path in sanitized_paths:
                if (not path) or len(path.lower().split(tags_dir.lower())) == 2:
                    continue
    
                print("Specified tag(s) are not located in the tags directory")
                return

        windows = Binilla.load_tags(self, sanitized_paths, def_id)

        if not windows:
            print("You might need to change the tag set to load these tag(s).")
            return ()

        return windows

    def load_tag_as(self, e=None):
        '''Prompts the user for a tag to load and loads it.'''
        if self.def_selector_window:
            return

        filetypes = [('All', '*')]
        defs = self.handler.defs
        for def_id in sorted(defs.keys()):
            filetypes.append((def_id, defs[def_id].ext))
        fp = askopenfilename(initialdir=self.last_load_dir,
                             filetypes=filetypes,
                             title="Select the tag to load")

        if not fp:
            return

        fp = fp.lower()

        self.last_load_dir = dirname(fp)
        dsw = DefSelectorWindow(
            self, title="Which tag is this", action=lambda def_id:
            self.load_tags(filepaths=fp, def_id=def_id))
        self.def_selector_window = dsw
        self.place_window_relative(self.def_selector_window, 30, 50)

    def set_tags_dir(self, e=None, tags_dir=None, manual=True):
        if tags_dir is None:
            tags_dir = askdirectory(initialdir=self.tags_dir,
                                    title="Select the tags directory to add")

        if not tags_dir:
            return

        tags_dir = sanitize_path(tags_dir).lower()
        if tags_dir and not tags_dir.endswith(s_c.PATHDIV):
            tags_dir += s_c.PATHDIV

        if tags_dir in self.tags_dirs:
            print("That tags directory already exists.")
            return

        if self.directory_frame is not None:
            self.directory_frame.set_root_dir(tags_dir)
            self.directory_frame.highlight_tags_dir(self.tags_dir)
        self.tags_dir = tags_dir

        if manual:
            print("Tags directory is currently:\n    %s\n" % self.tags_dir)

    def add_tags_dir(self, e=None, tags_dir=None, manual=True):
        if tags_dir is None:
            tags_dir = askdirectory(initialdir=self.tags_dir,
                                    title="Select the tags directory to add")

        if not tags_dir:
            return

        tags_dir = sanitize_path(tags_dir).lower()
        if tags_dir and not tags_dir.endswith(s_c.PATHDIV):
            tags_dir += s_c.PATHDIV

        if tags_dir in self.tags_dirs:
            if manual:
                print("That tags directory already exists.")
            return

        self.tags_dirs.append(tags_dir)
        self.switch_tags_dir(index=len(self.tags_dirs) - 1, manual=False)

        if self.directory_frame is not None:
            self.directory_frame.add_root_dir(tags_dir)

        if manual:
            self.last_load_dir = tags_dir
            curr_index = self._curr_tags_dir_index
            print("Tags directory is currently:\n    %s\n" % self.tags_dir)

    def remove_tags_dir(self, e=None, index=None, manual=True):
        dirs_count = len(self.tags_dirs)
        # need at least 2 tags dirs to delete one
        if dirs_count < 2:
            return

        if index is None:
            index = self._curr_tags_dir_index

        new_index = self._curr_tags_dir_index
        if index <= new_index:
            new_index = max(0, new_index - 1)

        tags_dir = self.tags_dirs[index]
        del self.tags_dirs[index]
        if self.directory_frame is not None:
            self.directory_frame.del_root_dir(tags_dir)

        self.switch_tags_dir(index=new_index, manual=False)

        if manual:
            print("Tags directory is currently:\n    %s\n" % self.tags_dir)

    def switch_tags_dir(self, e=None, index=None, manual=True):
        if index is None:
            index = (self._curr_tags_dir_index + 1) % len(self.tags_dirs)
        if self._curr_tags_dir_index == index:
            return

        self._curr_tags_dir_index = index
        self.handler.tagsdir = self.tags_dir

        if self.directory_frame is not None:
            self.directory_frame.highlight_tags_dir(self.tags_dir)

        for handler in self.handlers:
            try: handler.tagsdir = self.tags_dir
            except Exception: pass

        if manual:
            self.last_load_dir = self.tags_dir
            print("Tags directory is currently:\n    %s\n" % self.tags_dir)

    def make_tag_window(self, tag, focus=True, window_cls=None):
        if window_cls is None:
            window_cls = HaloTagWindow
        w = Binilla.make_tag_window(self, tag, focus=focus,
                                    window_cls=window_cls)
        self.update_tag_window_title(w)
        return w

    def new_tag(self, e=None):
        if self.def_selector_window:
            return

        dsw = DefSelectorWindow(
            self, title="Select a tag to create", action=lambda def_id:
            self.load_tags(filepaths='', def_id=def_id))
        self.def_selector_window = dsw
        self.place_window_relative(self.def_selector_window, 30, 50)

    def update_tag_window_title(self, window):
        if not hasattr(window, 'tag'):
            return

        tag = window.tag
        if tag is self.config_file:
            window.update_title('%s %s config' % (self.app_name, self.version))
        if not hasattr(tag, 'tags_dir'):
            return

        tags_dir = tag.tags_dir

        if tag is self.config_file or not tags_dir:
            return
        try:
            handler_i = self.handlers.index(window.handler)
            title = "[%s][%s] %s" % (
                self.handler_names[handler_i], tags_dir[:-1], tag.rel_filepath)
        except Exception:
            pass
        window.update_title(title)

    def save_tag(self, tag=None):
        if isinstance(tag, tk.Event):
            tag = None
        if tag is None:
            if self.selected_tag is None:
                return
            tag = self.selected_tag

        if tag is self.config_file:
            return self.save_config()

        # change the tags filepath to be relative to the current tags directory
        if hasattr(tag, "rel_filepath"):
            tag.filepath = tag.tags_dir + tag.rel_filepath

        Binilla.save_tag(self, tag)
        return tag

    def save_tag_as(self, tag=None, filepath=None):
        if isinstance(tag, tk.Event):
            tag = None
        if tag is None:
            if self.selected_tag is None:
                return
            tag = self.selected_tag

        if not hasattr(tag, "serialize"):
            return

        if filepath is None:
            ext = tag.ext
            filepath = asksaveasfilename(
                initialdir=dirname(tag.filepath), defaultextension=ext,
                title="Save tag as...", filetypes=[
                    (ext[1:], "*" + ext), ('All', '*')] )
        else:
            filepath = tag.filepath

        if not filepath:
            return

        # make sure the filepath is sanitized
        filepath = sanitize_path(filepath).lower()
        if len(filepath.split(tag.tags_dir)) != 2:
            print("Cannot save outside the tags directory")
            return

        tag.rel_filepath = filepath.split(tag.tags_dir)[-1]

        Binilla.save_tag_as(self, tag, filepath)

        self.update_tag_window_title(self.get_tag_window_by_tag(tag))
        return tag

    def set_handler(self, handler=None, index=None, name=None):
        if handler is not None:
            handler_index = self.handlers.index(handler)
            self._curr_handler_index = handler_index
            self.handler = handler
        elif index is not None:
            self._curr_handler_index = handler_index
            self.handler = self.handlers[handler_index]
        elif name is not None:
            handler_index = self.handler_names.index(name)
            self._curr_handler_index = handler_index
            self.handler = self.handlers[handler_index]

    def select_defs(self, menu_index=None, manual=True):
        names = self.handler_names
        if menu_index is None:
            menu_index = self._curr_handler_index

        name = names[menu_index]
        handler = self.handlers[menu_index]

        if name == "Halo 1 Map" and manual:
            try:
                debug_mode = self.config_file.data.header.flags.debug_mode
            except Exception:
                debug_mode = True
            if not debug_mode:
                print("Loading and editing maps is not supported yet, " +
                      "but it would be annoying to remove this button, " +
                      "so I put in this message instead!")
                return

        if handler is None or handler is self.handler:
            return

        if manual:
            print("Changing tag set to %s" % name)
            self.io_text.update_idletasks()

        if isinstance(handler, type):
            self.handlers[menu_index] = handler(debug=self.debug)

        self.handler = self.handlers[menu_index]

        entryconfig = self.defs_menu.entryconfig
        for i in range(len(names)):
            entryconfig(i, label=names[i])

        entryconfig(menu_index, label=("%s %s" % (name, u'\u2713')))
        if manual:
            print("    Finished")

        self._curr_handler_index = menu_index

        self.config_file.data.mozzarilla.selected_handler.data = menu_index

    def make_io_text(self, master=None):
        if not self._initialized:
            return
        if master is None:
            master = self.root_frame
        Binilla.make_io_text(self, master)

    def make_directory_frame(self, master=None):
        if not self._initialized:
            return
        if master is None:
            master = self.root_frame
        self.directory_frame = DirectoryFrame(self)
        self.directory_frame.pack(expand=True, fill='both')

    def make_window_panes(self):
        self.window_panes = tk.PanedWindow(
            self.root_frame, sashrelief='raised', sashwidth=8,
            bd=self.frame_depth, bg=self.frame_bg_color)
        self.window_panes.pack(anchor='nw', fill='both', expand=True)

    def make_config(self, filepath=None):
        if filepath is None:
            filepath = self.config_path

        # create the config file from scratch
        self.config_file = self.config_def.build()
        self.config_file.filepath = filepath

        data = self.config_file.data

        # make sure these have as many entries as they're supposed to
        for block in (data.directory_paths, data.widgets.depths, data.colors):
            block.extend(len(block.NAME_MAP))

        tags_dirs = data.mozzarilla.tags_dirs
        for tags_dir in self.tags_dirs:
            tags_dirs.append()
            tags_dirs[-1].path = tags_dir

        self.update_config()

        c_hotkeys = data.hotkeys
        c_tag_window_hotkeys = data.tag_window_hotkeys

        for k_set, b in ((default_hotkeys, c_hotkeys),
                         (default_tag_window_hotkeys, c_tag_window_hotkeys)):
            default_keys = k_set
            hotkeys = b
            for combo, method in k_set.items():
                hotkeys.append()
                keys = hotkeys[-1].combo

                modifier, key = read_hotkey_string(combo)
                keys.modifier.set_to(modifier)
                keys.key.set_to(key)

                hotkeys[-1].method.set_to(method)

    def apply_config(self, e=None):
        Binilla.apply_config(self)
        config_data = self.config_file.data
        mozz = config_data.mozzarilla
        self._curr_handler_index = mozz.selected_handler.data
        tags_dirs = mozz.tags_dirs

        try:
            self.select_defs()
        except Exception:
            pass

        for i in range(len(self.tags_dirs)):
            self.remove_tags_dir(i, manual=False)

        
        self._curr_tags_dir_index = 0
        for tags_dir in tags_dirs:
            self.add_tags_dir(tags_dir=tags_dir.path, manual=False)
        self.switch_tags_dir(
            index=min(mozz.last_tags_dir, len(self.tags_dirs)), manual=False)

        if not self.tags_dir:
            self.tags_dir = (
                self.curr_dir + "%stags%s" % (s_c.PATHDIV,  s_c.PATHDIV))

        for handler in self.handlers:
            try: handler.tagsdir = self.tags_dir
            except Exception: pass

    def update_config(self, config_file=None):
        if config_file is None:
            config_file = self.config_file
        Binilla.update_config(self, config_file)

        config_data = config_file.data
        mozz = config_data.mozzarilla
        tags_dirs = mozz.tags_dirs

        mozz.selected_handler.data = self._curr_handler_index
        mozz.last_tags_dir = self._curr_tags_dir_index

        sani = self.handler.sanitize_path
        del tags_dirs[:]
        for tags_dir in self.tags_dirs:
            tags_dirs.append()
            tags_dirs[-1].path = sani(tags_dir)

    def show_dependency_viewer(self, e=None):
        if self.dependency_window is not None:
            try: self.dependency_window.destroy()
            except Exception: pass
            return

        if not hasattr(self.handler, 'tag_ref_cache'):
            print("Change the current tag set.")
            return

        self.dependency_window = DependencyWindow(self)
        self.place_window_relative(self.dependency_window, 30, 50)
        self.dependency_window.focus_set()

    def show_tag_scanner(self, e=None):
        if self.tag_scanner_window is not None:
            try: self.tag_scanner_window.destroy()
            except Exception: pass
            return

        if not hasattr(self.handler, 'tag_ref_cache'):
            print("Change the current tag set.")
            return

        self.tag_scanner_window = TagScannerWindow(self)
        self.place_window_relative(self.tag_scanner_window, 30, 50)
        self.tag_scanner_window.focus_set()

    def show_find_and_replace(self, e=None):
        if self.f_and_r_window is not None:
            try: self.f_and_r_window.destroy()
            except Exception: pass
            return

        self.f_and_r_window = FindAndReplaceWindow(self)
        self.place_window_relative(self.f_and_r_window, 30, 50)
        self.f_and_r_window.focus_set()

    def update_window_settings(self):
        if not self._initialized:
            return

        Binilla.update_window_settings(self)
        try:
            for m in (self.defs_menu, self.tools_menu):
                m.config(bg=self.default_bg_color, fg=self.text_normal_color)

            self.window_panes.config(
                bg=self.frame_bg_color, bd=self.frame_depth)
            self.directory_frame.apply_style()
            if self.dependency_window is not None:
                self.dependency_window.apply_style()
            if self.tag_scanner_window is not None:
                self.tag_scanner_window.apply_style()

            try:
                flags = self.config_file.data.mozzarilla.flags
                self.window_panes.forget(self.directory_frame)
                self.window_panes.forget(self.io_frame)

                if flags.show_hierarchy_window:
                    self.directory_frame.pack(fill='both', expand=True)
                    self.window_panes.add(self.directory_frame)
                if flags.show_console_window:
                    self.io_frame.pack(fill='both', expand=True)
                    self.window_panes.add(self.io_frame)
            except Exception:
                print(format_exc())
        except AttributeError: print(format_exc())
        except Exception: print(format_exc())

class DependencyWindow(tk.Toplevel, BinillaWidget):

    app_root = None
    handler = None

    zipping = False
    stop_zipping = False

    def __init__(self, app_root, *args, **kwargs): 
        self.handler = app_root.handler
        self.app_root = app_root
        kwargs.update(width=400, height=500, bd=0,
                      highlightthickness=0, bg=self.default_bg_color)
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)

        tagset = app_root.handler_names[app_root._curr_handler_index]
        self.title("[%s] Tag dependency viewer" % tagset)
        self.minsize(width=400, height=100)

        # make the tkinter variables
        self.tag_filepath = tk.StringVar(self)

        # make the frames
        self.filepath_frame = tk.LabelFrame(
            self, text="Select a tag",
            fg=self.text_normal_color, bg=self.default_bg_color)
        self.button_frame = tk.LabelFrame(
            self, text="Actions",
            fg=self.text_normal_color, bg=self.default_bg_color)

        btn_kwargs = dict(
            bg=self.button_color, activebackground=self.button_color,
            fg=self.text_normal_color, bd=self.button_depth,
            disabledforeground=self.text_disabled_color,
            )
        self.display_button = tk.Button(
            self.button_frame, width=25, text='Show dependencies',
            command=self.populate_dependency_tree, **btn_kwargs)

        self.zip_button = tk.Button(
            self.button_frame, width=25, text='Zip tag recursively',
            command=self.recursive_zip, **btn_kwargs)

        self.dependency_window = DependencyFrame(self, app_root=self.app_root)

        self.filepath_entry = tk.Entry(
            self.filepath_frame, textvariable=self.tag_filepath,
            bd=self.entry_depth,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            disabledbackground=self.entry_disabled_color,
            disabledforeground=self.text_disabled_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color)
        self.browse_button = tk.Button(
            self.filepath_frame, text="Browse",
            command=self.browse, **btn_kwargs)

        self.display_button.pack(padx=4, pady=2, side=tk.LEFT)
        self.zip_button.pack(padx=4, pady=2, side=tk.RIGHT)

        self.filepath_entry.pack(padx=(4, 0), pady=2, side=tk.LEFT,
                                 expand=True, fill='x')
        self.browse_button.pack(padx=(0, 4), pady=2, side=tk.LEFT)

        self.filepath_frame.pack(fill='x', padx=1)
        self.button_frame.pack(fill='x', padx=1)
        self.dependency_window.pack(fill='both', padx=1, expand=True)

        self.transient(app_root)
        self.apply_style()

    def apply_style(self):
        self.config(bg=self.default_bg_color)
        for w in (self.filepath_frame, self.button_frame):
            w.config(fg=self.text_normal_color, bg=self.default_bg_color)

        for w in (self.display_button, self.zip_button, self.browse_button):
            w.config(bg=self.button_color, activebackground=self.button_color,
                     fg=self.text_normal_color, bd=self.button_depth,
                     disabledforeground=self.text_disabled_color)

        self.filepath_entry.config(
            bd=self.entry_depth,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            disabledbackground=self.entry_disabled_color,
            disabledforeground=self.text_disabled_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color)
        
        self.dependency_window.apply_style()

    def browse(self):
        filetypes = [('All', '*')]

        defs = self.app_root.handler.defs
        for def_id in sorted(defs.keys()):
            filetypes.append((def_id, defs[def_id].ext))
        fp = askopenfilename(initialdir=self.app_root.last_load_dir,
                             filetypes=filetypes, title="Select a tag")

        if not fp:
            return

        fp = sanitize_path(fp).lower()
        self.app_root.last_load_dir = dirname(fp)

        self.filepath_entry.delete(0, tk.END)
        self.filepath_entry.insert(0, fp)

    def destroy(self):
        try:
            self.app_root.dependency_window = None
        except AttributeError:
            pass
        self.stop_zipping = True
        tk.Toplevel.destroy(self)

    def get_tag(self, filepath):
        handler = self.handler
        def_id = handler.get_def_id(filepath)

        tag = handler.tags.get(def_id, {}).get(handler.sanitize_path(filepath))
        if tag is not None:
            return tag
        try:
            return handler.build_tag(filepath=filepath)
        except Exception:
            pass

    def get_dependencies(self, tag):
        handler = self.handler
        def_id = tag.def_id
        dependency_cache = handler.tag_ref_cache.get(def_id)

        if not dependency_cache:
            return ()

        nodes = handler.get_nodes_by_paths(handler.tag_ref_cache[def_id],
                                           tag.data)

        dependencies = []

        for node in nodes:
            # if the node's filepath is empty, just skip it
            if not node.filepath:
                continue
            try:
                ext = '.' + node.tag_class.enum_name
            except Exception:
                ext = ''
            dependencies.append(node.filepath + ext)
        return dependencies

    def populate_dependency_tree(self):
        filepath = self.tag_filepath.get()
        if not filepath:
            return

        app = self.app_root
        handler = self.handler = app.handler
        sani = sanitize_path

        handler_name = app.handler_names[app._curr_handler_index]
        if handler_name not in app.tags_dir_relative:
            print("Change the current tag set.")
            return
        else:
            tags_dir = handler.tagsdir.lower()

        filepath = sani(filepath.lower())
        if len(filepath.split(tags_dir)) != 2:
            print("Specified tag is not located within the tags directory")
            return

        tag = self.get_tag(filepath)
        if tag is None:
            print("Could not load tag:\n    %s" % filepath)
            return

        self.dependency_window.handler = handler
        self.dependency_window.tags_dir = tags_dir
        self.dependency_window.root_tag_path = tag.filepath

        self.dependency_window.reload()

    def recursive_zip(self):
        if self.zipping:
            return
        try: self.zip_thread.join()
        except Exception: pass
        self.zip_thread = Thread(target=self._recursive_zip)
        self.zip_thread.daemon = True
        self.zip_thread.start()

    def _recursive_zip(self):
        self.zipping = True
        try:
            self.do_recursive_zip()
        except Exception:
            print(format_exc())
        self.zipping = False

    def do_recursive_zip(self):
        tag_path = self.tag_filepath.get().lower()
        if not tag_path:
            return

        app = self.app_root
        handler = self.handler = app.handler
        sani = sanitize_path

        handler_name = app.handler_names[app._curr_handler_index]
        if handler_name not in app.tags_dir_relative:
            print("Change the current tag set.")
            return
        else:
            tags_dir = handler.tagsdir.lower()

        tag_path = sani(tag_path)
        if len(tag_path.split(tags_dir)) != 2:
            print("Specified tag is not located within the tags directory")
            return

        self.app_root.update()
        self.app_root.update_idletasks()
        tagzip_path = asksaveasfilename(
            initialdir=self.app_root.last_load_dir, title="Save zipfile to...",
            filetypes=(("zipfile", "*.zip"), ))

        if not tagzip_path:
            return

        tag = self.get_tag(tag_path)
        if tag is None:
            print("Could not load tag:\n    %s" % tag_path)
            return
        self.app_root.update()
        self.app_root.update_idletasks()

        # make the zipfile to put everything in
        tagzip_path = splitext(tagzip_path)[0] + ".zip"

        tags_to_zip = [tag_path.split(tags_dir)[-1]]
        new_tags_to_zip = []
        seen_tags = set()
        self.app_root.update()
        self.app_root.update_idletasks()

        with zipfile.ZipFile(tagzip_path, mode='w') as tagzip:
            # loop over all the tags and add them to the zipfile
            while tags_to_zip:
                for rel_tag_path in tags_to_zip:
                    tag_path = tags_dir + rel_tag_path
                    if self.stop_zipping:
                        print('Recursive zip operation cancelled.\n')
                        return
                        self.app_root.update()
                        self.app_root.update_idletasks()

                    if rel_tag_path in seen_tags:
                        continue
                    seen_tags.add(rel_tag_path)

                    try:
                        print("Adding '%s' to zipfile" % rel_tag_path)
                        self.app_root.update()
                        self.app_root.update_idletasks()
                        tag = self.get_tag(tag_path)
                        new_tags_to_zip.extend(self.get_dependencies(tag))
                        self.app_root.update()
                        self.app_root.update_idletasks()

                        # try to conserve memory a bit
                        del tag

                        tagzip.write(tag_path, arcname=rel_tag_path)
                        self.app_root.update()
                        self.app_root.update_idletasks()
                    except Exception:
                        print("    Could not add '%s' to zipfile." %
                              rel_tag_path)
                self.app_root.update()
                self.app_root.update_idletasks()

                # replace the tags to zip with the newly collected ones
                tags_to_zip[:] = new_tags_to_zip
                del new_tags_to_zip[:]
                self.app_root.update()
                self.app_root.update_idletasks()

        print("\nRecursive zip completed.\n")


class TagScannerWindow(tk.Toplevel, BinillaWidget):

    app_root = None
    handler = None

    scanning = False
    stop_scanning = False
    print_interval = 5

    listbox_index_to_def_id = ()

    def __init__(self, app_root, *args, **kwargs): 
        self.handler = handler = app_root.handler
        self.app_root = app_root
        kwargs.update(bd=0, highlightthickness=0, bg=self.default_bg_color)
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)

        ext_id_map = handler.ext_id_map
        self.listbox_index_to_def_id = [
            ext_id_map[ext] for ext in sorted(ext_id_map.keys())
            if ext_id_map[ext] in handler.tag_ref_cache]

        tagset = app_root.handler_names[app_root._curr_handler_index]

        self.title("[%s] Tag directory scanner" % tagset)
        self.minsize(width=400, height=250)
        self.resizable(0, 0)

        # make the tkinter variables
        self.directory_path = tk.StringVar(self)
        self.logfile_path = tk.StringVar(self)

        # make the frames
        self.directory_frame = tk.LabelFrame(
            self, text="Directory to scan",
            fg=self.text_normal_color, bg=self.default_bg_color)
        self.logfile_frame = tk.LabelFrame(
            self, text="Output log filepath",
            fg=self.text_normal_color, bg=self.default_bg_color)
        self.def_ids_frame = tk.LabelFrame(
            self, text="Select which tag types to scan",
            fg=self.text_normal_color, bg=self.default_bg_color)
        self.button_frame = tk.Frame(
            self.def_ids_frame,bg=self.default_bg_color)

        btn_kwargs = dict(
            bg=self.button_color, activebackground=self.button_color,
            fg=self.text_normal_color, bd=self.button_depth,
            disabledforeground=self.text_disabled_color,
            )

        self.scan_button = tk.Button(
            self.button_frame, text='Scan directory', width=20,
            command=self.scan_directory, **btn_kwargs)
        self.cancel_button = tk.Button(
            self.button_frame, text='Cancel scan', width=20,
            command=self.cancel_scan, **btn_kwargs)
        self.select_all_button = tk.Button(
            self.button_frame, text='Select all', width=20,
            command=self.select_all, **btn_kwargs)
        self.deselect_all_button = tk.Button(
            self.button_frame, text='Deselect all', width=20,
            command=self.deselect_all, **btn_kwargs)

        self.directory_entry = tk.Entry(
            self.directory_frame, textvariable=self.directory_path,
            bd=self.entry_depth,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            disabledbackground=self.entry_disabled_color,
            disabledforeground=self.text_disabled_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color)
        self.dir_browse_button = tk.Button(
            self.directory_frame, text="Browse",
            command=self.dir_browse, **btn_kwargs)

        self.logfile_entry = tk.Entry(
            self.logfile_frame, textvariable=self.logfile_path,
            bd=self.entry_depth,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            disabledbackground=self.entry_disabled_color,
            disabledforeground=self.text_disabled_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color)
        self.log_browse_button = tk.Button(
            self.logfile_frame, text="Browse",
            command=self.log_browse, **btn_kwargs)

        self.def_ids_scrollbar = tk.Scrollbar(
            self.def_ids_frame, orient="vertical")
        self.def_ids_listbox = tk.Listbox(
            self.def_ids_frame, selectmode=tk.MULTIPLE, highlightthickness=0,
            bg=self.enum_normal_color, fg=self.text_normal_color,
            selectbackground=self.enum_highlighted_color,
            selectforeground=self.text_highlighted_color,
            yscrollcommand=self.def_ids_scrollbar.set)
        self.def_ids_scrollbar.config(command=self.def_ids_listbox.yview)

        for def_id in self.listbox_index_to_def_id:
            tag_ext = handler.id_ext_map[def_id].split('.')[-1]
            self.def_ids_listbox.insert(tk.END, tag_ext)

            # these tag types are massive, so by
            # default dont set them to be scanned
            if def_id in ("sbsp", "scnr"):
                continue
            self.def_ids_listbox.select_set(tk.END)

        for w in (self.directory_entry, self.logfile_entry):
            w.pack(padx=(4, 0), pady=2, side=tk.LEFT, expand=True, fill='x')

        for w in (self.dir_browse_button, self.log_browse_button):
            w.pack(padx=(0, 4), pady=2, side=tk.LEFT)

        for w in (self.scan_button, self.cancel_button):
            w.pack(padx=4, pady=2)

        for w in (self.deselect_all_button, self.select_all_button):
            w.pack(padx=4, pady=2, side=tk.BOTTOM)

        self.def_ids_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        self.def_ids_scrollbar.pack(side=tk.LEFT, fill="y")
        self.button_frame.pack(side=tk.LEFT, fill="y")

        self.directory_frame.pack(fill='x', padx=1)
        self.logfile_frame.pack(fill='x', padx=1)
        self.def_ids_frame.pack(fill='x', padx=1, expand=True)

        self.transient(app_root)

        self.directory_entry.insert(0, handler.tagsdir)
        self.logfile_entry.insert(0, this_curr_dir + "tag_scanner.log")
        self.apply_style()

    def apply_style(self):
        self.config(bg=self.default_bg_color)        
        for w in(self.directory_frame, self.logfile_frame, self.def_ids_frame):
            w.config(fg=self.text_normal_color, bg=self.default_bg_color)

        self.button_frame.config(bg=self.default_bg_color)

        for w in (self.scan_button, self.cancel_button,
                  self.select_all_button, self.deselect_all_button,
                  self.dir_browse_button, self.log_browse_button):
            w.config(bg=self.button_color, activebackground=self.button_color,
                     fg=self.text_normal_color, bd=self.button_depth,
                     disabledforeground=self.text_disabled_color)

        for w in (self.directory_entry, self.logfile_entry):
            w.config(bd=self.entry_depth,
                bg=self.entry_normal_color, fg=self.text_normal_color,
                disabledbackground=self.entry_disabled_color,
                disabledforeground=self.text_disabled_color,
                selectbackground=self.entry_highlighted_color,
                selectforeground=self.text_highlighted_color)
        self.def_ids_listbox.config(
            bg=self.enum_normal_color, fg=self.text_normal_color,
            selectbackground=self.enum_highlighted_color,
            selectforeground=self.text_highlighted_color)

    def deselect_all(self):
        self.def_ids_listbox.select_clear(0, tk.END)

    def select_all(self):
        for i in range(len(self.listbox_index_to_def_id)):
            self.def_ids_listbox.select_set(i)

    def get_tag(self, filepath):
        handler = self.handler
        def_id = handler.get_def_id(filepath)

        tag = handler.tags.get(def_id, {}).get(handler.sanitize_path(filepath))
        if tag is not None:
            return tag
        try:
            return handler.build_tag(filepath=filepath)
        except Exception:
            pass

    def dir_browse(self):
        dirpath = askdirectory(
            initialdir=self.directory_path.get(),
            title="Select directory to scan")

        if not dirpath:
            return

        dirpath = sanitize_path(dirpath).lower()
        if not dirpath.endswith(PATHDIV):
            dirpath += PATHDIV

        self.app_root.last_load_dir = dirname(dirpath)
        if len(dirpath.split(self.handler.tagsdir)) != 2:
            print("Chosen directory is not located within the tags directory")
            return

        self.directory_entry.delete(0, tk.END)
        self.directory_entry.insert(0, dirpath)

    def log_browse(self):
        filepath = asksaveasfilename(
            initialdir=dirname(self.logfile_entry.get()),
            title="Save scan log to...",
            filetypes=(("tag scanner log", "*.log"), ('All', '*')))

        if not filepath:
            return

        filepath = sanitize_path(filepath)
        self.app_root.last_load_dir = dirname(filepath)

        self.logfile_entry.delete(0, tk.END)
        self.logfile_entry.insert(0, filepath)

    def destroy(self):
        try:
            self.app_root.tag_scanner_window = None
        except AttributeError:
            pass
        self.stop_scanning = True
        tk.Toplevel.destroy(self)

    def cancel_scan(self):
        self.stop_scanning = True

    def scan_directory(self):
        if self.scanning:
            return
        try: self.scan_thread.join()
        except Exception: pass
        self.scan_thread = Thread(target=self._scan_directory)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        self.update()

    def _scan_directory(self):
        self.scanning = True
        try:
            self.scan()
        except Exception:
            print(format_exc())
        self.scanning = False

    def scan(self):
        app = self.app_root
        handler = self.handler
        sani = sanitize_path
        self.stop_scanning = False

        tagsdir = self.handler.tagsdir.lower()
        dirpath = sani(self.directory_path.get().lower())
        logpath = sani(self.logfile_path.get())

        if len(dirpath.split(tagsdir)) != 2:
            print("Chosen directory is not located within the tags directory")
            return

        #this is the string to store the entire debug log
        log_name = "HEK Tag Scanner log"
        debuglog = "\n%s%s%s\n\n" % (
            "-"*30, log_name, "-" * (50-len(log_name)))
        debuglog += "tags directory = %s\nscan directory = %s\n\n" % (
            tagsdir, dirpath)
        debuglog += "broken dependencies are listed below\n"

        get_nodes = handler.get_nodes_by_paths
        get_tagref_invalid = handler.get_tagref_invalid

        s_time = time()
        c_time = s_time
        p_int = self.print_interval

        all_tag_paths = {self.listbox_index_to_def_id[int(i)]: [] for i in
                         self.def_ids_listbox.curselection()}
        ext_id_map = handler.ext_id_map
        id_ext_map = handler.id_ext_map

        print("Locating tags...")
        try: app.io_text.update()
        except Exception: pass

        for root, directories, files in os.walk(dirpath):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            root = root.split(tagsdir)[-1]

            for filename in files:
                filepath = sani(root + filename)

                if time() - c_time > p_int:
                    c_time = time()
                    print(' '*4 + filepath)
                self.app_root.update()
                self.app_root.update_idletasks()

                if self.stop_scanning:
                    print('Tag scanning operation cancelled.\n')
                    return

                tag_paths = all_tag_paths.get(
                    ext_id_map.get(splitext(filename)[-1].lower()))

                if tag_paths is not None:
                    tag_paths.append(filepath)

        # make the debug string by scanning the tags directory
        for def_id in sorted(all_tag_paths.keys()):
            tag_ref_paths = handler.tag_ref_cache[def_id]

            print("Scanning '%s' tags..." % id_ext_map[def_id][1:])
            self.app_root.update()
            self.app_root.update_idletasks()
            tags_coll = all_tag_paths[def_id]

            # always display the first tag's filepath
            c_time = time() - p_int + 1

            for filepath in sorted(tags_coll):
                if self.stop_scanning:
                    print('Tag scanning operation cancelled.\n')
                    break

                if time() - c_time > p_int:
                    c_time = time()
                    print(' '*4 + filepath)

                self.app_root.update()
                self.app_root.update_idletasks()

                tag = self.get_tag(tagsdir + filepath)
                if tag is None:
                    continue

                try:
                    missed = get_nodes(tag_ref_paths, tag.data,
                                       get_tagref_invalid)
                    self.app_root.update()
                    self.app_root.update_idletasks()

                    if not missed:
                        continue

                    debuglog += "\n\n%s\n" % filepath
                    block_name = None

                    for block in missed:
                        if block.NAME != block_name:
                            debuglog += '%s%s\n' % (' '*4, block.NAME)
                            block_name = block.NAME
                        try:
                            ext = '.' + block.tag_class.enum_name
                        except Exception:
                            ext = ''
                        debuglog += '%s%s\n' % (' '*8, block.STEPTREE + ext)
                        self.app_root.update()
                        self.app_root.update_idletasks()

                except Exception:
                    print("    Could not scan '%s'" % tag.filepath)
                    try: app.io_text.update()
                    except Exception: pass
                    continue

            if self.stop_scanning:
                break

        print("\nScanning took %s seconds." % int(time() - s_time))
        print("Writing logfile to %s..." % logpath)
        self.app_root.update()
        self.app_root.update_idletasks()

        # make and write to the logfile
        try:
            handler.make_log_file(debuglog, logpath)
            print("Scan completed.\n")
            return
        except Exception:
            pass

        print("Could not create log. Printing log to console instead.\n\n")
        self.app_root.update()
        self.app_root.update_idletasks()
        for line in debuglog.split('\n'):
            try:
                print(line)
            except Exception:
                print("<COULD NOT PRINT THIS LINE>")
            self.app_root.update()
            self.app_root.update_idletasks()

        print("Scan completed.\n")


class FindAndReplaceWindow(tk.Toplevel):

    def __init__(self, app_root, *args, **kwargs):
        self.app_root = app_root
        kwargs.update(width=400, height=100, bd=0, highlightthickness=0)
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)

        self.title("Find and replace")
        self.minsize(width=400, height=50)
        self.resizable(1, 0)

        # make the tkinter variables
        self.find_var = tk.StringVar(self)
        self.replace_var = tk.StringVar(self)

        # make the frames
        self.find_frame = tk.LabelFrame(self, text="Find this")
        self.replace_frame = tk.LabelFrame(self, text="Replace with this")

        self.replace_button = tk.Button(
            self, text='Replace', width=20, command=self.replace)

        self.find_entry = tk.Entry(
            self.find_frame, textvariable=self.find_var)
        self.replace_entry = tk.Entry(
            self.replace_frame, textvariable=self.replace_var)

        self.find_frame.pack(fill="x", expand=True)
        self.find_entry.pack(fill="x", expand=True)
        self.replace_frame.pack(fill="x", expand=True)
        self.replace_entry.pack(fill="x", expand=True)
        self.replace_button.pack(fill="x", anchor='center')

        self.transient(app_root)


    def replace(self, e=None):
        app_root = self.app_root
        try:
            window = app_root.get_tag_window_by_tag(app_root.selected_tag)
        except Exception:
            window = None

        if window is None:
            return

        find = self.find_var.get()
        replace = self.replace_var.get()

        f_widgets = window.field_widget.f_widgets.values()
        nodes = window.tag.data
        occurances = 0

        while f_widgets:
            new_f_widgets = []
            for w in f_widgets:
                if hasattr(w, 'entry_string'):
                    e_str = w.entry_string
                    if find == e_str.get():
                        e_str.set(replace)

                try: new_f_widgets.extend(w.f_widgets.values())
                except Exception: pass

            f_widgets = new_f_widgets

        while nodes:
            new_nodes = []
            for node in nodes:
                if not isinstance(node, list):
                    continue

                attrs = range(len(node))
                if hasattr(node, 'STEPTREE'):
                    attrs = tuple(attrs) + ('STEPTREE',)
                for i in attrs:
                    val = node[i]
                    if not isinstance(val, str):
                        continue

                    if find == val:
                        node[i] = replace
                        occurances += 1

                try:
                    if isinstance(node, list):
                        new_nodes.extend(node)
                    if hasattr(node, 'STEPTREE'):
                        new_nodes.append(node.STEPTREE)
                except Exception:
                    pass

            nodes = new_nodes

        print('Found and replaced %s occurances' % occurances)


class DirectoryFrame(BinillaWidget, tk.Frame):
    app_root = None

    def __init__(self, master, *args, **kwargs):
        kwargs.setdefault('app_root', master)
        self.app_root = kwargs.pop('app_root')

        kwargs.update(bd=0, highlightthickness=0, bg=self.default_bg_color)
        tk.Frame.__init__(self, master, *args, **kwargs)

        #self.controls_frame = tk.Frame(self, highlightthickness=0, height=100)
        self.hierarchy_frame = HierarchyFrame(self, app_root=self.app_root)

        #self.controls_frame.pack(fill='both')
        self.hierarchy_frame.pack(fill='both', expand=True)
        self.apply_style()

    def set_root_dir(self, root_dir):
        self.hierarchy_frame.set_root_dir(root_dir)

    def add_root_dir(self, root_dir):
        self.hierarchy_frame.add_root_dir(root_dir)

    def del_root_dir(self, root_dir):
        self.hierarchy_frame.del_root_dir(root_dir)

    def highlight_tags_dir(self, root_dir):
        self.hierarchy_frame.highlight_tags_dir(root_dir)

    def apply_style(self):
        #self.controls_frame.config(bg=self.default_bg_color)
        self.hierarchy_frame.apply_style()


class HierarchyFrame(BinillaWidget, tk.Frame):
    tags_dir = ''
    app_root = None
    tags_dir_items = ()

    def __init__(self, master, *args, **kwargs):
        kwargs.update(bg=self.default_bg_color, bd=self.listbox_depth,
            relief='sunken', highlightthickness=0)
        kwargs.setdefault('app_root', master)
        self.app_root = kwargs.pop('app_root')
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.tags_dir = self.app_root.tags_dir
        self.tag_dirs_frame = tk.Frame(self, highlightthickness=0)

        self.tag_dirs_tree = tk.ttk.Treeview(
            self.tag_dirs_frame, selectmode='browse', padding=(0, 0))
        self.scrollbar_y = tk.Scrollbar(
            self.tag_dirs_frame, orient='vertical',
            command=self.tag_dirs_tree.yview)
        self.tag_dirs_tree.config(yscrollcommand=self.scrollbar_y.set)

        self.tag_dirs_tree.bind('<<TreeviewOpen>>', self.open_selected)
        self.tag_dirs_tree.bind('<<TreeviewClose>>', self.close_selected)
        self.tag_dirs_tree.bind('<Double-Button-1>', self.activate_item)
        self.tag_dirs_tree.bind('<Return>', self.activate_item)

        self.tag_dirs_frame.pack(fill='both', side='left', expand=True)

        self.tag_dirs_tree.pack(side='left', fill='both', expand=True)
        self.scrollbar_y.pack(side='right', fill='y')

        self.reload()
        self.apply_style()

    def apply_style(self):
        self.tag_dirs_frame.config(bg=self.default_bg_color)

        dir_tree = self.tag_dirs_tree
        dir_tree.tag_configure(
            'item', background=self.entry_normal_color,
            foreground=self.text_normal_color)
        self.highlight_tags_dir()

    def reload(self):
        dir_tree = self.tag_dirs_tree
        dir_tree['columns'] = ('size', )
        dir_tree.heading("#0", text='path')
        dir_tree.heading("size", text='filesize')
        dir_tree.column("#0", minwidth=100, width=100)
        dir_tree.column("size", minwidth=100, width=100, stretch=False)

        for tags_dir in self.tags_dir_items:
            dir_tree.delete(tags_dir)

        self.tags_dir_items = []

        for tags_dir in self.app_root.tags_dirs:
            self.add_root_dir(tags_dir)

    def set_root_dir(self, root_dir):
        dir_tree = self.tag_dirs_tree
        curr_root_dir = self.app_root.tags_dir

        tags_dir_index = dir_tree.index(curr_root_dir)
        dir_tree.delete(curr_root_dir)
        self.insert_root_dir(root_dir)

    def add_root_dir(self, root_dir):
        self.insert_root_dir(root_dir)

    def insert_root_dir(self, root_dir, index='end'):
        iid = self.tag_dirs_tree.insert(
            '', index, iid=root_dir, text=root_dir[:-1],
            tags=(root_dir, 'tagdir'))
        self.tags_dir_items.append(iid)
        self.destroy_subitems(iid)

    def del_root_dir(self, root_dir):
        self.tag_dirs_tree.delete(root_dir)

    def destroy_subitems(self, directory):
        '''
        Destroys all the given items subitems and creates an empty
        subitem so as to give the item the appearance of being expandable.
        '''
        dir_tree = self.tag_dirs_tree

        for child in dir_tree.get_children(directory):
            dir_tree.delete(child)

        # add an empty node to make an "expand" button appear
        dir_tree.insert(directory, 'end')

    def generate_subitems(self, directory):
        dir_tree = self.tag_dirs_tree

        for root, subdirs, files in os.walk(directory):
            for subdir in sorted(subdirs):
                folderpath = directory + subdir + PATHDIV
                dir_tree.insert(
                    directory, 'end', text=subdir,
                    iid=folderpath, tags=('item',))

                # loop over each of the new items, give them
                # at least one item so they can be expanded.
                self.destroy_subitems(folderpath)
            for file in sorted(files):
                try:
                    filesize = os.stat(directory + file).st_size
                    if filesize < 1024:
                        filesize = str(filesize) + " bytes"
                    elif filesize < 1024**2:
                        filesize = str(round(filesize/1024, 3)) + " Kb"
                    else:
                        filesize = str(round(filesize/(1024**2), 3)) + " Mb"
                except Exception:
                    filesize = 'COULDNT CALCULATE'
                dir_tree.insert(directory, 'end', text=file,
                                iid=directory + file, tags=('item',),
                values=(filesize, ))

            # just do the toplevel of the hierarchy
            break

    def get_item_tags_dir(self, iid):
        '''Returns the tags directory of the given item'''
        dir_tree = self.tag_dirs_tree
        prev_parent = iid
        parent = dir_tree.parent(prev_parent)
        
        while parent:
            prev_parent = parent
            parent = dir_tree.parent(prev_parent)

        return prev_parent

    def open_selected(self, e=None):
        dir_tree = self.tag_dirs_tree
        tag_path = dir_tree.focus()
        for child in dir_tree.get_children(tag_path):
            dir_tree.delete(child)

        if tag_path:
            self.generate_subitems(tag_path)

    def close_selected(self, e=None):
        dir_tree = self.tag_dirs_tree
        tag_path = dir_tree.focus()
        if tag_path is None:
            return

        if isdir(tag_path):
            self.destroy_subitems(tag_path)

    def highlight_tags_dir(self, tags_dir=None):
        app = self.app_root
        dir_tree = self.tag_dirs_tree
        if tags_dir is None:
              tags_dir = self.app_root.tags_dir
        for td in app.tags_dirs:
            if td == tags_dir:
                dir_tree.tag_configure(
                    td, background=self.entry_highlighted_color,
                    foreground=self.text_highlighted_color)
            else:
                dir_tree.tag_configure(
                    td, background=self.entry_normal_color,
                    foreground=self.text_normal_color)

    def activate_item(self, e=None):
        dir_tree = self.tag_dirs_tree
        tag_path = dir_tree.focus()
        if tag_path is None:
            return

        try:
            app = self.app_root
            tags_dir = self.get_item_tags_dir(tag_path)
            self.highlight_tags_dir(tags_dir)
            app.switch_tags_dir(index=app.tags_dirs.index(tags_dir))
        except Exception:
            print(format_exc())

        if isdir(tag_path):
            return

        try:
            app.load_tags(filepaths=tag_path)
        except Exception:
            print(format_exc())


class DependencyFrame(HierarchyFrame):
    root_tag_path = ''
    _initialized = False
    handler = None

    def __init__(self, master, *args, **kwargs):
        HierarchyFrame.__init__(self, master, *args, **kwargs)
        self.handler = self.app_root.handler
        self._initialized = True

    def apply_style(self):
        HierarchyFrame.apply_style(self)
        self.tag_dirs_tree.tag_configure(
            'badref', foreground=self.invalid_path_color,
            background=self.entry_normal_color)

    def get_item_tags_dir(*args, **kwargs): pass

    def highlight_tags_dir(*args, **kwargs): pass

    def reload(self):
        dir_tree = self.tag_dirs_tree
        dir_tree["columns"]=("dependency")
        dir_tree.heading("#0", text='Filepath')
        dir_tree.heading("dependency", text='Dependency path')

        if not self._initialized:
            return

        for item in dir_tree.get_children():
            try: dir_tree.delete(item)
            except Exception: pass

        root = self.root_tag_path

        iid = self.tag_dirs_tree.insert(
            '', 'end', iid=self.root_tag_path, text=root,
            tags=(root, 'item'), values=('', root))
        self.destroy_subitems(iid)

    def get_dependencies(self, tag_path):
        tag = self.master.get_tag(tag_path)
        handler = self.handler
        d_id = tag.def_id
        dependency_cache = handler.tag_ref_cache.get(d_id)

        if not dependency_cache:
            return ()

        dependencies = []

        for block in handler.get_nodes_by_paths(dependency_cache, tag.data):
            # if the node's filepath is empty, just skip it
            if not block.filepath:
                continue
            dependencies.append(block)
        return dependencies

    def destroy_subitems(self, iid):
        '''
        Destroys all the given items subitems and creates an empty
        subitem so as to give the item the appearance of being expandable.
        '''
        dir_tree = self.tag_dirs_tree

        for child in dir_tree.get_children(iid):
            dir_tree.delete(child)

        # add an empty node to make an "expand" button appear
        tag_path = dir_tree.item(iid)['values'][-1]
        if not exists(tag_path):
            dir_tree.item(iid, tags=('badref', ))
        elif self.get_dependencies(tag_path):
            dir_tree.insert(iid, 'end')

    def close_selected(self, e=None):
        dir_tree = self.tag_dirs_tree
        iid = dir_tree.focus()
        if iid:
            self.destroy_subitems(iid)

    def generate_subitems(self, parent_iid):
        tags_dir = self.tags_dir
        dir_tree = self.tag_dirs_tree
        parent_tag_path = dir_tree.item(parent_iid)['values'][-1]

        if not exists(parent_tag_path):
            return

        for tag_ref_block in self.get_dependencies(parent_tag_path):
            try:
                ext = '.' + tag_ref_block.tag_class.enum_name
            except Exception:
                ext = ''
            tag_path = tag_ref_block.filepath + ext

            dependency_name = tag_ref_block.NAME
            last_block = tag_ref_block
            parent = last_block.parent
            while parent is not None and hasattr(parent, 'NAME'):
                name = parent.NAME
                f_type = parent.TYPE
                if f_type.is_array:
                    index = parent.index(last_block)
                    dependency_name = '[%s].%s' % (index, dependency_name)
                elif name not in ('tagdata', 'data'):
                    if not last_block.TYPE.is_array:
                        name += '.'
                    dependency_name = name + dependency_name
                last_block = parent
                parent = last_block.parent

            # slice off the 4cc id and the period
            dependency_name = dependency_name.split('.', 1)[-1]

            iid = dir_tree.insert(
                parent_iid, 'end', text=tag_path, tags=('item',),
                values=(dependency_name, tags_dir + tag_path))

            self.destroy_subitems(iid)

    def activate_item(self, e=None):
        dir_tree = self.tag_dirs_tree
        active = dir_tree.focus()
        if active is None:
            return
        tag_path = dir_tree.item(active)['values'][-1]

        try:
            app = self.app_root
            tags_dir = self.get_item_tags_dir(tag_path)
            self.highlight_tags_dir(tags_dir)
        except Exception:
            print(format_exc())

        if isdir(tag_path):
            return

        try:
            app.load_tags(filepaths=tag_path)
        except Exception:
            print(format_exc())
