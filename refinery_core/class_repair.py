from supyr_struct.defs.constants import *
from supyr_struct.defs.util import *
from reclaimer.os_v4_hek.handler import \
     tag_class_be_int_to_fcc_os,     tag_class_fcc_to_ext_os,\
     tag_class_be_int_to_fcc_stubbs, tag_class_fcc_to_ext_stubbs

tag_cls_int_to_fcc = dict(tag_class_be_int_to_fcc_os)
tag_cls_int_to_ext = {}

tag_cls_int_to_fcc.update(tag_class_be_int_to_fcc_stubbs)

for key in tag_class_be_int_to_fcc_os:
    tag_cls_int_to_ext[key] = tag_class_fcc_to_ext_os[
        tag_class_be_int_to_fcc_os[key]]

for key in tag_class_be_int_to_fcc_stubbs:
    tag_cls_int_to_ext[key] = tag_class_fcc_to_ext_stubbs[
        tag_class_be_int_to_fcc_stubbs[key]]


NULL_CLASS = b'\xFF\xFF\xFF\xFF'

shader_class_bytes = (
    NULL_CLASS,
    NULL_CLASS,
    NULL_CLASS,
    b'vnes',
    b'osos',
    b'rtos',
    b'ihcs',
    b'xecs',
    b'taws',
    b'algs',
    b'tems',
    b'alps',
    b'rdhs'
    )

object_class_bytes = (
    b'dpib',
    b'ihev',
    b'paew',
    b'piqe',
    b'brag',
    b'jorp',
    b'necs',
    b'hcam',
    b'lrtc',
    b'ifil',
    b'calp',
    b'ecss',
    b'ejbo'
    )

def read_reflexive(map_data, offset):
    '''
    Reads a reflexive from the given map_data at the given offset.
    Returns the reflexive's offset and pointer
    '''
    map_data.seek(offset)
    return (int.from_bytes(map_data.read(4), "little"),
            int.from_bytes(map_data.read(4), "little"))


def iter_reflexive_offs(map_data, offset, struct_size):
    '''
    Reads a reflexive from the given map_data at the given offset.
    Returns the reflexive's offset and pointer
    '''
    map_data.seek(offset)
    count = int.from_bytes(map_data.read(4), "little")
    start = int.from_bytes(map_data.read(4), "little")
    return range(start, start + count*struct_size, struct_size)


def repair_dependency(index_array, map_data, magic, repair, engine, cls,
                      offset, map_magic=None):
    if map_magic is None:
        map_magic = magic

    offset -= magic
    if cls is None:
        map_data.seek(offset)
        cls = map_data.read(4)

    map_data.seek(offset + 12)
    tag_id = int.from_bytes(map_data.read(4), "little") & 0xFFFF

    if tag_id != 0xFFFF:
        # if the class is obje or shdr, make sure to get the ACTUAL class
        if cls in b'ejbo_meti_ived_tinu':
            map_data.seek(index_array[tag_id].meta_offset - map_magic)
            cls = object_class_bytes[
                int.from_bytes(map_data.read(2), 'little')]
        elif cls == b'rdhs':
            map_data.seek(index_array[tag_id].meta_offset - map_magic + 36)
            cls = shader_class_bytes[
                int.from_bytes(map_data.read(2), 'little')]
        elif cls in b'2dom_edom':
            if "xbox" in engine:
                cls = b'edom'
            else:
                cls = b'2dom'

        map_data.seek(offset)
        map_data.write(cls)

        if tag_id not in repair:
            repair[tag_id] = cls[slice(None, None, -1)]\
                             .decode(encoding='latin-1')
            #DEBUG
            # print("        %s %s %s" % (tag_id, cls, offset))


def repair_hud_background(index_array, map_data, magic, repair, engine, offset):
    args = (index_array, map_data, magic, repair, engine, b'mtib')
    repair_dependency(*(args + (offset + 36, )))
    for moff in iter_reflexive_offs(map_data, offset + 88 - magic, 480):
        repair_dependency(*(args + (moff + 100, )))
        repair_dependency(*(args + (moff + 116, )))
        repair_dependency(*(args + (moff + 132, )))


def repair_dependency_array(index_array, map_data, magic, repair, engine,
                            base_class, start, array_size, struct_size=16,
                            map_magic=None):
    '''Macro for deprotecting a contiguous array of dependencies'''
    for offset in range(start, start + array_size*struct_size, struct_size):
        repair_dependency(
            index_array, map_data, magic, repair, engine, base_class, offset,
            map_magic)


def repair_devi_attrs(offset, index_array, map_data, magic, repair, engine):
    # struct size is 276
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (None, offset + 36)))
    repair_dependency(*(args + (None, offset + 52)))
    repair_dependency(*(args + (None, offset + 68)))
    repair_dependency(*(args + (None, offset + 84)))
    repair_dependency(*(args + (None, offset + 100)))
    repair_dependency(*(args + (None, offset + 116)))
    repair_dependency(*(args + (None, offset + 144)))


def repair_item_attrs(offset, index_array, map_data, magic, repair, engine):
    # struct size is 396
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'toof', offset + 204)))
    repair_dependency(*(args + (b'!dns', offset + 220)))
    repair_dependency(*(args + (b'effe', offset + 364)))
    repair_dependency(*(args + (b'effe', offset + 380)))


def repair_unit_attrs(offset, index_array, map_data, magic, repair, engine):
    # struct size is 372
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'effe', offset + 12)))

    ct, moff = read_reflexive(map_data, offset + 120 - magic)
    repair_dependency_array(*(args + (b'kart', moff, ct, 28)))

    repair_dependency(*(args + (b'vtca', offset + 208)))
    repair_dependency(*(args + (b'!tpj', offset + 268)))

    ct, moff = read_reflexive(map_data, offset + 300 - magic)
    repair_dependency_array(*(args + (b'ihnu', moff, ct, 48)))

    ct, moff = read_reflexive(map_data, offset + 312 - magic)
    repair_dependency_array(*(args + (b'gldu', moff + 8, ct, 24)))

    ct, moff = read_reflexive(map_data, offset + 348 - magic)
    repair_dependency_array(*(args + (b'paew', moff, ct, 36)))

    for moff in iter_reflexive_offs(map_data, offset + 360 - magic, 284):
        # seats
        ct, moff2 = read_reflexive(map_data, moff + 208 - magic)
        repair_dependency_array(*(args + (b'kart', moff2, ct, 28)))

        ct, moff2 = read_reflexive(map_data, moff + 220 - magic)
        repair_dependency_array(*(args + (b'ihnu', moff2, ct, 48)))

        repair_dependency(*(args + (b'vtca', moff + 248)))

        if engine == "yelo":
            # seat extension
            for moff2 in iter_reflexive_offs(map_data, moff + 264 - magic, 100):
                off = moff2 - magic
                # seat boarding
                for moff3 in iter_reflexive_offs(map_data, off + 28, 112):
                    # seat keyframe action
                    for moff4 in iter_reflexive_offs(map_data, moff3 + 76, 152):
                        repair_dependency(*(args + (b'!tpj', moff3 + 48)))
                        repair_dependency(*(args + (b'effe', moff3 + 68)))

                # seat damage
                for moff3 in iter_reflexive_offs(map_data, off + 40, 136):
                    repair_dependency(*(args + (b'!tpj', moff3 + 4)))
                    repair_dependency(*(args + (b'!tpj', moff3 + 96)))

    if engine == "yelo":
        # unit extension
        for moff in iter_reflexive_offs(map_data, offset + 288 - magic, 60):
            # mounted states
            for moff2 in iter_reflexive_offs(map_data, moff - magic, 128):
                ct, moff3 = read_reflexive(map_data, moff2 + 80 - magic)
                repair_dependency_array(*(args + (b'kart', moff3, ct, 28)))

                # unit keyframe action
                for moff3 in iter_reflexive_offs(map_data, moff2 + 92, 96):
                    repair_dependency(*(args + (b'!tpj', moff3 + 8)))
                    repair_dependency(*(args + (b'effe', moff3 + 24)))


def repair_actv(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'rtca', tag_offset + 0x4)))
    repair_dependency(*(args + (b'tinu', tag_offset + 0x14)))
    repair_dependency(*(args + (b'vtca', tag_offset + 0x24)))
    repair_dependency(*(args + (b'paew', tag_offset + 0x64)))
    repair_dependency(*(args + (b'piqe', tag_offset + 0x1C0)))


def repair_ant_(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'mtib', tag_offset + 0x20)))
    repair_dependency(*(args + (b'yhpp', tag_offset + 0x30)))


def repair_antr(tag_id, index_array, map_data, magic, repair, engine):
    ct, moff = read_reflexive(
        map_data, index_array[tag_id].meta_offset + 0x54 - magic)
    repair_dependency_array(index_array, map_data, magic, repair, engine,
                            b'!dns', moff, ct, 20)


def repair_coll(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine, b'effe')
    repair_dependency(*(args + (tag_offset + 0x70, )))
    repair_dependency(*(args + (tag_offset + 0x84, )))
    repair_dependency(*(args + (tag_offset + 0x98, )))
    repair_dependency(*(args + (tag_offset + 0xA8, )))
    repair_dependency(*(args + (tag_offset + 0xBC, )))
    repair_dependency(*(args + (tag_offset + 0x188, )))
    repair_dependency(*(args + (tag_offset + 0x198, )))
    repair_dependency(*(args + (tag_offset + 0x1A8, )))

    ct, moff = read_reflexive(map_data, tag_offset + 0x240 - magic)
    repair_dependency_array(*(args + (moff + 0x38, ct, 0x54)))


def repair_cont(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'mtib', tag_offset + 0x30)))
    repair_dependency(*(args + (b'mtib', tag_offset + 0xD0)))
    ct, moff = read_reflexive(map_data, tag_offset + 0x138 - magic)
    repair_dependency_array(*(args + (b'yhpp', moff + 16, ct, 104)))


def repair_deca(tag_id, index_array, map_data, magic, repair, engine):
    moff = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'aced', moff + 0x8)))
    repair_dependency(*(args + (b'mtib', moff + 0xD8)))


def repair_DeLa(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'mtib', tag_offset + 56)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 84 - magic, 72):
        repair_dependency(*(args + (b'aLeD', moff + 8)))
        repair_dependency(*(args + (b'!dns', moff + 24)))

    repair_dependency(*(args + (b'rtsu', tag_offset + 236)))
    repair_dependency(*(args + (b'tnof', tag_offset + 252)))
    repair_dependency(*(args + (b'mtib', tag_offset + 340)))
    repair_dependency(*(args + (b'mtib', tag_offset + 356)))
    repair_dependency(*(args + (b'aLeD', tag_offset + 420)))

    ct, moff = read_reflexive(map_data, tag_offset + 724 - magic)
    repair_dependency_array(*(args + (b'aLeD', moff, ct, 80)))

    ct, moff = read_reflexive(map_data, tag_offset + 992 - magic)
    repair_dependency_array(*(args + (b'aLeD', moff, ct, 80)))


def repair_dobc(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'mtib', index_array[tag_id].meta_offset + 52)


def repair_effe(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x34 - magic, 0x44):
        # parts
        for moff2 in iter_reflexive_offs(map_data, moff + 0x2C - magic, 0x68):
            map_data.seek(moff2 - magic + 0x14)
            tag_class = map_data.read(4)
            repair_dependency(*(args + (tag_class, moff2 + 0x18)))

        # particles
        ct, moff2 = read_reflexive(map_data, moff + 0x38 - magic)
        repair_dependency_array(*(args + (b'trap', moff2 + 0x54, ct, 0xE8)))


def repair_elec(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'mtib', index_array[tag_id].meta_offset + 52)

def repair_flag(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'rdhs', tag_offset + 0x18)))
    repair_dependency(*(args + (b'yhpp', tag_offset + 0x28)))
    repair_dependency(*(args + (b'rdhs', tag_offset + 0x44)))


def repair_fog(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'mtib', tag_offset + 0xBC)))
    repair_dependency(*(args + (b'dnsl', tag_offset + 0xF4)))
    repair_dependency(*(args + (b'edns', tag_offset + 0x104)))


def repair_font(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency_array(index_array, map_data, magic, repair, engine,
                            b'mtib', index_array[tag_id].meta_offset + 0x3C, 4)


def repair_foot(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    for moff in iter_reflexive_offs(map_data, tag_offset - magic, 28):
        for moff2 in iter_reflexive_offs(map_data, moff - magic, 48):
            repair_dependency(*(args + (b'effe', moff2)))
            repair_dependency(*(args + (b'!dns', moff2 + 16)))


def repair_glw_(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'mtib', index_array[tag_id].meta_offset + 324)

def repair_grhi(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    # grenade hud background
    repair_hud_background(*(args + (tag_offset + 36, )))
    # total grenades background
    repair_hud_background(*(args + (tag_offset + 140, )))

    repair_dependency(*(args + (b'mtib', tag_offset + 332)))

    # warning sounds
    for moff in iter_reflexive_offs(map_data, tag_offset + 360 - magic, 56):
        map_data.seek(moff - magic)
        if map_data.read(4) == b'dnsl':
            repair_dependency(*(args + (b'dnsl', moff)))
        else:
            repair_dependency(*(args + (b'!dns', moff)))


def repair_hud_(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'mtib', index_array[tag_id].meta_offset)


def repair_hudg(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'tnof', tag_offset + 0x48, )))
    repair_dependency(*(args + (b'tnof', tag_offset + 0x58, )))
    repair_dependency(*(args + (b'rtsu', tag_offset + 0x94, )))
    repair_dependency(*(args + (b'mtib', tag_offset + 0xA4, )))
    repair_dependency(*(args + (b'rtsu', tag_offset + 0xB4, )))
    repair_dependency(*(args + (b' tmh', tag_offset + 0xF0, )))
    repair_dependency(*(args + (b'mtib', tag_offset + 0x150, )))
    repair_dependency(*(args + (b'ihpw', tag_offset + 0x2C0, )))
    repair_dependency(*(args + (b'mtib', tag_offset + 0x338, )))
    repair_dependency(*(args + (b'mtib', tag_offset + 0x3C8, )))
    repair_dependency(*(args + (b'!dns', tag_offset + 0x3E0, )))


def repair_itmc(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    ct, moff = read_reflexive(map_data, tag_offset - magic)
    repair_dependency_array(*(args + (b'meti', moff + 36, ct, 84)))


def repair_jpt_(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'!dns', index_array[tag_id].meta_offset + 0x114)


def repair_lens(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'mtib', index_array[tag_id].meta_offset + 0x20)


def repair_ligh(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'mtib', tag_offset + 0x64)))
    repair_dependency(*(args + (b'mtib', tag_offset + 0x7C)))
    repair_dependency(*(args + (b'snel', tag_offset + 0xAC)))


def repair_lsnd(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'gmdc', tag_offset + 0x2C)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 0x3C - magic, 0xA0):
        repair_dependency(*(args + (b'!dns', moff + 0x30)))
        repair_dependency(*(args + (b'!dns', moff + 0x40)))
        repair_dependency(*(args + (b'!dns', moff + 0x50)))
        repair_dependency(*(args + (b'!dns', moff + 0x80)))
        repair_dependency(*(args + (b'!dns', moff + 0x90)))

    ct, moff = read_reflexive(map_data, tag_offset + 0x48 - magic)
    repair_dependency_array(*(args + (b'!dns', moff, ct, 104)))


def repair_matg(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    # sounds
    ct, moff = read_reflexive(map_data, tag_offset + 0xF8 - magic)
    repair_dependency_array(*(args + (b'!dns', moff, ct)))

    # camera
    ct, moff = read_reflexive(map_data, tag_offset + 0x104 - magic)
    repair_dependency_array(*(args + (b'kart', moff, ct)))

    # grenades
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x128 - magic, 68):
        repair_dependency(*(args + (b'effe', moff + 4)))
        repair_dependency(*(args + (b'ihrg', moff + 20)))
        repair_dependency(*(args + (b'piqe', moff + 36)))
        repair_dependency(*(args + (b'jorp', moff + 52)))


    # rasterizer data
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x134 - magic, 428):
        # function textures
        repair_dependency_array(*(args + (b'mtib', moff, 7)))
        moff += 7*16 + 60
        # default/experimental/video effect textures
        repair_dependency_array(*(args + (b'mtib', moff, 9)))
        moff += 9*16 + 52 + 4*11
        # pc textures
        repair_dependency(*(args + (b'mtib', moff)))

    # interface bitmaps
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x140 - magic, 304):
        repair_dependency_array(*(args + (b'tnof', moff, 2)))
        repair_dependency_array(*(args + (b'oloc', moff + 32, 4)))
        repair_dependency(*(args + (b'gduh', moff + 96)))
        repair_dependency_array(*(args + (b'mtib', moff + 112, 3)))
        repair_dependency(*(args + (b'#rts', moff + 160)))
        repair_dependency(*(args + (b'#duh', moff + 176)))
        repair_dependency_array(*(args + (b'mtib', moff + 192, 4)))

    # weapons
    ct, moff = read_reflexive(map_data, tag_offset + 0x14C - magic)
    repair_dependency_array(*(args + (b'ejbo', moff, ct)))

    # powerups
    ct, moff = read_reflexive(map_data, tag_offset + 0x158 - magic)
    repair_dependency_array(*(args + (b'ejbo', moff, ct)))

    # multiplayer info
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x164 - magic, 160):
        repair_dependency(*(args + (b'meti', moff)))
        repair_dependency(*(args + (b'tinu', moff + 16)))
        # vehicles
        v_ct, v_moff = read_reflexive(map_data, moff + 32 - magic)
        repair_dependency_array(*(args + (b'ejbo', v_moff, v_ct)))
        # shaders
        repair_dependency_array(*(args + (b'rdhs', moff + 44, 2)))
        repair_dependency(*(args + (b'meti', moff + 76)))
        # sounds
        s_ct, s_moff = read_reflexive(map_data, moff + 92 - magic)
        repair_dependency_array(*(args + (b'!dns', s_moff, s_ct)))

    # player info
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x170 - magic, 244):
        repair_dependency(*(args + (b'tinu', moff)))
        repair_dependency(*(args + (b'effe', moff + 184)))

    # fp interface
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x17C - magic, 192):
        repair_dependency(*(args + (b'2dom', moff)))
        repair_dependency(*(args + (b'mtib', moff + 16)))
        repair_dependency(*(args + (b'rtem', moff + 32)))
        repair_dependency(*(args + (b'rtem', moff + 52)))
        repair_dependency_array(*(args + (b'effe', moff + 72, 2)))

    # falling damage
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x188 - magic, 152):
        repair_dependency(*(args + (b'!tpj', moff + 16)))
        repair_dependency_array(*(args + (b'!tpj', moff + 44, 5)))

    # materials
    for moff in iter_reflexive_offs(map_data, tag_offset + 0x194 - magic, 884):
        repair_dependency(*(args + (b'effe', moff + 740)))
        repair_dependency(*(args + (b'!dns', moff + 756)))
        repair_dependency(*(args + (b'!dns', moff + 868)))
        # particle effects
        p_ct, p_moff = read_reflexive(map_data, moff + 796 - magic)
        repair_dependency_array(*(args + (b'trap', p_moff, p_ct, 128)))


def repair_mgs2(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'mtib', index_array[tag_id].meta_offset + 92)


def repair_mode(tag_id, index_array, map_data, magic, repair, engine):
    ct, moff = read_reflexive(
        map_data, index_array[tag_id].meta_offset + 0xDC - magic)
    repair_dependency_array(index_array, map_data, magic, repair,
                            engine, b'rdhs', moff, ct, 32)


def repair_mply(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    for moff in iter_reflexive_offs(map_data, tag_offset - magic, 68):
        repair_dependency(*(args + (b'mtib', moff)))
        repair_dependency(*(args + (b'rtsu', moff + 16)))


def repair_ngpr(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'mtib', tag_offset + 56)))
    repair_dependency(*(args + (b'mtib', tag_offset + 76)))


def repair_predicted_resources(map_data, offset, magic, repair):
    for moff in iter_reflexive_offs(map_data, offset - magic, 8):
        map_data.seek(moff - magic)
        rsrc_type = map_data.read(4)[:2]
        tag_id = int.from_bytes(map_data.read(4), "little") & 0xFFFF

        if tag_id == 0xFFFF:
            continue
        elif rsrc_type == b'\x00\x00':
            # bitmap resource type
            repair[tag_id] = 'bitm'
        elif rsrc_type == b'\x01\x00':
            # sound resource type
            repair[tag_id] = 'snd!'


def repair_object(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    map_data.seek(tag_offset - magic)
    object_type = int.from_bytes(map_data.read(2), 'little')

    # obje_attrs struct size is 380
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'2dom', tag_offset + 40)))
    repair_dependency(*(args + (b'rtna', tag_offset + 56)))

    repair_dependency(*(args + (b'lloc', tag_offset + 112)))
    repair_dependency(*(args + (b'syhp', tag_offset + 128)))
    repair_dependency(*(args + (b'rdhs', tag_offset + 144)))
    repair_dependency(*(args + (b'effe', tag_offset + 160)))

    ct, moff = read_reflexive(map_data, tag_offset + 320 - magic)
    repair_dependency_array(*(args + (None, moff, ct, 72)))

    ct, moff = read_reflexive(map_data, tag_offset + 332 - magic)
    repair_dependency_array(*(args + (None, moff, ct, 32)))

    # add the predicted resources to the tags to repair
    repair_predicted_resources(map_data, tag_offset + 368, magic, repair)

    tag_offset += 380
    args2 = (index_array, map_data, magic, repair, engine)
    if object_type <= 1:
        # bipd or vehi
        repair_unit_attrs(tag_offset, *args2)
        tag_offset += 372
        if object_type == 0:
            # bipd
            repair_dependency(*(args + (b'!tpj', tag_offset + 36)))
            repair_dependency(*(args + (b'toof', tag_offset + 156)))
        else:
            # vehi
            repair_dependency(*(args + (b'!dns', tag_offset + 192)))
            repair_dependency(*(args + (b'!dns', tag_offset + 208)))
            repair_dependency(*(args + (b'toof', tag_offset + 224)))
            repair_dependency(*(args + (b'effe', tag_offset + 240)))

    elif object_type <= 4:
        # weap, eqip, or garb
        repair_item_attrs(tag_offset, *args2)
        tag_offset += 396
        if object_type == 2:
            # weap
            repair_dependency(*(args + (None, tag_offset + 52)))
            repair_dependency(*(args + (None, tag_offset + 108)))
            repair_dependency(*(args + (None, tag_offset + 124)))
            repair_dependency(*(args + (b'!tpj', tag_offset + 140)))
            repair_dependency(*(args + (b'!tpj', tag_offset + 156)))
            repair_dependency(*(args + (b'vtca', tag_offset + 180)))
            repair_dependency(*(args + (None, tag_offset + 280)))
            repair_dependency(*(args + (None, tag_offset + 296)))
            repair_dependency(*(args + (b'2dom', tag_offset + 340)))
            repair_dependency(*(args + (b'rtna', tag_offset + 356)))
            repair_dependency(*(args + (b'ihpw', tag_offset + 376)))
            repair_dependency(*(args + (b'!dns', tag_offset + 392)))
            repair_dependency(*(args + (b'!dns', tag_offset + 408)))
            repair_dependency(*(args + (b'!dns', tag_offset + 424)))

            repair_predicted_resources(
                map_data, tag_offset + 476, magic, repair)

            for moff in iter_reflexive_offs(
                    map_data, tag_offset + 488 - magic, 112):
                # magazines
                repair_dependency(*(args + (None, moff + 56)))
                repair_dependency(*(args + (None, moff + 72)))

                ct, moff2 = read_reflexive(map_data, moff + 100 - magic)
                repair_dependency_array(*(args + (b'piqe', moff2 + 12, ct, 28)))

            for moff in iter_reflexive_offs(
                    map_data, tag_offset + 500 - magic, 276):
                # triggers
                repair_dependency(*(args + (None, moff + 92)))
                repair_dependency(*(args + (b'ejbo', moff + 148)))

                for moff2 in iter_reflexive_offs(
                        map_data, moff + 264 - magic, 132):
                    # firing effects
                    repair_dependency(*(args + (None, moff2 + 36)))
                    repair_dependency(*(args + (None, moff2 + 52)))
                    repair_dependency(*(args + (None, moff2 + 68)))
                    repair_dependency(*(args + (b'!tpj', moff2 + 84)))
                    repair_dependency(*(args + (b'!tpj', moff2 + 100)))
                    repair_dependency(*(args + (b'!tpj', moff2 + 116)))

        elif object_type == 3:
            # eqip
            repair_dependency(*(args + (b'!dns', tag_offset + 8)))
        else:
            # garb
            pass  # nothing else to do for this

    elif object_type == 5:
        # proj
        repair_dependency(*(args + (b'effe', tag_offset + 16)))
        repair_dependency(*(args + (b'effe', tag_offset + 48)))
        repair_dependency(*(args + (b'effe', tag_offset + 120)))
        repair_dependency(*(args + (b'!dns', tag_offset + 136)))
        repair_dependency(*(args + (b'!tpj', tag_offset + 152)))
        repair_dependency(*(args + (b'!tpj', tag_offset + 168)))

        for moff in iter_reflexive_offs(
                map_data, tag_offset + 196 - magic, 160):
            # material responses
            repair_dependency(*(args + (b'effe', moff + 4)))
            repair_dependency(*(args + (b'effe', moff + 60)))
            repair_dependency(*(args + (b'effe', moff + 104)))
    elif object_type == 6:
        # scen
        pass  # nothing else to do for this

    elif object_type <= 9:
        # mach, ctrl, or lifi
        repair_devi_attrs(tag_offset, *args2)
        tag_offset += 276
        if object_type == 8:
            # ctrl
            repair_dependency(*(args + (None, tag_offset + 88)))
            repair_dependency(*(args + (None, tag_offset + 104)))
            repair_dependency(*(args + (None, tag_offset + 120)))
        else:
            # mach, lifi
            pass  # nothing else to do for these

    else:
        # plac, or ssce
        pass  # nothing else to do for these


def repair_part(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'mtib', tag_offset + 0x4)))
    repair_dependency(*(args + (b'yhpp', tag_offset + 0x14)))
    repair_dependency(*(args + (b'toof', tag_offset + 0x24)))
    repair_dependency(*(args + (b'effe', tag_offset + 0x48)))
    repair_dependency(*(args + (b'effe', tag_offset + 0x58)))
    repair_dependency(*(args + (b'mtib', tag_offset + 0xFC)))


def repair_pctl(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'yhpp', tag_offset + 56)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 92 - magic, 128):
        for moff2 in iter_reflexive_offs(map_data, moff + 116 - magic, 376):
            repair_dependency(*(args + (b'mtib', moff2 + 48)))
            repair_dependency(*(args + (b'yhpp', moff2 + 132)))
            repair_dependency(*(args + (b'mtib', moff2 + 260)))


def repair_rain(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    for moff in iter_reflexive_offs(map_data, tag_offset + 0x24 - magic, 0x25C):
        repair_dependency(*(args + (b'yhpp', moff + 0xAC)))
        repair_dependency(*(args + (b'mtib', moff + 0x194)))
        repair_dependency(*(args + (b'mtib', moff + 0x1F4)))


def repair_sbsp(tag_offset, index_array, map_data, magic, repair, engine,
                map_magic):
    # This function requires the first argument is the tag's magic offset
    # relative to the bsp magic, rather than the tag's index id
    args = (index_array, map_data, magic, repair, engine)
    kwargs = dict(map_magic=map_magic)
    repair_dependency(*(args + (b'mtib', tag_offset)), **kwargs)

    ct, moff = read_reflexive(map_data, tag_offset + 164 - magic)
    repair_dependency_array(*(args + (b'rdhs', moff, ct, 20)), **kwargs)

    for moff in iter_reflexive_offs(map_data, tag_offset + 260 - magic, 32):
        ct, moff2 = read_reflexive(map_data, moff + 20 - magic)
        repair_dependency_array(*(args + (b'rdhs', moff2, ct, 256)), **kwargs)

    ct, moff = read_reflexive(map_data, tag_offset + 284 - magic)
    repair_dependency_array(*(args + (b'snel', moff, ct)), **kwargs)

    ct, moff = read_reflexive(map_data, tag_offset + 400 - magic)
    repair_dependency_array(*(args + (b' gof', moff + 32, ct, 136)), **kwargs)

    for moff in iter_reflexive_offs(map_data, tag_offset + 436 - magic, 240):
        repair_dependency(*(args + (b'niar', moff + 32)), **kwargs)
        repair_dependency(*(args + (b'dniw', moff + 128)), **kwargs)

    ct, moff = read_reflexive(map_data, tag_offset + 508 - magic)
    repair_dependency_array(*(args + (b'dnsl', moff + 32, ct, 116)), **kwargs)

    ct, moff = read_reflexive(map_data, tag_offset + 520 - magic)
    repair_dependency_array(*(args + (b'edns', moff + 32, ct, 80)), **kwargs)


def repair_scnr(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    if engine == "yelo":
        repair_dependency(*(args + (b'oley', tag_offset)))

    ct, moff = read_reflexive(map_data, tag_offset + 48 - magic)
    repair_dependency_array(*(args + (b' yks', moff, ct)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 840 - magic, 104):
        repair_dependency(*(args + (b'paew', moff + 40)))
        repair_dependency(*(args + (b'paew', moff + 60)))

    ct, moff = read_reflexive(map_data, tag_offset + 888 - magic)
    repair_dependency_array(*(args + (b'cmti', moff + 20, ct, 148)))

    ct, moff = read_reflexive(map_data, tag_offset + 900 - magic)
    repair_dependency_array(*(args + (b'cmti', moff + 80, ct, 144)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 912 - magic, 204):
        repair_dependency(*(args + (b'cmti', moff + 60)))
        repair_dependency(*(args + (b'cmti', moff + 76)))
        repair_dependency(*(args + (b'cmti', moff + 92)))
        repair_dependency(*(args + (b'cmti', moff + 108)))
        repair_dependency(*(args + (b'cmti', moff + 124)))
        repair_dependency(*(args + (b'cmti', moff + 140)))

    ct, moff = read_reflexive(map_data, tag_offset + 1092 - magic)
    repair_dependency_array(*(args + (b'rtna', moff + 32, ct, 60)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 1128 - magic, 116):
        for moff2 in iter_reflexive_offs(map_data, moff + 92 - magic, 124):
            repair_dependency(*(args + (b'!dns', moff2 + 28)))
            repair_dependency(*(args + (b'!dns', moff2 + 44)))
            repair_dependency(*(args + (b'!dns', moff2 + 60)))
            repair_dependency(*(args + (b'!dns', moff2 + 76)))
            repair_dependency(*(args + (b'!dns', moff2 + 92)))
            repair_dependency(*(args + (b'!dns', moff2 + 108)))

    ct, moff = read_reflexive(map_data, tag_offset + 1204 - magic)
    repair_dependency_array(*(args + (None, moff + 24, ct, 40)))

    ct, moff = read_reflexive(map_data, tag_offset + 1444 - magic)
    repair_dependency_array(*(args + (b'psbs', moff + 16, ct, 32)))

    # palettes
    for off in (540, 564, 588, 612, 636, 672, 696, 720, 744):
        ct, moff = read_reflexive(map_data, tag_offset + off - magic)
        repair_dependency_array(*(args + (b'ejbo', moff, ct, 48)))

    ct, moff = read_reflexive(map_data, tag_offset + 948 - magic)
    repair_dependency_array(*(args + (b'aced', moff, ct)))

    ct, moff = read_reflexive(map_data, tag_offset + 960 - magic)
    repair_dependency_array(*(args + (b'cbod', moff, ct, 48)))

    ct, moff = read_reflexive(map_data, tag_offset + 1056 - magic)
    repair_dependency_array(*(args + (b'vtca', moff, ct)))


def repair_shader(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    map_data.seek(tag_offset + 36 - magic)
    typ = shader_class_bytes[int.from_bytes(map_data.read(2), 'little')]

    tag_offset += 40
    args = (index_array, map_data, magic, repair, engine)

    if typ == b'vnes':
        repair_dependency(*(args + (b'snel', tag_offset + 0x8)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x60)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x90)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0xA4)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0xD4)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x100)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x22C)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x2FC)))
        # shader environment os extension
        if engine == "yelo":
            ct, moff = read_reflexive(map_data, tag_offset + 0xC8 - magic)
            repair_dependency_array(*(args + (b'mtib', moff + 8, ct, 100)))

    elif typ == b'osos':
        repair_dependency(*(args + (b'mtib', tag_offset + 0x7C)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x94)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0xB4)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x13C)))
        # shader model os extension
        if engine == "yelo":
            for moff in iter_reflexive_offs(
                    map_data, tag_offset + 0xC8 - magic, 192):
                repair_dependency(*(args + (b'mtib', moff)))
                repair_dependency(*(args + (b'mtib', moff + 0x20)))
                repair_dependency(*(args + (b'mtib', moff + 0x40)))
                repair_dependency(*(args + (b'mtib', moff + 0x60)))

    elif typ == b'tems':
        repair_dependency(*(args + (b'mtib', tag_offset + 0x24)))

    elif typ == b'algs':
        repair_dependency(*(args + (b'mtib', tag_offset + 0x3C)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x84)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x98)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x130)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x144)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x178)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x18C)))

    elif typ == b'alps':
        repair_dependency(*(args + (b'mtib', tag_offset + 0xAC)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0xF4)))

    elif typ == b'taws':
        repair_dependency(*(args + (b'mtib', tag_offset + 0x24)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0x74)))
        repair_dependency(*(args + (b'mtib', tag_offset + 0xA0)))

    elif typ in b'rtos_ihcs_xecs':
        repair_dependency(*(args + (b'snel', tag_offset + 0x10)))
        # layers
        ct, moff = read_reflexive(map_data, tag_offset + 0x20 - magic)
        repair_dependency_array(*(args + (b'rdhs', moff, ct)))
        # maps
        ct, moff = read_reflexive(map_data, tag_offset + 0x2C - magic)
        if typ == b'rtos':
            maps_size  = 0x64
            maps_start = moff + 0x1C
        else:
            maps_size  = 0xDC
            maps_start = moff + 0x6C
        repair_dependency_array(*(args + (b'mtib', maps_start, ct, maps_size)))

        if typ == b'xecs':
            # 2 stage maps
            ct, moff = read_reflexive(map_data, tag_offset + 0x38 - magic)
            repair_dependency_array(*(args + (b'mtib', moff + 0x6C, ct, 0xDC)))


def repair_sky(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'2dom', tag_offset)))
    repair_dependency(*(args + (b'rtna', tag_offset + 0x10)))
    repair_dependency(*(args + (b' gof', tag_offset + 0x98)))
    # lens flares
    ct, moff = read_reflexive(map_data, tag_offset + 0xC4 - magic)
    repair_dependency_array(*(args + (b'snel', moff, ct, 116)))


def repair_snd_(tag_id, index_array, map_data, magic, repair, engine):
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'!dns', index_array[tag_id].meta_offset + 0x70)


def repair_Soul(tag_id, index_array, map_data, magic, repair, engine):
    ct, moff = read_reflexive(map_data, index_array[tag_id].meta_offset - magic)
    repair_dependency_array(
        index_array, map_data, magic, repair, engine, b'aLeD', moff, ct)


def repair_tagc(tag_id, index_array, map_data, magic, repair, engine):
    ct, moff = read_reflexive(map_data, index_array[tag_id].meta_offset - magic)
    repair_dependency_array(
        index_array, map_data, magic, repair, engine, None, moff, ct)


def repair_udlg(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine, b'!dns')
    repair_dependency_array(*(args + (tag_offset + 0x10, 3)))
    repair_dependency_array(*(args + (tag_offset + 0x70, 14)))
    repair_dependency_array(*(args + (tag_offset + 0x160, 4)))
    repair_dependency_array(*(args + (tag_offset + 0x1E0, 17)))
    repair_dependency_array(*(args + (tag_offset + 0x320, 28)))
    repair_dependency_array(*(args + (tag_offset + 0x510, 13)))
    repair_dependency_array(*(args + (tag_offset + 0x610, 10)))
    repair_dependency_array(*(args + (tag_offset + 0x6D0, 13)))
    repair_dependency_array(*(args + (tag_offset + 0x7C0, 21)))
    repair_dependency_array(*(args + (tag_offset + 0x950, 23)))
    repair_dependency_array(*(args + (tag_offset + 0xB20, 7)))
    repair_dependency_array(*(args + (tag_offset + 0xBD0, 5)))
    repair_dependency_array(*(args + (tag_offset + 0xC60, 8)))


def repair_unhi(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    # unit hud background
    repair_hud_background(*(args + (tag_offset + 36, )))
    # shield panel background
    repair_hud_background(*(args + (tag_offset + 140, )))
    # shield panel meter
    repair_dependency(*(args + (b'mtib', tag_offset + 280)))
    # health panel background
    repair_hud_background(*(args + (tag_offset + 380, )))
    # health panel meter
    repair_dependency(*(args + (b'mtib', tag_offset + 520)))
    # motion sensor panel background
    repair_hud_background(*(args + (tag_offset + 620, )))
    # motion sensor panel foreground
    repair_hud_background(*(args + (tag_offset + 724, )))

    # auxilary overlay
    for moff in iter_reflexive_offs(map_data, tag_offset + 932 - magic, 132):
        repair_hud_background(*(args + (moff, )))

    # warning sounds
    for moff in iter_reflexive_offs(map_data, tag_offset + 960 - magic, 56):
        map_data.seek(moff - magic)
        if map_data.read(4) == b'dnsl':
            repair_dependency(*(args + (b'dnsl', moff)))
        else:
            repair_dependency(*(args + (b'!dns', moff)))

    # auxilary meter
    for moff in iter_reflexive_offs(map_data, tag_offset + 972 - magic, 324):
        repair_hud_background(*(args + (moff + 20, )))
        repair_dependency(*(args + (b'mtib', moff + 160)))


def repair_vcky(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'tnof', tag_offset)))
    repair_dependency(*(args + (b'mtib', tag_offset + 16)))
    repair_dependency(*(args + (b'rtsu', tag_offset + 32)))
    for moff in iter_reflexive_offs(map_data, tag_offset + 48 - magic, 80):
        repair_dependency_array(*(args + (b'mtib', moff + 16, 4)))


def repair_wphi(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'ihpw', tag_offset)))

    # static elements
    for moff in iter_reflexive_offs(map_data, tag_offset + 96 - magic, 180):
        repair_dependency(*(args + (b'mtib', moff + 72)))
        for moff2 in iter_reflexive_offs(map_data, moff + 124 - magic, 480):
            repair_dependency(*(args + (b'mtib', moff2 + 100)))
            repair_dependency(*(args + (b'mtib', moff2 + 116)))
            repair_dependency(*(args + (b'mtib', moff2 + 132)))

    # meter elements
    for moff in iter_reflexive_offs(map_data, tag_offset + 108 - magic, 180):
        repair_dependency(*(args + (b'mtib', moff + 72)))

    # crosshairs
    for moff in iter_reflexive_offs(map_data, tag_offset + 132 - magic, 104):
        repair_dependency(*(args + (b'mtib', moff + 36)))

    # overlay elements
    for moff in iter_reflexive_offs(map_data, tag_offset + 144 - magic, 104):
        repair_dependency(*(args + (b'mtib', moff + 36)))

    # screen effects
    for moff in iter_reflexive_offs(map_data, tag_offset + 172 - magic, 184):
        repair_dependency(*(args + (b'mtib', moff + 24)))
        repair_dependency(*(args + (b'mtib', moff + 40)))


# open-sauce repair functions
def repair_avtc(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    for moff in iter_reflexive_offs(map_data, tag_offset - magic, 52):
        repair_dependency(*(args + (b'vtca', moff)))

        for moff2 in iter_reflexive_offs(map_data, moff + 16 - magic, 116):
            repair_dependency(*(args + (b'otva', moff2 + 52)))
            repair_dependency(*(args + (b'itva', moff2 + 72)))


def repair_avti(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)
    for moff in iter_reflexive_offs(map_data, tag_offset - magic, 172):
        repair_dependency(*(args + (b'vtca', moff + 52)))

        for moff2 in iter_reflexive_offs(map_data, moff + 120 - magic, 72):
            repair_dependency(*(args + (b'!tpj', moff2 + 8)))
            repair_dependency(*(args + (b'effe', moff2 + 24)))


def repair_avto(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    for moff in iter_reflexive_offs(map_data, tag_offset - magic, 52):
        repair_dependency(*(args + (b'vtca', moff)))
        ct, moff2 = read_reflexive(map_data, moff + 16 - magic)

        for moff3 in iter_reflexive_offs(map_data, moff2 + 16 - magic, 116):
            repair_dependency(*(args + (b'otva', moff3 + 52)))
            repair_dependency(*(args + (b'itva', moff3 + 72)))


def repair_efpc(tag_id, index_array, map_data, magic, repair, engine):
    ct, moff = read_reflexive(
        map_data, index_array[tag_id].meta_offset + 24 - magic)
    repair_dependency_array(
        index_array, map_data, magic, repair, engine, b'gpfe', moff, ct, 72)


def repair_efpg(tag_id, index_array, map_data, magic, repair, engine):
    ct, moff = read_reflexive(
        map_data, index_array[tag_id].meta_offset + 60 - magic)
    repair_dependency_array(
        index_array, map_data, magic, repair, engine, b'gphs', moff, ct, 76)


def repair_gelc(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    for moff in iter_reflexive_offs(map_data, tag_offset + 4 - magic, 52):
        ct, moff2 = read_reflexive(map_data, moff + 4 - magic)
        repair_dependency_array(*(args + (b'tinu', moff2, ct)))

        for moff2 in iter_reflexive_offs(map_data, moff + 16 - magic, 144):
            repair_dependency(*(args + (b'tinu', moff2 + 0x4)))
            repair_dependency(*(args + (b'tinu', moff2 + 0x18)))
            repair_dependency(*(args + (b'vtca', moff2 + 0x28)))
            repair_dependency(*(args + (b'effe', moff2 + 0x38)))
            repair_dependency(*(args + (b'obje', moff2 + 0x48)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 16 - magic, 68):
        repair_dependency(*(args + (b'tinu', moff + 4)))

        ct, moff2 = read_reflexive(map_data, moff + 20 - magic)
        repair_dependency_array(*(args + (b'!tpj', moff2 + 72, ct)))


def repair_gelo(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'cgat', tag_offset + 0x28)))
    repair_dependency(*(args + (b'cleg', tag_offset + 0x38)))

    ct, moff = read_reflexive(map_data, tag_offset + 0x98 - magic)
    repair_dependency_array(*(args + (b'aLeD', moff + 32, ct, 76)))


def repair_magy(tag_id, index_array, map_data, magic, repair, engine):
    repair_antr(tag_id, index_array, map_data, magic, repair, engine)
    repair_dependency(index_array, map_data, magic, repair, engine,
                      b'rtna', index_array[tag_id].meta_offset + 0x80)


def repair_shpg(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset + 164
    args = (index_array, map_data, magic, repair, engine)
    repair_dependency(*(args + (b'gphs', moff + 4)))

    for moff in iter_reflexive_offs(map_data, tag_offset + 0x20 - magic, 0x74):
        repair_dependency(*(args + (b'mtib', moff + 0x64)))


def repair_shpp(tag_id, index_array, map_data, magic, repair, engine):
    repair_predicted_resources(
        map_data, index_array[tag_id].meta_offset + 120, magic, repair)


def repair_unic(tag_id, index_array, map_data, magic, repair, engine):
    ct, moff = read_reflexive(map_data, index_array[tag_id].meta_offset - magic)
    repair_dependency_array(index_array, map_data, magic, repair, engine,
                            b'ydis', moff, ct, 56)


def repair_yelo(tag_id, index_array, map_data, magic, repair, engine):
    tag_offset = index_array[tag_id].meta_offset
    args = (index_array, map_data, magic, repair, engine)

    repair_dependency(*(args + (b'oleg', tag_offset + 0x4)))
    repair_dependency(*(args + (b'gtam', tag_offset + 0x14)))
    repair_dependency(*(args + (b'cgat', tag_offset + 0x24)))

    ct, moff = read_reflexive(map_data, tag_offset + 0x68 - magic)
    repair_dependency_array(*(args + (b'aLeD', moff + 32, ct, 76)))


class_repair_functions = {
    "actv": repair_actv,
    "ant!": repair_ant_,
    "antr": repair_antr,
    "coll": repair_coll,
    "cont": repair_cont,
    "deca": repair_deca,
    "DeLa": repair_DeLa,
    "dobc": repair_dobc,
    "effe": repair_effe,
    "elec": repair_elec,
    "flag": repair_flag,
    "fog ": repair_fog,
    "font": repair_font,
    "foot": repair_foot,
    "glw!": repair_glw_,
    "grhi": repair_grhi,
    "hud#": repair_hud_,
    "hudg": repair_hudg,
    "itmc": repair_itmc,
    "jpt!": repair_jpt_,
    "lens": repair_lens,
    "ligh": repair_ligh,
    "lsnd": repair_lsnd,
    "matg": repair_matg,
    "mgs2": repair_mgs2,
    "mode": repair_mode,
    "mod2": repair_mode,
    "mply": repair_mply,
    "ngpr": repair_ngpr,
    "obje": repair_object,
    "part": repair_part,
    "pctl": repair_pctl,
    "rain": repair_rain,
    "sbsp": repair_sbsp,
    "scnr": repair_scnr,
    "shdr": repair_shader,
    "sky ": repair_sky,
    "snd!": repair_snd_,
    "Soul": repair_Soul,
    "tagc": repair_tagc,
    "udlg": repair_udlg,
    "unhi": repair_unhi,
    "vcky": repair_vcky,
    "wphi": repair_wphi,

    # subclass duplicates
    "bipd": repair_object,
    "vehi": repair_object,
    "weap": repair_object,
    "eqip": repair_object,
    "garb": repair_object,
    "proj": repair_object,
    "scen": repair_object,
    "mach": repair_object,
    "ctrl": repair_object,
    "lifi": repair_object,
    "plac": repair_object,
    "ssce": repair_object,

    "senv": repair_shader,
    "soso": repair_shader,
    "sotr": repair_shader,
    "schi": repair_shader,
    "scex": repair_shader,
    "swat": repair_shader,
    "sgla": repair_shader,
    "smet": repair_shader,
    "spla": repair_shader,

    # open sauce
    "avtc": repair_avtc,
    "avti": repair_avti,
    "avto": repair_avto,
    "efpc": repair_efpc,
    "efpg": repair_efpg,
    "gelc": repair_gelc,
    "gelo": repair_gelo,
    "magy": repair_magy,
    "shpg": repair_shpg,
    "shpp": repair_shpp,
    "unic": repair_unic,
    "yelo": repair_yelo
    }

# make a copy of the class_repair_functions, but have the
# functions indexed by the reversed fcc string as bytes
_class_repair_functions_by_bytes = {
    bytes(k[slice(None, None, -1)], "latin1"): class_repair_functions[k]
    for k in class_repair_functions}


class_bytes_by_fcc = {
    "senv": b'vnes' + b'rdhs' + NULL_CLASS,  # 3
    "soso": b'osos' + b'rdhs' + NULL_CLASS,  # 4
    "sotr": b'rtos' + b'rdhs' + NULL_CLASS,  # 5
    "schi": b'ihcs' + b'rdhs' + NULL_CLASS,  # 6
    "scex": b'xecs' + b'rdhs' + NULL_CLASS,  # 7
    "swat": b'taws' + b'rdhs' + NULL_CLASS,  # 8
    "sgla": b'algs' + b'rdhs' + NULL_CLASS,  # 9
    "smet": b'tems' + b'rdhs' + NULL_CLASS,  # 10
    "spla": b'alps' + b'rdhs' + NULL_CLASS,  # 11
    "shdr": b'rdhs' + NULL_CLASS + NULL_CLASS,  # -1

    "bipd": b'dpib' + b'tinu' + b'ejbo',  # 0
    "vehi": b'ihev' + b'tinu' + b'ejbo',  # 1
    "weap": b'paew' + b'meti' + b'ejbo',  # 2
    "eqip": b'piqe' + b'meti' + b'ejbo',  # 3
    "garb": b'brag' + b'meti' + b'ejbo',  # 4
    "proj": b'jorp' + b'ejbo' + NULL_CLASS,  # 5
    "scen": b'necs' + b'ejbo' + NULL_CLASS,  # 6
    "mach": b'hcam' + b'ejbo' + NULL_CLASS,  # 7
    "ctrl": b'lrtc' + b'ejbo' + NULL_CLASS,  # 8
    "lifi": b'ifil' + b'ived' + b'ejbo',  # 9
    "plac": b'calp' + b'ived' + b'ejbo',  # 10
    "ssce": b'ecss' + b'ived' + b'ejbo',  # 11
    "obje": b'ejbo' + NULL_CLASS + NULL_CLASS  # -1
    }

for cls in tag_class_be_int_to_fcc_os.values():
    if cls not in class_bytes_by_fcc:
        cls_1 = bytes(cls[slice(None, None, -1)], "latin1")
        cls_2 = cls_3 = NULL_CLASS
        if cls_1 == b'gpfe':
            cls_2 == b'ppfe'
        elif cls_1 == b'gphs':
            cls_2 == b'pphs'

        class_bytes_by_fcc[cls] = cls_1 + cls_2 + cls_3
