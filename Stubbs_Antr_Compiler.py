import os, struct, supyr_struct

from struct import unpack, pack_into
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory, askopenfilename
from traceback import format_exc

from supyr_struct.field_types import FieldType
from supyr_struct.defs.constants import fcc, PATHDIV
from supyr_struct.defs.block_def import BlockDef
from reclaimer.halo.hek.defs.antr import antr_def
from reclaimer.halo.constants import PC_TAG_INDEX_HEADER_SIZE, XBOX_TAG_INDEX_HEADER_SIZE

force_little = FieldType.force_little
force_normal = FieldType.force_normal

UNIT_WEAP_PAD = b'\x00'*32
PATHDIV = PATHDIV
curr_dir = os.path.abspath(os.curdir) + PATHDIV

def get_int(rawdata, off):
    return unpack("<i", rawdata[off:off+4])[0]

def slice_out(rawdata, off, size):
    if not size:
        return rawdata
    return rawdata[:off] + rawdata[off+size:]

def remove_pad2(rawdata, off, ct):
    if (2-(ct)%2)%2:
        return rawdata[:off] + rawdata[off+2:]
    return rawdata

def clean_antr_meta(meta):
    '''
    Removes stubbs specific fields and shifts animation block
    raw data pointers/sizes/etc to where the HEK needs them.
    '''
    obje_ct = get_int(meta, 0)
    unit_ct = get_int(meta, 12)
    weap_ct = get_int(meta, 24)
    vehi_ct = get_int(meta, 36)
    devi_ct = get_int(meta, 48)
    damage_ct = get_int(meta, 60)
    fp_anim_ct = get_int(meta, 72)
    sound_ref_ct = get_int(meta, 84)
    node_ct = get_int(meta, 104)
    anim_ct = get_int(meta, 116)

    # set the number of damages to zero
    pack_into("<i", meta, 60, 0)

    off = 128

    # skip the objects
    off += obje_ct*20

    unit_anim_cts = [None]*unit_ct
    ik_point_cts = [None]*unit_ct
    unit_weap_cts = [None]*unit_ct
    unknown_cts = [None]*unit_ct

    for i in range(unit_ct):
        unit_anim_cts[i] = get_int(meta, off + 64)
        ik_point_cts[i] = get_int(meta, off + 76)
        unit_weap_cts[i] = get_int(meta, off + 88)
        unknown_cts[i] = get_int(meta, off + 100)

        # skip to the end of the unit block
        off += 100

        # slice out the unknown block reflexive
        meta = slice_out(meta, off, 28)

    # remove certain blocks from the units
    for i in range(unit_ct):
        unit_anim_ct = unit_anim_cts[i]
        ik_point_ct = ik_point_cts[i]
        unit_weap_ct = unit_weap_cts[i]
        unknown_ct = unknown_cts[i]

        # skip the unit_anims
        off += 2*unit_anim_ct
        meta = remove_pad2(meta, off, unit_anim_ct)

        # skip the ik_points
        off += 64*ik_point_ct

        ext_anim_cts = [None]*unit_weap_ct
        weap_ik_point_cts = [None]*unit_weap_ct
        weap_type_cts = [None]*unit_weap_ct
        for j in range(unit_weap_ct):
            ext_anim_cts[j] = get_int(meta, off + 152)
            weap_ik_point_cts[j] = get_int(meta, off + 164)
            weap_type_cts[j] = get_int(meta, off + 176)

            # set the number of ext_anims to zero
            pack_into("<i", meta, off + 152, 0)

            # shift the position of certain fields backward 32 bytes
            meta = slice_out(meta, off+96, 32)
            meta = meta[:off+120] + UNIT_WEAP_PAD + meta[off+120:]

            # skip to the end of the weapon block
            off += 188

        # remove certain blocks from the unit weapons
        for j in range(unit_weap_ct):
            ext_anim_ct = ext_anim_cts[j]
            weap_ik_point_ct = weap_ik_point_cts[j]
            weap_type_ct = weap_type_cts[j]

            temp_size = 0
            temp_off = off
            # tally the bytes taken up by the ext_anims
            for k in range(ext_anim_ct):
                ext_anim_anim_ct = get_int(meta, temp_off + 16)
                ext_anim_anim_ct += (2-(ext_anim_anim_ct)%2)%2

                temp_size += ext_anim_anim_ct*2 + 28
                temp_off += 28

            # remove the ext_anims
            meta = slice_out(meta, off, temp_size)

            # skip the weap_ik_points
            off += weap_ik_point_ct*64

            weap_type_anim_cts = [None]*weap_type_ct
            for k in range(weap_type_ct):
                weap_type_anim_cts[k] = get_int(meta, off + 48)
                off += 60

            # skip the weapon types
            for weap_type_anim_ct in weap_type_anim_cts:
                off += weap_type_anim_ct*2
                meta = remove_pad2(meta, off, weap_type_anim_ct)


        temp_size = 0
        temp_off = off
        # tally the bytes used by the unknown block, its labels, and its anims
        for j in range(unknown_ct):
            label_ct = get_int(meta, temp_off + 40)
            unknown_anim_ct = get_int(meta, temp_off + 52)
            unknown_anim_ct += (2-(unknown_anim_ct)%2)%2

            # tally the byte size of the labels, anims, and unknown block
            temp_size += label_ct*32 + unknown_anim_ct*2 + 64
            temp_off += 64

        # remove the unknown block and its labels and anims
        meta = slice_out(meta, off, temp_size)


    weap_anim_cts = [None]*weap_ct
    for i in range(weap_ct):
        weap_anim_cts[i] = get_int(meta, off + 16)
        off += 28  # skip to the end of the weapon block

    # remove certain blocks from the weapons
    for weap_anim_ct in weap_anim_cts:
        off += 2*weap_anim_ct  # skip the anims
        meta = remove_pad2(meta, off, weap_anim_ct)


    vehi_seat_cts = [None]*vehi_ct
    vehi_anim_cts = [None]*vehi_ct
    vehi_anim_pads = [None]*vehi_ct
    susp_cts = [None]*vehi_ct
    for i in range(vehi_ct):
        vehi_seat_cts[i] = get_int(meta, off + 80)
        vehi_anim_cts[i] = get_int(meta, off + 92)
        vehi_anim_pads[i] = (2-(vehi_anim_cts[i])%2)%2
        susp_cts[i] = get_int(meta, off + 104)

        # set the number of seats to zero
        pack_into("<i", meta, off + 80, 0)

        # skip to end of the vehicle block
        off += 116

    # remove certain blocks from the vehicles
    for i in range(vehi_ct):
        vehi_seat_ct = vehi_seat_cts[i]
        vehi_anim_ct = vehi_anim_cts[i]
        vehi_anim_pad = vehi_anim_pads[i]
        susp_ct = susp_cts[i]

        temp_size = 0
        temp_off = off
        # tally the bytes used by the seats and its anims
        for j in range(vehi_seat_ct):
            seat_anim_ct = get_int(meta, temp_off + 48)
            seat_anim_ct += (2-(seat_anim_ct)%2)%2

            # tally the byte size of the seat_anims and the seat block
            temp_size += seat_anim_ct*2 + 60
            temp_off += 60

        # remove the seats and their animations
        meta = slice_out(meta, off, temp_size)

        # skip the anims
        off += 2*vehi_anim_ct
        meta = remove_pad2(meta, off, vehi_anim_ct)

        # skip the suspensions
        off += 20*susp_ct


    devi_anim_cts = [None]*devi_ct
    for i in range(devi_ct):
        devi_anim_cts[i] = get_int(meta, off + 84)
        off += 96  # skip to the end of the device block

    # remove certain blocks from the devices
    for devi_anim_ct in devi_anim_cts:
        off += 2*devi_anim_ct  # skip the anims
        meta = remove_pad2(meta, off, devi_anim_ct)


    # remove the damages
    meta = slice_out(meta, off, 2*(damage_ct + ((2-(damage_ct)%2)%2)))


    fp_anim_cts = [None]*fp_anim_ct
    for i in range(fp_anim_ct):
        fp_anim_cts[i] = get_int(meta, off + 16)
        off += 28  # skip to the end of the fp_anim block

    # skip the fp animations
        off += 2*fp_anim_ct  # skip the anims
        meta = remove_pad2(meta, off, fp_anim_ct)

    # skip the sound references
    off += sound_ref_ct*20

    # skip the nodes
    off += node_ct*64

    rawdata_size = 0
    # shift the position of certain parts of the data backward 8 bytes
    for i in range(anim_ct):
        frame_info_size = get_int(meta, off+80)
        default_data_size = get_int(meta, off+148)
        frame_data_size = get_int(meta, off+168)
        meta = slice_out(meta, off+56, 8)
        off += 180  # skip to the end of the anim block

        rawdata_size += frame_info_size + default_data_size + frame_data_size

    # return the meta data cut off at where it needs to be
    return meta[:off] + b'\x00'*rawdata_size


def decompress_animation(anim_block, rawdata):
    return rawdata


def make_antr_tag(meta_path, tags_dir, map_data):
    antr_tag = antr_def.build()
    try:
        idx_off = unpack("<i", map_data[16:20])[0]

        header_size = PC_TAG_INDEX_HEADER_SIZE
        if map_data[idx_off+32:idx_off+36] == b'sgat':
            header_size = XBOX_TAG_INDEX_HEADER_SIZE

        idx_magic = unpack("<i", map_data[idx_off:idx_off+4])[0]
        magic = idx_off +header_size - idx_magic

        # force reading in little endian since meta data is ALL little endian
        force_little()

        # make a new tag
        tagdata = antr_tag.data.tagdata

        # get the dependencies to put in the new tag
        try:
            tag_paths = get_tag_paths(meta_path + '.data')
        except FileNotFoundError:
            print("    Could not locate meta.data file. " +
                  "Cannot get the tags name or its dependency paths.",)
            tag_paths = os.path.split(meta_path)[-1].split('[antr].meta')[:1]

        with open(meta_path, 'rb') as f:
            meta_data = bytearray(f.read())

        try:
            meta_data = clean_antr_meta(meta_data)
        except Exception:
            print(format_exc())
            print("Could not parse meta! Tell Moses and send him these:\n" +
                  '    %s\n    %s%s' % (meta_path , meta_path, '.data'))
            return

        # populate that new tag with the meta data
        try:
            tagdata.parse(rawdata=meta_data, allow_corrupt=True)
        except Exception:
            print(format_exc())
            tagdata.pprint(printout=True)
            input()

        sounds = tagdata.sound_references.STEPTREE

        # replace the filepath
        fp = tags_dir + tag_paths[0] + ".model_animations"
        fp = fp.replace('\\', '/').replace('/', PATHDIV)
        antr_tag.filepath = fp

        # insert the dependency strings
        for i in range(len(tag_paths)-1):
            reference = sounds[i]
            reference.sound.filepath = tag_paths[i+1][0]
            reference.sound.tag_class.data = tag_paths[i+1][1]

        map_len = len(map_data)

        # grab the animation data from the map and put it in the tag
        for anim in antr_tag.data.tagdata.animations.STEPTREE:
            f_info = anim.frame_info
            d_data = anim.default_data
            f_data = anim.frame_data

            f_info_size = f_info.size
            d_data_size = d_data.size
            f_data_size = f_data.size

            f_info_off = f_info.pointer + magic
            d_data_off = d_data.pointer + magic
            f_data_off = f_data.raw_pointer

            frame_count = anim.frame_count
            frame_size = anim.frame_size
            node_count = anim.node_count

            compressed = anim.flags.compressed_data
            trans_flags = anim.trans_flags0 + (anim.trans_flags1<<32)
            rot_flags   = anim.rot_flags0   + (anim.rot_flags1<<32)
            scale_flags = anim.scale_flags0 + (anim.scale_flags1<<32)

            if f_info_size > 0 and f_info_off > 0 and f_info_off < map_len:
                raw = map_data[f_info_off:f_info_off + f_info_size]
                # byteswap the data
                swapped = bytearray(raw)
                for i in range(0, len(raw), 4):
                    swapped[i] = raw[i+3];   swapped[i+1] = raw[i+2]
                    swapped[i+2] = raw[i+1]; swapped[i+3] = raw[i]
                f_info.STEPTREE = swapped
            elif f_info_size:
                f_info.size = 0

            if d_data_size > 0 and d_data_off > 0 and d_data_off < map_len:
                raw = map_data[d_data_off:d_data_off + d_data_size]
                # byteswap the data
                swapped = bytearray(b'\x00'*len(raw))
                i = j = 0

                # there are only default values for each
                # node if there isnt frame data for each
                for n in range(node_count):
                    if not (rot_flags&(1<<n)):
                        swapped[j] = raw[i+1];   swapped[j+1] = raw[i]
                        swapped[j+2] = raw[i+3]; swapped[j+3] = raw[i+2]
                        swapped[j+4] = raw[i+5]; swapped[j+5] = raw[i+4]
                        swapped[j+6] = raw[i+7]; swapped[j+7] = raw[i+6]
                        j += 8
                    i += 8

                    if not (trans_flags&(1<<n)):
                        swapped[j] = raw[i+3];   swapped[j+1] = raw[i+2]
                        swapped[j+2] = raw[i+1]; swapped[j+3] = raw[i]
                        swapped[j+4] = raw[i+7]; swapped[j+5] = raw[i+6]
                        swapped[j+6] = raw[i+5]; swapped[j+7] = raw[i+4]
                        swapped[j+8] = raw[i+11]; swapped[j+9] = raw[i+10]
                        swapped[j+10] = raw[i+9]; swapped[j+11] = raw[i+8]
                        j += 12
                    i += 12

                    if not (scale_flags&(1<<n)):
                        swapped[j] = raw[i+3]; swapped[j+1] = raw[i+2]
                        swapped[j+2] = raw[i+1]; swapped[j+3] = raw[i]
                        j += 4
                    i += 4

                d_data.STEPTREE = swapped[:j]
            elif d_data_size:
                d_data.size = 0

            if f_data_size > 0 and f_data_off > 0 and f_data_off < map_len:
                raw = map_data[f_data_off:f_data_off + f_data_size]
                corrupt = False

                if compressed:
                    f_data.STEPTREE = raw
                    rot_def_off = get_int(raw, 4)
                    trans_def_off = get_int(raw, 20)
                    scale_def_off = get_int(raw, 36)

                    rot_end = get_int(raw, 12)
                    trans_end = get_int(raw, 28)
                    scale_end = len(raw)

                    largest_off = max(
                        rot_def_off, get_int(raw, 8), rot_end, get_int(raw, 16),
                        trans_def_off, get_int(raw, 24), trans_end,
                        get_int(raw, 32), scale_def_off, get_int(raw, 40))

                    if largest_off > len(raw):
                        print("    Error: compressed animation frame data " +
                              "seems to be corrupted in '%s'" % anim.name)
                        corrupt = True


                if corrupt:
                    # change a few things so it doesnt crash the hek
                    anim.flags.compressed_data = False
                    anim.name = ('CORRUPT_' + anim.name)[:31]
                    continue
                elif compressed:
                    continue

                # byteswap the data
                i = 0
                f_data.STEPTREE = swapped = bytearray(raw)
                for f in range(frame_count):
                    for n in range(node_count):
                        if rot_flags&(1<<n):
                            swapped[i] = raw[i+1];   swapped[i+1] = raw[i]
                            swapped[i+2] = raw[i+3]; swapped[i+3] = raw[i+2]
                            swapped[i+4] = raw[i+5]; swapped[i+5] = raw[i+4]
                            swapped[i+6] = raw[i+7]; swapped[i+7] = raw[i+6]
                            i += 8

                        if trans_flags&(1<<n):
                            swapped[i] = raw[i+3];   swapped[i+1] = raw[i+2]
                            swapped[i+2] = raw[i+1]; swapped[i+3] = raw[i]
                            swapped[i+4] = raw[i+7]; swapped[i+5] = raw[i+6]
                            swapped[i+6] = raw[i+5]; swapped[i+7] = raw[i+4]
                            swapped[i+8] = raw[i+11]; swapped[i+9] = raw[i+10]
                            swapped[i+10] = raw[i+9]; swapped[i+11] = raw[i+8]
                            i += 12

                        if scale_flags&(1<<n):
                            swapped[i] = raw[i+3]; swapped[i+1] = raw[i+2]
                            swapped[i+2] = raw[i+1]; swapped[i+3] = raw[i]
                            i += 4

            elif f_data_size:
                f_data.size = 0

        # force fix the endianness
        force_normal()
    except Exception:
        force_normal()
        raise

    return antr_tag


def get_tag_paths(data_path):
    tag_paths = ['']
    try:
        with open(data_path, 'r') as f:
            for line in f:
                if line.lower().startswith('filename'):
                    tag_paths[0] = line.split('|')[-1].split('\n')[0]
                elif line.lower().startswith('dependency'):
                    tag_path, tag_class = line.split('\n')[0].split('|')[2:]
                    tag_class = fcc(tag_class[:4], 'big')
                    tag_paths.append((tag_path, tag_class))
    except FileNotFoundError:
        raise
    except Exception:
        print(format_exc())
    return tag_paths


class StubbsAntrCompiler(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Stubbs antr tag compiler v1.0")
        self.geometry("400x150+0+0")
        self.resizable(0, 0)

        self.meta_dir = StringVar(self)
        self.tags_dir = StringVar(self)
        self.map_path = StringVar(self)

        # make the frames
        self.meta_dir_frame = LabelFrame(self, text="Directory of metadata")
        self.tags_dir_frame = LabelFrame(self, text="Output tags directory")
        self.map_path_frame = LabelFrame(self, text="Map to extract from")
        
        # add the filepath boxes
        self.meta_dir_entry = Entry(
            self.meta_dir_frame, textvariable=self.meta_dir)
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.map_path_entry = Entry(
            self.map_path_frame, textvariable=self.map_path)
        self.meta_dir_entry.config(width=55, state=DISABLED)
        self.tags_dir_entry.config(width=55, state=DISABLED)
        self.map_path_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.compile_btn = Button(
            self, text="Compile", width=15, command=self.compile_animations)
        self.meta_dir_browse_btn = Button(
            self.meta_dir_frame, text="Browse",
            width=6, command=self.meta_dir_browse)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)
        self.map_path_browse_btn = Button(
            self.map_path_frame, text="Browse",
            width=6, command=self.map_path_browse)

        # pack everything
        self.meta_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.map_path_entry.pack(expand=True, fill='x', side='left')
        self.meta_dir_browse_btn.pack(fill='both', side='left')
        self.tags_dir_browse_btn.pack(fill='both', side='left')
        self.map_path_browse_btn.pack(fill='both', side='left')

        self.meta_dir_frame.pack(expand=True, fill='both')
        self.tags_dir_frame.pack(expand=True, fill='both')
        self.map_path_frame.pack(expand=True, fill='both')
        self.compile_btn.pack(fill='both', padx=5, pady=5)

    def meta_dir_browse(self):
        dirpath = askdirectory(initialdir=self.meta_dir.get())
        if dirpath:
            self.meta_dir.set(dirpath)
        
    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)
        
    def map_path_browse(self):
        path = askopenfilename(initialdir=self.map_path.get())
        if path:
            self.map_path.set(path)

    def compile_animations(self):
        print('Compiling model_animations\n')
        start = time()
        meta_dir = self.meta_dir.get()
        tags_dir = self.tags_dir.get()
        map_path = self.map_path.get()

        if not meta_dir.endswith(PATHDIV):
            meta_dir += PATHDIV

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        try:
            with open(map_path, 'rb') as f:
                map_data = f.read()
        except Exception:
            print("Could not open '%s' to extract animation data.")
            return

        for root, dirs, files in os.walk(meta_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if not filename.lower().endswith('[antr].meta'):
                    continue

                print('Compiling %s' % filepath.split(meta_dir)[-1])

                tag = make_antr_tag(filepath, tags_dir, map_data)
                if not tag:
                    continue

                tag.serialize(temp=False, backup=False, int_test=False)
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    compiler = StubbsAntrCompiler()
    compiler.mainloop()
except Exception:
    print(format_exc())
    input()

