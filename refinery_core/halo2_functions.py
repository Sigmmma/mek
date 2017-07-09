from math import pi, sqrt
from struct import unpack, pack_into
from traceback import format_exc

from supyr_struct.buffer import BytearrayBuffer
from supyr_struct.defs.constants import *
from supyr_struct.defs.util import *
from supyr_struct.field_types import FieldType

from .byteswapping import raw_block_def


def inject_rawdata(self, meta, tag_cls, tag_index_ref):
    pass


def meta_to_tag_data(self, meta, tag_cls, tag_index_ref):
    return meta
