import tkinter as tk

from os.path import dirname, basename
from traceback import format_exc

from mozzarilla.tools.shared_widgets import HierarchyFrame
from .class_repair import tag_cls_int_to_fcc, tag_cls_int_to_ext


no_op = lambda *a, **kw: None

class ExplorerHierarchyTree(HierarchyFrame):
    map_magic = None
    tags_tree = None
    tag_index = None
    queue_tree = None

    def __init__(self, *args, **kwargs):
        self.queue_tree = kwargs.pop('queue_tree', self.queue_tree)
        kwargs['select_mode'] = 'extended'

        HierarchyFrame.__init__(self, *args, **kwargs)
        self.tags_tree.bind('<Return>', self.activate_item)

    def setup_columns(self):
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

    def reload(self, tag_index=None):
        self.tag_index = tag_index
        tags_tree = self.tags_tree
        self.setup_columns()
        if tag_index:
            # remove any currently existing children
            for child in tags_tree.get_children():
                tags_tree.delete(child)

            # generate the hierarchy
            self.add_tag_index_refs(tag_index.tag_index)

    def _compile_dict_of_selected(self, parent, selected=None, curr_dir=''):
        if selected is None:
            selected = []

        tags_tree = self.tags_tree
        for iid in tags_tree.get_children(parent):
            if len(tags_tree.item(iid, 'values')):
                # tag_index_ref
                selected.append(tags_tree.item(iid, 'values')[6])
            else:
                # directory
                self._compile_dict_of_selected(iid, selected)

        return selected

    def activate_item(self, e=None):
        tags_tree = self.tags_tree
        if self.queue_tree is None:
            return

        # add selection to queue
        for iid in tags_tree.selection():

            if len(tags_tree.item(iid, 'values')):
                # tag_index_ref
                item_name = tags_tree.parent(iid) + tags_tree.item(iid, 'text')
                tag_index_refs = (tags_tree.item(iid, 'values')[6] ,)
            else:
                # directory
                item_name = iid
                tag_index_refs = self._compile_dict_of_selected(iid)

            # ask for extraction options
            extract_options = dict(tag_index_refs=tag_index_refs)

            self.queue_tree.add_to_queue(item_name, extract_options)

    def rename_tag_index_refs(self, index_refs):
        # get the tag_id of the tag_index_ref. useing tag_tree.parent() we
        # will traverse the tree upward until we find an item with more
        # than 1 child. delete this node with tag_tree.delete()
        # if there is a new name, call self.add_tag_index_refs to add the
        # item back to the tree, but only after changing its tag.tag_path
        pass

    def add_tag_index_refs(self, index_refs, dont_sort=False):
        map_magic = self.map_magic
        tags_tree = self.tags_tree

        if dont_sort:
            assert isinstance(index_refs, dict)
            index_refs_by_path = index_refs
        else:
            index_refs_by_path = {}
            # sort the index_refs
            if isinstance(index_refs, dict):
                index_refs = index_refs.keys()

            for b in index_refs:
                try:
                    ext = "." + tag_cls_int_to_ext[b.class_1.data]
                except Exception:
                    ext = ".INVALID"

                index_refs_by_path[b.tag.tag_path.replace\
                                   ("/", "\\").lower() + ext] = b

        # add all the directories before files
        for tag_path in sorted(index_refs_by_path):
            dir_path = dirname(tag_path) + '\\'

            try:
                if not tags_tree.exists(dir_path):
                    self.add_folder_path(dir_path.split("\\"))
            except Exception:
                print(format_exc())

        for tag_path in sorted(index_refs_by_path):
            dir_path = dirname(tag_path) + '\\'
            tag_name = basename(tag_path)
            b = index_refs_by_path[tag_path]
            tag_id = b.id[0]
            map_magic = self.map_magic

            if b.indexed and map_magic:
                pointer = "not in map"
            elif map_magic:
                pointer = b.meta_offset - map_magic
            else:
                pointer = 0

            if not map_magic:
                # resource cache tag
                tag_id += (b.id[1] << 16)

            try:
                tags_tree.insert(
                    dir_path, 'end', iid=tag_id, text=tag_name,
                    values=(tag_cls_int_to_fcc.get(b.class_1.data, ''),
                            tag_cls_int_to_fcc.get(b.class_2.data, ''),
                            tag_cls_int_to_fcc.get(b.class_3.data, ''),
                            b.meta_offset, pointer, tag_id, b))
            except Exception:
                print(format_exc())

        

    def add_folder_path(self, dir_paths=(), parent_dir=''):
        if not dir_paths:
            return

        this_dir = dir_paths.pop(0)
        if not this_dir:
            return

        abs_dir_path = parent_dir + this_dir + "\\"

        if not self.tags_tree.exists(abs_dir_path):
            # add the directory to the treeview
            self.tags_tree.insert(
                parent_dir, 'end', iid=abs_dir_path, text=this_dir)

        self.add_folder_path(dir_paths, abs_dir_path)

    open_selected = close_selected = no_op

    set_root_dir = add_root_dir = insert_root_dir = del_root_dir = no_op

    destroy_subitems = no_op

    get_item_tags_dir = highlight_tags_dir = no_op


class ExplorerClassTree(ExplorerHierarchyTree):

    def add_tag_index_refs(self, index_refs, dont_sort=False):
        map_magic = self.map_magic
        tags_tree = self.tags_tree

        if dont_sort:
            assert isinstance(index_refs, dict)
            index_refs_by_path = index_refs
        else:
            index_refs_by_path = {}

            # sort the index_refs
            if isinstance(index_refs, dict):
                index_refs = index_refs.keys()

            for b in index_refs:
                try:
                    ext = "." + tag_cls_int_to_ext[b.class_1.data]
                except Exception:
                    ext = ".INVALID"

                index_refs_by_path[b.tag.tag_path.replace\
                                   ("/", "\\").lower() + ext] = b

        for tag_path in sorted(index_refs_by_path):
            b = index_refs_by_path[tag_path]
            tag_cls = tag_cls_int_to_fcc.get(b.class_1.data, '')
            tag_id = b.id[0]
            map_magic = self.map_magic
            dir_path = dirname(tag_path)

            if b.indexed and map_magic:
                pointer = "not in map"
            elif map_magic:
                pointer = b.meta_offset - map_magic
            else:
                pointer = 0

            if not map_magic:
                # resource cache tag
                tag_id += (b.id[1] << 16)

            try:
                if not tags_tree.exists(tag_cls + '\\'):
                    self.add_folder_path([tag_cls])

                tags_tree.insert(
                    tag_cls + '\\', 'end', iid=tag_id, text=tag_path,
                    values=(tag_cls_int_to_fcc.get(b.class_1.data, ''),
                            tag_cls_int_to_fcc.get(b.class_2.data, ''),
                            tag_cls_int_to_fcc.get(b.class_3.data, ''),
                            b.meta_offset, pointer, tag_id, b))
            except Exception:
                print(format_exc())


class ExplorerHybridTree(ExplorerHierarchyTree):

    def add_tag_index_refs(self, index_refs, dont_sort=False):
        index_refs_by_tag_cls = {}
        if isinstance(index_refs, dict):
            index_refs = index_refs.keys()

        for b in index_refs:
            try:
                ext = "." + tag_cls_int_to_ext[b.class_1.data]
            except Exception:
                ext = ".INVALID"

            tag_cls = tag_cls_int_to_fcc.get(b.class_1.data, 'INVALID')

            index_refs_by_tag_cls[tag_cls + "\\" + b.tag.tag_path.replace\
                                  ("/", "\\").lower() + ext] = b

        ExplorerHierarchyTree.add_tag_index_refs(self, index_refs_by_tag_cls, 1)


class QueueTree(ExplorerHierarchyTree):
    # keys are the iid's of the items in the queue
    # values are dictionaries containing extraction details
    queue_info = None

    def __init__(self, *args, **kwargs):
        self.queue_info = {}
        ExplorerHierarchyTree.__init__(self, *args, **kwargs)

        self.tags_tree.bind('<BackSpace>', self.remove_curr_selection)
        self.tags_tree.bind('<Delete>', self.remove_curr_selection)

    def setup_columns(self):
        tags_tree = self.tags_tree
        if not tags_tree['columns']:
            # dont want to do this more than once
            tags_tree['columns'] = ('overwrite',)
            tags_tree.heading("#0", text='')
            tags_tree.heading("overwrite", text='overwrite')

            tags_tree.column("#0", minwidth=100, width=100)
            tags_tree.column("overwrite", minwidth=50, width=50, stretch=True)

    def activate_item(self, e=None):
        tags_tree = self.tags_tree
        if not tags_tree.selection():
            return

        # edit queue

    def add_to_queue(self, item_name, new_queue_info):
        self.queue_info[item_name] = new_queue_info

        if self.tags_tree.exists(item_name):
            self.tags_tree.delete(item_name)
        self.tags_tree.insert('', 'end', iid=item_name, text=item_name)

    def remove_items(self, items=None):
        if items is None:
            items = self.tags_tree.get_children()
        if not hasattr(items, "__iter__"):
            items = (items, )

        for item in items:
            self.queue_info.pop(item, None)

        self.tags_tree.delete(*items)

    def remove_curr_selection(self, e=None):
        self.remove_items(self.tags_tree.selection())

    def reload(self, tag_index=None):
        self.setup_columns()

        # remove any currently existing children
        self.remove_items()


class RefinerySettingsWindow(tk.Toplevel):
    tk_vars = None

    def __init__(self, *args, **kwargs):
        self.tk_vars = tk_vars = kwargs.pop('tk_vars', {})
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.geometry("250x210")
        self.resizable(0, 0)
        self.title("Refinery settings")

        self.extract_frame   = tk.LabelFrame(self, text="Extraction settings")
        self.deprotect_frame = tk.LabelFrame(self, text="Deprotection settings")
        self.yelo_frame      = tk.LabelFrame(self, text="Open Sauce settings")

        self.extract_from_ce_resources_checkbutton = tk.Checkbutton(
            self.extract_frame, text="Extract from CE resource maps",
            variable=tk_vars.get("extract_from_ce_resources", tk.IntVar))

        self.fix_tag_classes_checkbutton = tk.Checkbutton(
            self.deprotect_frame, text="Fix tag classes",
            variable=tk_vars.get("fix_tag_classes", tk.IntVar))
        self.use_hashcaches_checkbutton = tk.Checkbutton(
            self.deprotect_frame, text="Use hashcaches",
            variable=tk_vars.get("use_hashcaches", tk.IntVar))
        self.use_heuristics_checkbutton = tk.Checkbutton(
            self.deprotect_frame, text="Use heuristics",
            variable=tk_vars.get("use_heuristics", tk.IntVar))

        self.use_old_gelo_checkbutton = tk.Checkbutton(
            self.yelo_frame, text="Use old project_yellow_globals definition",
            variable=tk_vars.get("use_old_gelo", tk.IntVar))
        self.extract_cheape_checkbutton = tk.Checkbutton(
            self.yelo_frame, text="Extract cheape.map from yelo maps",
            variable=tk_vars.get("extract_cheape", tk.IntVar))

        # pack everything
        self.extract_frame.pack(padx=4, pady=2, expand=True, fill="x")
        self.deprotect_frame.pack(padx=4, pady=2, expand=True, fill="x")
        self.yelo_frame.pack(padx=4, pady=2, expand=True, fill="x")

        self.extract_from_ce_resources_checkbutton.pack(padx=4, side='left')

        self.fix_tag_classes_checkbutton.pack(padx=4, anchor='w')
        self.use_hashcaches_checkbutton.pack(padx=4, anchor='w')
        self.use_heuristics_checkbutton.pack(padx=4, anchor='w')

        self.extract_cheape_checkbutton.pack(padx=4, anchor='w')
        self.use_old_gelo_checkbutton.pack(padx=4, anchor='w')

        # make the window not show up on the start bar
        self.transient(self.master)

    def destroy(self):
        try: self.master.settings_window = None
        except AttributeError: pass
        tk.Toplevel.destroy(self)
