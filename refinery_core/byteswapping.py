'''
Most byteswapping is handeled by supyr_struct by changing the endianness,
but certain chunks of raw data are significantly faster to just write
byteswapping routines for, like raw vertex, triangle, and animation data.
'''

from supyr_struct.field_types import BytearrayRaw
from supyr_struct.defs.block_def import BlockDef

raw_block_def = BlockDef("raw_block",
    BytearrayRaw('data',
        SIZE=lambda node, *a, **kw: 0 if node is None else len(node))
    )


def byteswap_raw_reflexive(refl):
    desc = refl.desc
    struct_size, two_byte_offs, four_byte_offs = desc.get(
        "RAW_REFLEXIVE_INFO", (0, (), ()))
    if not two_byte_offs and not four_byte_offs:
        return

    data = refl.STEPTREE
    refl.STEPTREE = swapped = bytearray(data)

    for refl_off in range(0, refl.size*struct_size, struct_size):
        for tmp_off in two_byte_offs:
            tmp_off += refl_off
            swapped[tmp_off]   = data[tmp_off+1]
            swapped[tmp_off+1] = data[tmp_off]

        for tmp_off in four_byte_offs:
            tmp_off += refl_off
            swapped[tmp_off]   = data[tmp_off+3]
            swapped[tmp_off+1] = data[tmp_off+2]
            swapped[tmp_off+2] = data[tmp_off+1]
            swapped[tmp_off+3] = data[tmp_off]


def byteswap_coll_bsp(bsp):
    for b in bsp:
        byteswap_raw_reflexive(b)


def byteswap_pcm16_samples(pcm_block):
    data = pcm_block.STEPTREE

    # replace the verts with the byteswapped ones
    pcm_block.STEPTREE = new_data = bytearray(len(data))
    for i in range(0, len(data), 2):
        new_data[i]     = data[i + 1]
        new_data[i + 1] = data[i]


def byteswap_sbsp_meta(meta):
    if len(meta.collision_bsp.STEPTREE):
        for b in meta.collision_bsp.STEPTREE[0]:
            byteswap_raw_reflexive(b)

    # do NOT need to swap meta.nodes since they are always little endian
    for b in (meta.leaves, meta.leaf_surfaces, meta.surface,
              meta.lens_flare_markers, meta.breakable_surfaces, meta.markers):
        byteswap_raw_reflexive(b)


def byteswap_scnr_script_syntax_data(meta):
    syntax_data = meta.script_syntax_data.data
    swapped = bytearray(syntax_data)
    # swap the 56 byte header
    # first 32 bytes are a string
    for i in (32, 34, 38, 44, 46, 48, 50):
        # swap the Int16's
        swapped[i]   = syntax_data[i+1]
        swapped[i+1] = syntax_data[i]

    for i in (40, 52):
        # swap the Int32's
        swapped[i]   = syntax_data[i+3]
        swapped[i+1] = syntax_data[i+2]
        swapped[i+2] = syntax_data[i+1]
        swapped[i+3] = syntax_data[i]

    # swap the 20 byte blocks
    for i in range(56, len(swapped), 20):
        # swap the Int16's
        swapped[i]   = syntax_data[i+1]; swapped[i+1] = syntax_data[i]
        swapped[i+2] = syntax_data[i+3]; swapped[i+3] = syntax_data[i+2]
        swapped[i+4] = syntax_data[i+5]; swapped[i+5] = syntax_data[i+4]
        swapped[i+6] = syntax_data[i+7]; swapped[i+7] = syntax_data[i+6]

        # swap the Int32's
        swapped[i+8]  = syntax_data[i+11]
        swapped[i+9]  = syntax_data[i+10]
        swapped[i+10] = syntax_data[i+9]
        swapped[i+11] = syntax_data[i+8]

        swapped[i+12] = syntax_data[i+15]
        swapped[i+13] = syntax_data[i+14]
        swapped[i+14] = syntax_data[i+13]
        swapped[i+15] = syntax_data[i+12]

        swapped[i+16] = syntax_data[i+19]
        swapped[i+17] = syntax_data[i+18]
        swapped[i+18] = syntax_data[i+17]
        swapped[i+19] = syntax_data[i+16]

    meta.script_syntax_data.data = swapped


def byteswap_uncomp_verts(verts_block):
    raw_block = verts_block.STEPTREE
    raw_data  = raw_block.data

    # replace the verts with the byteswapped and trimmed ones
    raw_block.data = new_raw = bytearray(68*(len(raw_data)//68))
    four_byte_field_offs = (0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44,
                            48, 52, 60, 64)
    # byteswap each of the floats, ints, and shorts
    for i in range(0, len(new_raw), 68):
        # byteswap the position floats and lighting vectors
        for j in four_byte_field_offs:
            j += i
            new_raw[j] = raw_data[j+3]
            new_raw[j+1] = raw_data[j+2]
            new_raw[j+2] = raw_data[j+1]
            new_raw[j+3] = raw_data[j]
        # byteswap the node indices
        new_raw[i+56] = raw_data[i+57]
        new_raw[i+57] = raw_data[i+56]
        new_raw[i+58] = raw_data[i+59]
        new_raw[i+59] = raw_data[i+58]

    # set the size of the reflexive
    verts_block.size = len(new_raw)//68


def byteswap_comp_verts(verts_block):
    raw_block = verts_block.STEPTREE
    raw_data  = raw_block.data

    # replace the verts with the byteswapped and trimmed ones
    raw_block.data = new_raw = bytearray(32*(len(raw_data)//32))
    four_byte_field_offs = (0, 4, 8, 12, 16, 20)
    # byteswap each of the floats, ints, and shorts
    for i in range(0, len(new_raw), 32):
        # byteswap the position floats and lighting vectors
        for j in four_byte_field_offs:
            j += i
            new_raw[j] = raw_data[j+3]
            new_raw[j+1] = raw_data[j+2]
            new_raw[j+2] = raw_data[j+1]
            new_raw[j+3] = raw_data[j]
        # byteswap the texture coordinates
        new_raw[i+24] = raw_data[i+25]
        new_raw[i+25] = raw_data[i+24]
        new_raw[i+26] = raw_data[i+27]
        new_raw[i+27] = raw_data[i+26]
        # copy over the node indices
        new_raw[i+28] = raw_data[i+28]
        new_raw[i+29] = raw_data[i+29]
        # byteswap the node weight
        new_raw[i+30] = raw_data[i+31]
        new_raw[i+31] = raw_data[i+30]

    # set the size of the reflexive
    verts_block.size = len(new_raw)//32


def byteswap_tris(tris_block):
    raw_block = tris_block.STEPTREE
    raw_data  = raw_block.data

    if len(raw_data)%6 == 4:
        raw_data += b'\xff\xff'

    # replace the verts with the byteswapped and trimmed ones
    raw_block.data = new_raw = bytearray(6*(len(raw_data)//6))
    # byteswap each of the shorts
    for i in range(0, len(new_raw), 2):
        new_raw[i] = raw_data[i+1]
        new_raw[i+1] = raw_data[i]

    # set the size of the reflexive
    tris_block.size = len(new_raw)//6


def byteswap_animation(anim):
    frame_info   = anim.frame_info.STEPTREE
    default_data = anim.default_data.STEPTREE
    frame_data   = anim.frame_data.STEPTREE

    comp_data_offset = anim.offset_to_compressed_data
    frame_count = anim.frame_count
    node_count  = anim.node_count
    uncomp_size = anim.frame_size * frame_count
    trans_flags = anim.trans_flags0 + (anim.trans_flags1<<32)
    rot_flags   = anim.rot_flags0   + (anim.rot_flags1  <<32)
    scale_flags = anim.scale_flags0 + (anim.scale_flags1<<32)

    default_data_size = 0
    for n in range(node_count):
        if not rot_flags   & (1<<n): default_data_size += 8
        if not trans_flags & (1<<n): default_data_size += 12
        if not scale_flags & (1<<n): default_data_size += 4

    new_frame_info   = bytearray(len(frame_info))
    new_default_data = bytearray(default_data_size)

    # some tags actually have the offset as non-zero in meta form
    # and it actually matters, so we need to take this into account
    new_uncomp_frame_data = bytearray(uncomp_size)

    # byteswap the frame info
    for i in range(0, len(frame_info), 4):
        new_frame_info[i]   = frame_info[i+3]
        new_frame_info[i+1] = frame_info[i+2]
        new_frame_info[i+2] = frame_info[i+1]
        new_frame_info[i+3] = frame_info[i]

    if default_data:
        i = 0
        swap = new_default_data
        raw = default_data
        # byteswap the default_data
        for n in range(node_count):
            if not rot_flags & (1<<n):
                for j in range(0, 8, 2):
                    swap[i] = raw[i+1]; swap[i+1] = raw[i]
                    i += 2

            if not trans_flags & (1<<n):
                for j in range(0, 12, 4):
                    swap[i] = raw[i+3];   swap[i+1] = raw[i+2]
                    swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                    i += 4

            if not scale_flags & (1<<n):
                swap[i] = raw[i+3]; swap[i+1] = raw[i+2]
                swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                i += 4

    if not anim.flags.compressed_data or comp_data_offset:
        i = 0
        swap = new_uncomp_frame_data
        raw = frame_data
        # byteswap the frame_data
        for f in range(frame_count):
            for n in range(node_count):
                if rot_flags & (1<<n):
                    for j in range(0, 8, 2):
                        swap[i] = raw[i+1]; swap[i+1] = raw[i]
                        i += 2

                if trans_flags & (1<<n):
                    for j in range(0, 12, 4):
                        swap[i] = raw[i+3];   swap[i+1] = raw[i+2]
                        swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                        i += 4

                if scale_flags & (1<<n):
                    swap[i] = raw[i+3];   swap[i+1] = raw[i+2]
                    swap[i+2] = raw[i+1]; swap[i+3] = raw[i]
                    i += 4

    anim.frame_info.STEPTREE   = new_frame_info
    anim.default_data.STEPTREE = new_default_data
    anim.frame_data.STEPTREE   = new_uncomp_frame_data
    anim.offset_to_compressed_data = 0
    
    if anim.flags.compressed_data:
        anim.offset_to_compressed_data = len(new_uncomp_frame_data)
        anim.frame_data.STEPTREE += frame_data[comp_data_offset:]
