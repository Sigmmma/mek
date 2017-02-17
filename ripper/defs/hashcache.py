from supyr_struct.defs.tag_def import *

def get(): return hash_cache_def

hash_cache_header = Struct("header",
    LUInt32("id", DEFAULT='hsah'),
    LUInt32("version", DEFAULT=3),

    LUInt32("hashcount"),
    LUInt16("hashsize"),
    LUInt16("namelen"),
    LUInt32("descriptionlen"),

    Pad(76), #ROOM FOR ADDITIONAL DATA

    StrLatin1("hashmethod", SIZE=32),
    SIZE=128
    )
                          
hash_desc = Container("hash",
    BytesRaw("hash", SIZE="...header.hashsize"),
    LSInt16("value size"),
    StrUtf8("value", SIZE=".value_size")
    )

hash_cache_def = TagDef("hashcache",
    hash_cache_header,
    StrUtf8("cache_name", SIZE=".header.namelen"),
    StrUtf8("cache_description", SIZE=".header.descriptionlen"),
    Array("cache", SIZE=".header.hashcount", SUB_STRUCT=hash_desc),

    ext=".hashcache"
    )
