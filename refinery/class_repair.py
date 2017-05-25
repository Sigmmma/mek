from supyr_struct.defs.constants import *
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


# used to determine the shader/object class by
# getting its SInt16 at the start of its meta
shader_classes = (
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
    b'rdhs',  # -1 will get this
    )

object_classes = (
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
    b'ejbo',  # -1 will get this
    )


def read_reflexive(map_data, reflexive_offset, magic):
    '''
    Reads a reflexive from the given map_data at the given
    offset, and returns its size and non-magic pointer.
    '''
    map_data.seek(reflexive_offset)
    size    = int.from_bytes(map_data.read(4), "little")
    pointer = int.from_bytes(map_data.read(4), "little") - magic
    return size, pointer


def deprotect_dependency(map_data, index_array, repaired, magic,
                         bsp_magics, dependency_offset, base_class, engine):
    '''
    Reads a dependency from the map_data at the given offset, calls
    the deprotect function(if any) for that type of tag, changes its
    class to the exact one it needs to be one, adds the tag_id to the
    set of repaired tag_ids, and repairs its class in the tag_index.
    '''
    # get the tag_index id
    map_data.seek(dependency_offset + 12)
    tagid = int.from_bytes(map_data.read(2), "little")
    if tagid >= 0xFFFF or tagid >= len(index_array):
        # reference is invalid
        return

    repair_index_ref = tagid not in repaired
    repaired.add(tagid)

    deprotector = _class_repair_functions_by_bytes.get(base_class)
    if deprotector is None:
        class_1, class_2, class_3 = base_class, NULL_CLASS, NULL_CLASS
    else:
        # call the deprotect function for this dependency and
        # get the exact subclasses for the tag_index
        class_1, class_2, class_3 = deprotector(
            map_data, index_array, repaired, magic, tagid, engine)

    if repair_index_ref:
        # write the new class to the dependency
        map_data.seek(dependency_offset)
        map_data.write(exact_class)

        # change the class in the index_array
        index_array[tagid].class_1.data = int.from_bytes(class_1, 'little')
        index_array[tagid].class_2.data = int.from_bytes(class_2, 'little')
        index_array[tagid].class_3.data = int.from_bytes(class_3, 'little')


def deprotect_palette(map_data, index_array, repaired,
                      magic, bsp_magics, tagid, engine):
    '''Macro for deprotecting all palettes in a scenario'''
    pass


def deprotect_wphi_overlay(map_data, index_array, repaired,
                           magic, bsp_magics, tagid, engine):
    '''Macro for deprotecting all overlay structs in a wphi tag'''
    pass


def deprotect_multitex_overlay(map_data, index_array, repaired,
                               magic, bsp_magics, tagid, engine):
    '''Macro for deprotecting all multitex overlay structs in
    wphi, unhi, and grhi tags'''
    pass


def deprotect_dependency_array(map_data, index_array, repaired,
                               magic, bsp_magics, tagid, engine, base_class):
    '''Macro for deprotecting a contiguous array of dependencies'''
    pass


def repair_actv(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'vtca', NULL_CLASS, NULL_CLASS


def repair_ant(map_data, index_array, repaired,
               magic, bsp_magics, tagid, engine):
    return b' tna', NULL_CLASS, NULL_CLASS


def repair_antr(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'rtna', NULL_CLASS, NULL_CLASS


def repair_coll(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'lloc', NULL_CLASS, NULL_CLASS


def repair_cont(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'tnoc', NULL_CLASS, NULL_CLASS


def repair_deca(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'aced', NULL_CLASS, NULL_CLASS


def repair_DeLa(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'aLeD', NULL_CLASS, NULL_CLASS


def repair_effe(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'effe', NULL_CLASS, NULL_CLASS


def repair_flag(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'galf', NULL_CLASS, NULL_CLASS


def repair_fog(map_data, index_array, repaired,
               magic, bsp_magics, tagid, engine):
    return b' gof', NULL_CLASS, NULL_CLASS


def repair_font(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'vtca', NULL_CLASS, NULL_CLASS


def repair_foot(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'toof', NULL_CLASS, NULL_CLASS


def repair_grhi(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'ihrg', NULL_CLASS, NULL_CLASS


def repair_hud_number(map_data, index_array, repaired,
                      magic, bsp_magics, tagid, engine):
    return b'#duh', NULL_CLASS, NULL_CLASS


def repair_hudg(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'gduh', NULL_CLASS, NULL_CLASS


def repair_itmc(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'cmti', NULL_CLASS, NULL_CLASS


def repair_jpt(map_data, index_array, repaired,
               magic, bsp_magics, tagid, engine):
    return b'!tpj', NULL_CLASS, NULL_CLASS


def repair_lens(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'snel', NULL_CLASS, NULL_CLASS


def repair_ligh(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'hgil', NULL_CLASS, NULL_CLASS


def repair_lsnd(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'dnsl', NULL_CLASS, NULL_CLASS


def repair_matg(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'gtam', NULL_CLASS, NULL_CLASS


def repair_metr(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'rtem', NULL_CLASS, NULL_CLASS


def repair_mode(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'edom', NULL_CLASS, NULL_CLASS


def repair_mod2(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'2dom', NULL_CLASS, NULL_CLASS


def repair_object(map_data, index_array, repaired,
                  magic, bsp_magics, tagid, engine):
    class_1 = object_classes[object_type]
    class_2 = class_3 = NULL_CLASS

    if class_1 in (b'ihev', b'dpib'):
        class_2 = b'tinu'
        class_3 = b'ejbo'
    elif class_1 in (b'paew', b'piqe', b'brag'):
        class_2 = b'meti'
        class_3 = b'ejbo'
    elif class_1 in (b'hcam', b'lrtc', b'ifil'):
        class_2 = b'ived'
        class_3 = b'ejbo'
    elif class_1 in (b'jorp', b'necs', b'calp', b'ecss'):
        class_2 = b'ejbo'

    return class_1, class_2, class_3


def repair_part(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'trap', NULL_CLASS, NULL_CLASS


def repair_pctl(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'ltcp', NULL_CLASS, NULL_CLASS


def repair_rain(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'niar', NULL_CLASS, NULL_CLASS


def repair_sbsp(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'psbs', NULL_CLASS, NULL_CLASS


def repair_scnr(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'rncs', NULL_CLASS, NULL_CLASS


def repair_shader(map_data, index_array, repaired,
                  magic, bsp_magics, tagid, engine):
    shader_class = shader_classes[shader_type]

    if shader_class == b'rdhs':
        return b'rdhs', NULL_CLASS, NULL_CLASS
    else:
        return shader_class, b'rdhs', NULL_CLASS


def repair_sky(map_data, index_array, repaired,
               magic, bsp_magics, tagid, engine):
    return b' yks', NULL_CLASS, NULL_CLASS


def repair_Soul(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'luoS', NULL_CLASS, NULL_CLASS


def repair_tagc(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'cgat', NULL_CLASS, NULL_CLASS


def repair_unhi(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'ihnu', NULL_CLASS, NULL_CLASS


def repair_wphi(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'ihpw', NULL_CLASS, NULL_CLASS


# open-sauce repair functions
def repair_avtc(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'ctva', NULL_CLASS, NULL_CLASS


def repair_avti(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'itva', NULL_CLASS, NULL_CLASS


def repair_avto(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'otva', NULL_CLASS, NULL_CLASS


def repair_efpc(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'cpfe', NULL_CLASS, NULL_CLASS


def repair_efpg(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'gpfe', b'ppfe', NULL_CLASS


def repair_gelc(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'', NULL_CLASS, NULL_CLASS


def repair_gelo(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'oleg', NULL_CLASS, NULL_CLASS


def repair_magy(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'ygam', NULL_CLASS, NULL_CLASS


def repair_shpg(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'gphs', b'pphs', NULL_CLASS


def repair_tag_database(map_data, index_array, repaired,
                        magic, bsp_magics, tagid, engine):
    return b'+gat', NULL_CLASS, NULL_CLASS


def repair_udlg(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'gldu', NULL_CLASS, NULL_CLASS


def repair_unic(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'cinu', NULL_CLASS, NULL_CLASS


def repair_yelo(map_data, index_array, repaired,
                magic, bsp_magics, tagid, engine):
    return b'oley', NULL_CLASS, NULL_CLASS


class_repair_functions = {
    "actv": repair_actv,
    "ant ": repair_ant,
    "antr": repair_antr,
    "coll": repair_coll,
    "cont": repair_cont,
    "deca": repair_deca,
    "DeLa": repair_DeLa,
    "effe": repair_effe,
    "flag": repair_flag,
    "fog ": repair_fog,
    "font": repair_font,
    "foot": repair_foot,
    "grhi": repair_grhi,
    "hud#": repair_hud_number,
    "hudg": repair_hudg,
    "itmc": repair_itmc,
    "jpt!": repair_jpt,
    "lens": repair_lens,
    "ligh": repair_ligh,
    "lsnd": repair_lsnd,
    "matg": repair_matg,
    "metr": repair_metr,
    "mode": repair_mode,
    "mod2": repair_mod2,
    "obje": repair_object,
    "part": repair_part,
    "pctl": repair_pctl,
    "rain": repair_rain,
    "sbsp": repair_sbsp,
    "scnr": repair_scnr,
    "shdr": repair_shader,
    "sky ": repair_sky,
    "Soul": repair_Soul,
    "tagc": repair_tagc,
    "udlg": repair_udlg,
    "unhi": repair_unhi,
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
    "tag+": repair_tag_database,
    "unic": repair_unic,
    "yelo": repair_yelo
    }

# make a copy of the class_repair_functions, but have the
# functions indexed by the reversed fcc string as bytes
_class_repair_functions_by_bytes = {
    bytes(k[slice(None, None, -1)], "latin1"): class_repair_functions[k]
    for k in class_repair_functions}
