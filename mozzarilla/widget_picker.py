from binilla import editor_constants as e_c
from binilla.widget_picker import *
from binilla.widgets import BinillaWidget
from .field_widgets import *
from reclaimer.field_types import *

e_c.TITLE_WIDTH = 28
e_c.DEF_STRING_ENTRY_WIDTH = 30
e_c.DEF_STRING_ENTRY_WIDTH = 30
BinillaWidget.title_width = e_c.TITLE_WIDTH
BinillaWidget.def_string_entry_width = e_c.DEF_STRING_ENTRY_WIDTH
BinillaWidget.max_string_entry_width = e_c.MAX_STRING_ENTRY_WIDTH

__all__ = ("WidgetPicker", "def_widget_picker", "add_widget",
           "MozzarillaWidgetPicker", "def_halo_widget_picker")

class MozzarillaWidgetPicker(WidgetPicker):
    pass

def_halo_widget_picker = dhwp = MozzarillaWidgetPicker()

dhwp.add_widget(HaloRefStr, EntryFrame)
dhwp.add_widget(TagIndexRef, DependencyFrame)

dhwp.copy_widget(FlUTF16StrData, StrUtf16)
dhwp.copy_widget(FlStrUTF16, StrUtf16)

dhwp.copy_widget(FlUInt16, UInt16)
dhwp.copy_widget(FlUInt32, UInt32)
dhwp.copy_widget(FlUEnum16, UEnum16)
dhwp.copy_widget(FlUEnum32, UEnum32)
dhwp.copy_widget(FlBool16, Bool16)
dhwp.copy_widget(FlBool32, Bool32)
dhwp.copy_widget(FlSInt16, SInt16)
dhwp.copy_widget(FlSInt32, SInt32)
dhwp.copy_widget(FlSEnum16, SEnum16)
dhwp.copy_widget(FlSEnum32, SEnum32)

dhwp.copy_widget(FlFloat, Float)

dhwp.copy_widget(RawdataRef, Struct)
dhwp.copy_widget(Reflexive, Struct)

dhwp.copy_widget(TagIndex, Array)
dhwp.copy_widget(Rawdata, BytearrayRaw)
dhwp.copy_widget(StrLatin1Enum, SEnum32)
