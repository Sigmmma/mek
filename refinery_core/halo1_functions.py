from math import pi, sqrt
from struct import unpack, pack_into
from traceback import format_exc

from supyr_struct.buffer import BytearrayBuffer
from supyr_struct.defs.constants import *
from supyr_struct.defs.util import *
from supyr_struct.field_types import FieldType

from .byteswapping import raw_block_def, byteswap_animation,\
     byteswap_uncomp_verts, byteswap_comp_verts, byteswap_tris,\
     byteswap_coll_bsp, byteswap_sbsp_meta, byteswap_scnr_script_syntax_data


def inject_rawdata(self, meta, tag_cls, tag_index_ref):
    magic  = self.map_magic
    engine = self.engine

    map_data    = self.map_data
    bitmap_data = self.bitmap_data
    sound_data  = self.sound_data
    loc_data    = self.loc_data
    is_not_indexed = not self.is_indexed(tag_index_ref)

    # get some rawdata that would be pretty annoying to do in the parser
    if tag_cls == "bitm":
        # grab bitmap data correctly from map
        new_pixels = BytearrayBuffer()
        pixel_data = map_data
        can_be_indexed = engine not in ("stubbs", "stubbspc", "halo1xbox")

        # uncheck the prefer_low_detail flag, get the pixel data
        # from the map, and set up the pixels_offset correctly.
        for bitmap in meta.bitmaps.STEPTREE:
            pixel_data = map_data
            if can_be_indexed and bitmap.flags.data_in_resource_map:
                pixel_data = bitmap_data

            # grab the bitmap data from this map(no magic used)
            pixel_data.seek(bitmap.pixels_offset)
            new_pixels += pixel_data.read(bitmap.pixels_meta_size)

        meta.processed_pixel_data.STEPTREE = new_pixels

    elif tag_cls == "font":
        # might need to grab pixel data correctly from resource map
        meta_offset = tag_index_ref.meta_offset

        if is_not_indexed:
            return meta
        elif not self.map_is_resource:
            meta_offset = self.loc_rsrc_header.tag_headers\
                          [meta_offset].offset

        loc_data.seek(meta.pixels.pointer + meta_offset)
        meta.pixels.data = loc_data.read(meta.pixels.size)

    elif tag_cls == "hmt ":
        # might need to grab string data correctly from resource map
        meta_offset = tag_index_ref.meta_offset

        if is_not_indexed:
            return meta
        elif not self.map_is_resource:
            meta_offset = self.loc_rsrc_header.tag_headers\
                          [meta_offset].offset

        b = meta.string
        loc_data.seek(b.pointer + meta_offset)
        meta.string.data = loc_data.read(b.size).decode('utf-16-le')

    elif tag_cls == "snd!":
        # might need to get samples and permutations from the resource map
        is_pc = engine in ("halo1pc", "halo1pcdemo")
        is_ce = engine in ("halo1ce", "halo1yelo")
        if not (is_pc or is_ce):
            return meta

        # ce tagpaths are in the format:  path__permutations
        #     ex: sound\sfx\impulse\coolant\enter_water__permutations
        #
        # pc tagpaths are in the format:  path__pitch_range__permutation
        #     ex: sound\sfx\impulse\coolant\enter_water__0__0

        # why do ce and pc have to store shit so differently.
        # it was really annoying to figure out the differences
        other_data = sound_data
        if is_pc:
            sound_magic = 0 - magic
            other_data = map_data
        elif not self.map_is_resource:
            sound_map = self.ce_sound_offsets_by_path
            tag_path  = tag_index_ref.tag.tag_path
            if sound_map is None or tag_path not in sound_map:
                return
            sound_magic = sound_map[tag_path] + meta.get_size()
        else:
            sound_magic = tag_index_ref.meta_offset + meta.get_size()

        for pitches in meta.pitch_ranges.STEPTREE:
            for perm in pitches.permutations.STEPTREE:
                samples = perm.samples
                mouth_data = perm.mouth_data
                subtitle_data = perm.subtitle_data

                if is_ce and not samples.flags.data_in_resource_map:
                    continue

                if samples.size:
                    sound_data.seek(samples.raw_pointer)
                    samples.data = sound_data.read(samples.size)
                else:
                    samples.data = b''

                if mouth_data.size:
                    other_data.seek(mouth_data.pointer + sound_magic)
                    mouth_data.data = other_data.read(mouth_data.size)
                else:
                    mouth_data.data = b''

                if subtitle_data.size:
                    other_data.seek(subtitle_data.pointer + sound_magic)
                    subtitle_data.data = other_data.read(subtitle_data.size)
                else:
                    subtitle_data.data = b''

    elif tag_cls == "ustr":
        # might need to grab string data correctly from resource map
        meta_offset = tag_index_ref.meta_offset

        if is_not_indexed:
            return meta
        elif not self.map_is_resource:
            meta_offset = self.loc_rsrc_header.tag_headers\
                          [meta_offset].offset

        string_blocks = meta.strings.STEPTREE

        if len(string_blocks):
            desc = string_blocks[0].get_desc('STEPTREE')
            parser = desc['TYPE'].parser

        try:
            FieldType.force_little()
            for b in string_blocks:
                parser(desc, None, b, 'STEPTREE',
                       loc_data, meta_offset, b.pointer)
            FieldType.force_normal()
        except Exception:
            print(format_exc())
            FieldType.force_normal()
            raise


def meta_to_tag_data(self, meta, tag_cls, tag_index_ref):
    magic     = self.map_magic
    engine    = self.engine
    map_data  = self.map_data
    tag_index = self.tag_index

    predicted_resources = []

    if hasattr(meta, "obje_attrs"):
        predicted_resources.append(meta.obje_attrs.predicted_resources)


    if tag_cls == "actv":
        # multiply grenade velocity by 30
        meta.grenades.grenade_velocity *= 30
        
    elif tag_cls in ("antr", "magy"):
        # byteswap animation data
        for anim in meta.animations.STEPTREE:
            byteswap_animation(anim)

    elif tag_cls == "bitm":
        # set the size of the compressed plate data to nothing
        meta.compressed_color_plate_data.STEPTREE = BytearrayBuffer()

        # to enable compatibility with my bitmap converter we'll set the
        # base address to a certain constant based on the console platform
        if engine in ("halo1xbox", "stubbs"):
            for bitmap in meta.bitmaps.STEPTREE:
                bitmap.base_address = 1073751810
        else:
            for bitmap in meta.bitmaps.STEPTREE:
                bitmap.base_address = 0

        is_xbox = "xbox" in engine or engine == "stubbs"
        new_pixels_offset = 0

        # uncheck the prefer_low_detail flag and
        # set up the pixels_offset correctly.
        for bitmap in meta.bitmaps.STEPTREE:
            bitmap.flags.prefer_low_detail = is_xbox
            bitmap.pixels_offset = new_pixels_offset
            new_pixels_offset += bitmap.pixels_meta_size

            # clear some meta-only fields
            bitmap.pixels_meta_size = 0
            bitmap.bitmap_id_unknown1 = bitmap.bitmap_id_unknown2 = 0
            bitmap.bitmap_data_pointer = bitmap.base_address = 0

    elif tag_cls == "cdmg":
        # divide camera shaking wobble period by 30
        meta.camera_shaking.wobble_function_period /= 30

    elif tag_cls == "coll":
        # byteswap the raw bsp collision data
        for node in meta.nodes.STEPTREE:
            for perm_bsp in node.bsps.STEPTREE:
                byteswap_coll_bsp(perm_bsp)

    elif tag_cls == "effe":
        # mask away the meta-only flags
        meta.flags.data &= 3

    elif tag_cls == "jpt!":
        # camera shaking wobble period by 30
        meta.camera_shaking.wobble_function_period /= 30

    elif tag_cls == "glw!":
        # increment enumerators properly
        for b in (meta.particle_rotational_velocity,
                  meta.effect_rotational_velocity,
                  meta.effect_translational_velocity,
                  meta.particle_distance_to_object,
                  meta.particle_size,
                  meta.particle_color):
            b.attachment.data += 1

    elif tag_cls == "lens":
        # multiply corona rotation by pi/180
        meta.corona_rotation.function_scale *= pi/180

    elif tag_cls == "ligh":
        # divide light time by 30
        meta.effect_parameters.duration /= 30

    elif tag_cls == "matg":
        # tool will fail to compile any maps if the
        # multiplayer_info or falling_damage is blank

        # make sure there is multiplayer info.
        multiplayer_info = meta.multiplayer_informations.STEPTREE
        if not len(multiplayer_info):
            multiplayer_info.append()

        # make sure there is falling damage info.
        falling_damages = meta.falling_damages.STEPTREE
        if not len(falling_damages):
            falling_damages.append()

    elif tag_cls == "metr":
        # The meter bitmaps can literally point to not
        # only the wrong tag, but the wrong TYPE of tag.
        # Since dependencies in meter tags are useless, we null them out.
        meta.stencil_bitmap.filepath = meta.source_bitmap.filepath = ''

    elif tag_cls in ("mode", "mod2"):
        if engine in ("halo1yelo", "halo1ce", "halo1pc", "halo1pcdemo",
                      "stubbspc"):
            # model_magic seems to be the same for all pc maps
            # need to figure out what that magic is though.........
            verts_start = tag_index.model_data_offset
            tris_start  = verts_start + tag_index.vertex_data_size
            model_magic = None
        else:
            model_magic = magic

        # grab vertices and indices from the map
        if model_magic is None:
            verts_attr_name = "uncompressed_vertices"
            byteswap_verts = byteswap_uncomp_verts
            vert_size = 68

            if engine != "stubbspc":
                # need to swap the lod cutoff and nodes values around
                cutoffs = (meta.superlow_lod_cutoff, meta.low_lod_cutoff,
                           meta.high_lod_cutoff, meta.superhigh_lod_cutoff)
                nodes = (meta.superlow_lod_nodes, meta.low_lod_nodes,
                         meta.high_lod_nodes, meta.superhigh_lod_nodes)
                meta.superlow_lod_cutoff  = cutoffs[3]
                meta.low_lod_cutoff       = cutoffs[2]
                meta.high_lod_cutoff      = cutoffs[1]
                meta.superhigh_lod_cutoff = cutoffs[0]
                meta.superlow_lod_nodes  = nodes[3]
                meta.low_lod_nodes       = nodes[2]
                meta.high_lod_nodes      = nodes[1]
                meta.superhigh_lod_nodes = nodes[0]
        else:
            verts_attr_name = "compressed_vertices"
            byteswap_verts = byteswap_comp_verts
            vert_size = 32

        for geom in meta.geometries.STEPTREE:
            for part in geom.parts.STEPTREE:
                verts_block = part[verts_attr_name]
                tris_block  = part.triangles
                info  = part.model_meta_info

                # null out certain things in the part
                part.previous_part_index = part.next_part_index = 0
                part.centroid_primary_node = 0
                part.centroid_secondary_node = 0
                part.centroid_primary_weight = 0.0
                part.centroid_secondary_weight = 0.0

                # make the new blocks to hold the raw data
                verts_block.STEPTREE = raw_block_def.build()
                tris_block.STEPTREE  = raw_block_def.build()

                # read the offsets of the vertices and indices from the map
                if model_magic is None:
                    verts_off = verts_start + info.vertices_offset
                    tris_off  = tris_start  + info.indices_offset
                else:
                    map_data.seek(
                        info.vertices_reflexive_offset + 4 - model_magic)
                    verts_off = unpack(
                        "<I", map_data.read(4))[0] - model_magic
                    map_data.seek(
                        info.indices_reflexive_offset  + 4 - model_magic)
                    tris_off  = unpack(
                        "<I", map_data.read(4))[0] - model_magic

                # read the raw data from the map
                map_data.seek(verts_off)
                raw_verts = map_data.read(vert_size*info.vertex_count)
                map_data.seek(tris_off)
                raw_tris  = map_data.read(2*(info.index_count + 3))

                # put the raw data in the verts and tris blocks
                verts_block.STEPTREE.data = raw_verts
                tris_block.STEPTREE.data  = raw_tris

                # call the byteswappers
                byteswap_verts(verts_block)
                byteswap_tris(tris_block)

                # null out the model_meta_info
                info.index_type.data  = info.index_count  = 0
                info.vertex_type.data = info.vertex_count = 0
                info.indices_offset = info.vertices_offset  = 0
                if model_magic is None:
                    info.indices_magic_offset  = 0
                    info.vertices_magic_offset = 0
                else:
                    info.indices_reflexive_offset  = 0
                    info.vertices_reflexive_offset = 0

    elif tag_cls == "pphy":
        # set the meta-only values to 0
        meta.wind_coefficient = 0
        meta.wind_sine_modifier = 0
        meta.z_translation_rate = 0

        # scale friction values
        meta.air_friction /= 10000
        meta.water_friction /= 10000

    elif tag_cls == "proj":
        # need to scale velocities by 30
        meta.proj_attrs.physics.initial_velocity *= 30
        meta.proj_attrs.physics.final_velocity *= 30

    elif tag_cls == "sbsp":
        byteswap_sbsp_meta(meta)

        # null out the runtime decals
        del meta.runtime_decals.STEPTREE[:]

        for cluster in meta.clusters.STEPTREE:
            predicted_resources.append(cluster.predicted_resources)

        compressed = engine in ("halo1xbox", "stubbs")

        # local variables for faster access
        s_unpack = unpack
        s_pack_into = pack_into

        # make sure the compressed and uncompressed lightmap vertices
        # are padded with 0x00 up to the size they need to be
        for lightmap in meta.lightmaps.STEPTREE:
            for b in lightmap.materials.STEPTREE:
                vert_count = b.vertices_count
                lightmap_vert_count = b.lightmap_vertices_count

                u_verts = b.uncompressed_vertices
                c_verts = b.compressed_vertices

                if compressed:
                    # generate uncompressed vertices from the compressed
                    comp_buffer   = c_verts.STEPTREE
                    uncomp_buffer = bytearray(56*vert_count +
                                              20*lightmap_vert_count)
                    in_off  = 0
                    out_off = 0
                    for i in range(vert_count):
                        n, b, t = s_unpack("<3I",
                            comp_buffer[in_off + 12: in_off + 24])
                        ni = n&2047; nj = (n>>11)&2047; nk = (n>>22)&1023
                        bi = b&2047; bj = (b>>11)&2047; bk = (b>>22)&1023
                        ti = t&2047; tj = (t>>11)&2047; tk = (t>>22)&1023
                        if ni&1024: ni = -1*((~ni) & 2047)
                        if nj&1024: nj = -1*((~nj) & 2047)
                        if nk&512:  nk = -1*((~nk) & 1023)
                        if bi&1024: bi = -1*((~bi) & 2047)
                        if bj&1024: bj = -1*((~bj) & 2047)
                        if bk&512:  bk = -1*((~bk) & 1023)
                        if ti&1024: ti = -1*((~ti) & 2047)
                        if tj&1024: tj = -1*((~tj) & 2047)
                        if tk&512:  tk = -1*((~tk) & 1023)
                        ni /= 1023; nj /= 1023; nk /= 511
                        bi /= 1023; bj /= 1023; bk /= 511
                        ti /= 1023; tj /= 1023; tk /= 511

                        nmag = max(sqrt(ni**2 + nj**2 + nk**2), 0.00000001)
                        bmag = max(sqrt(bi**2 + bj**2 + bk**2), 0.00000001)
                        tmag = max(sqrt(ti**2 + tj**2 + tk**2), 0.00000001)
                        
                        # write the uncompressed data
                        s_pack_into('<12s9f8s', uncomp_buffer, out_off,
                                    comp_buffer[in_off: in_off + 12],
                                    ni/nmag, nj/nmag, nk/nmag,
                                    bi/bmag, bj/bmag, bk/bmag,
                                    ti/tmag, tj/tmag, tk/tmag,
                                    comp_buffer[in_off + 24: in_off + 32])

                        in_off  += 32
                        out_off += 56

                    for i in range(lightmap_vert_count):
                        n, u, v = s_unpack(
                            "<I2h", comp_buffer[in_off: in_off + 8])
                        ni = n&2047; nj = (n>>11)&2047; nk = (n>>22)&1023
                        if ni&1024: ni = -1*((~ni) & 2047)
                        if nj&1024: nj = -1*((~nj) & 2047)
                        if nk&512:  nk = -1*((~nk) & 1023)
                        ni /= 1023; nj /= 1023; nk /= 511

                        mag = max(sqrt(ni**2 + nj**2 + nk**2), 0.00000001)

                        # write the uncompressed data
                        s_pack_into('<5f', uncomp_buffer, out_off,
                                    ni/mag, nj/mag, nk/mag,
                                    u/32767, v/32767)

                        in_off  += 8
                        out_off += 20
                else:
                    # generate compressed vertices from uncompressed
                    uncomp_buffer = u_verts.STEPTREE
                    comp_buffer   = bytearray(32*vert_count +
                                              8*lightmap_vert_count)

                # replace the buffers
                u_verts.STEPTREE = uncomp_buffer
                c_verts.STEPTREE = comp_buffer

    elif tag_cls == "scnr":
        # need to remove the references to the child scenarios
        del meta.child_scenarios.STEPTREE[:]

        # set the bsp pointers and stuff to 0
        for b in meta.structure_bsps.STEPTREE:
            b.bsp_pointer = b.bsp_size = b.bsp_magic = 0

        predicted_resources.append(meta.predicted_resources)

        # byteswap the script syntax data
        byteswap_scnr_script_syntax_data(meta)

        # rename duplicate stuff that causes errors when compiling scripts
        if self.rename_duplicates_in_scnr.get():
            for refl in (meta.cutscene_flags, meta.cutscene_camera_points,
                         meta.recorded_animations):
                names = set()
                blocks = refl.STEPTREE
                # go through the array in reverse so the last name is
                # considered the actual name and all others are renamed
                for i in range(len(blocks) -1, -1, -1):
                    j = 0
                    b = blocks[i]
                    name = orig_name = b.name
                    while name in names:
                        name = ("DUP_%s_%s" % (j, orig_name))[:31]
                        j += 1
                    b.name = name
                    names.add(name)

        # divide the cutscene times by 30(they're in ticks)
        for b in meta.cutscene_titles.STEPTREE:
            b.fade_in_time /= 30
            b.up_time /= 30
            b.fade_out_time /= 30

    elif tag_cls == "shpp":
        predicted_resources.append(meta.predicted_resources)

    elif tag_cls == "weap":
        predicted_resources.append(meta.weap_attrs.predicted_resources)

    # remove any predicted resources
    for pr in predicted_resources:
        del pr.STEPTREE[:]

    return meta
