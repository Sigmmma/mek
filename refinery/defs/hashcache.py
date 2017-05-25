from supyr_struct.defs.tag_def import *
try:
    from binilla.field_widgets import TextFrame
except Exception:
    TextFrame = None

def get():
    return hashcache_def

hashcache_header = Struct("header",
    UInt32("id", DEFAULT='hsah', EDITABLE=False),
    UInt32("version", DEFAULT=3, EDITABLE=False),

    UInt32("hashcount", EDITABLE=False),
    UInt16("hashsize", EDITABLE=False),
    UInt16("namelen", VISIBLE=False),
    UInt32("descriptionlen", VISIBLE=False),

    Pad(76), #ROOM FOR ADDITIONAL DATA

    StrLatin1("hashmethod", SIZE=32, EDITABLE=False),
    SIZE=128
    )
                          
hash_desc = Container("hash",
    BytesRaw("hash", SIZE="...header.hashsize"),
    SInt16("value size", VISIBLE=False, EDITABLE=False),
    StrUtf8("value", SIZE=".value_size")
    )

hashcache_def = TagDef("hashcache",
    hashcache_header,
    StrUtf8("cache_name", SIZE=".header.namelen"),
    StrUtf8("cache_description",
        SIZE=".header.descriptionlen", WIDGET=TextFrame),
    Array("cache", SIZE=".header.hashcount", SUB_STRUCT=hash_desc),

    ext=".hashcache", endian="<"
    )
