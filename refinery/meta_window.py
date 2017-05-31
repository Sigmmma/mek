import tkinter as tk
from binilla.tag_window import *
from mozzarilla.widget_picker import def_halo_widget_picker
from supyr_struct.defs.constants import *


class MetaWindow(TagWindow):
    widget_picker = def_halo_widget_picker
    tag_path = None
    save_as_60 = False

    def __init__(self, master, tag, *args, **kwargs):
        self.tag_path = kwargs.pop("tag_path", self.tag_path)
        self.tag = tag

        # delete the tags_dir so the FieldWidgets dont create
        # unusable browse/open buttons for dependencies
        self.tag.tags_dir = None
        del self.tag.tags_dir

        kwargs["tag_def"] = None
        TagWindow.__init__(self, master, tag, *args, **kwargs)
        self.bind('<Shift-MouseWheel>', self.mousewheel_scroll_x)
        self.bind('<MouseWheel>', self.mousewheel_scroll_y)

    def save(self, **kwargs):
        print("Cannot save meta-data")

    def destroy(self):
        del self.tag
        tk.Toplevel.destroy(self)

    def select_window(self, e):
        pass

    def bind_hotkeys(self, hotkeys=None):
        pass

    def unbind_hotkeys(self, hotkeys=None):
        pass

    def populate(self):
        '''
        Destroys the FieldWidget attached to this TagWindow and remakes it.
        '''
        # Destroy everything
        if hasattr(self.field_widget, 'destroy'):
            self.field_widget.destroy()
            self.field_widget = None

        # Get the desc of the top block in the tag
        root_block = self.tag.data.tagdata

        # Get the widget to build
        widget_cls = self.widget_picker.get_widget(root_block.desc)

        # Rebuild everything
        self.field_widget = widget_cls(self.root_frame, node=root_block,
                                       show_frame=True, tag_window=self)
        self.field_widget.pack(expand=True, fill='both')


    def update_title(self, new_title=None):
        if new_title is None:
            new_title = self.tag_path
        self.title(new_title)
