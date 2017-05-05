import os, supyr_struct

from array import array
from math import acos, ceil, sqrt, sin
from struct import unpack, pack
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc
from reclaimer.common_descs import tag_header_os
from supyr_struct.defs.block_def import BlockDef
from reclaimer.hek.defs.antr import antr_def
from reclaimer.hek.defs.objs.antr import compressed_frames

tag_header_def = BlockDef(tag_header_os)
curr_dir = os.path.join(os.path.abspath(os.curdir), '')


def get_node_frames(anim):
    # make a nested list to store all transforms
    node_frames = []
    for i in range(anim.node_count):
        # the node stores rotation, translation, and scale
        frames = [ [[0.0, 0.0, 0.0, 1.0],
                    [0.0, 0.0, 0.0], 1.0]
                   for j in range(frame_count) ]

        node_frames.append(frames)
    return node_frames


def get_transform_flags(anim):
    node_count = anim.node_count
    rot_flags   = anim.rot_flags0   + (anim.rot_flags1   << 32)
    trans_flags = anim.trans_flags0 + (anim.trans_flags1 << 32)
    scale_flags = anim.scale_flags0 + (anim.scale_flags1 << 32)

    # mask them off by the node count since some flags seem to be wrong
    rot_flags   &= (1<<node_count)-1
    trans_flags &= (1<<node_count)-1
    scale_flags &= (1<<node_count)-1
    rots   = [bool(rot_flags   & (1<<i)) for i in range(64)]
    trans  = [bool(trans_flags & (1<<i)) for i in range(64)]
    scales = [bool(scale_flags & (1<<i)) for i in range(64)]
    return rots, trans, scales


def convert_30fps_to_60fps(anim):
    rot_flags, trans_flags, scale_flags = get_transform_flags(anim)
    rot_count   = sum(rot_flags)
    trans_count = sum(trans_flags)
    scale_count = sum(scale_flags)

    f_size = rot_count*8 + trans_count*12 + scale_count*4
    f_info_ct = 0
    if anim.frame_info_type.data:
        f_info_ct = anim.frame_info_type.data + 1

    node_count = anim.node_count
    old_frame_count = anim.frame_count

    pack_code = ">%sf" % f_info_ct
    new_frame_count = old_frame_count*2 - 1

    frame_info = anim.frame_info.data
    frame_data = anim.frame_data.data

    new_frame_info = b''
    new_frame_data = b''
    info = None
    curr_frame = None
    i_off = 0

    # copy existing frame info and data and interpolate new ones
    for f in range(new_frame_count):
        old_f = f//2

        if f%2:
            if f_info_ct:
                new_frame_info += pack(pack_code, *info)

            # interpolate a frame from the surrounding two
            for n in range(node_count):

                # if this node has rotations, make a new one
                if rot_flags[n]:
                    i0, j0, k0, w0 = unpack(">4h", curr_frame[off: off+8])
                    i1, j1, k1, w1 = unpack(">4h", next_frame[off: off+8])

                    # invert the second vector if the angle is > 180
                    if i0*i1 + j0*j1 + k0*k1 + w0*w1 < 0:
                        i1, j1, k1, w1 = -i1, -j1, -k1, -w1

                    # nlerp interpolation code
                    i2, j2, k2, w2 = i0+i1, j0+j1, k0+k1, w0+w1
                    l = sqrt(i2**2 + j2**2 + k2**2 + w2**2)/32767

                    if l == 0:
                        # avoid division by zero
                        #new_frame_data += pack(">4h", 0, 0, 0, 32767)
                        new_frame_data += b'\x00\x00\x00\x00\x00\x00\x7f\xff'
                    else:
                        new_frame_data += pack(">4h",
                            int(i2/l), int(j2/l), int(k2/l), int(w2/l))

                    # slerp interpolation code
                    '''
                    l0 = sqrt(i0**2 + j0**2 + k0**2 + w0**2)
                    l1 = sqrt(i1**2 + j1**2 + k1**2 + w1**2)
                    if l0 == 0 or l1 == 0:
                        i0 = i1 = j0 = j1 = k0 = k1 = 0
                        w0 = w1 = 1
                    else:
                        i0, j0, k0, w0 = i0/l0, j0/l0, k0/l0, w0/l0
                        i1, j1, k1, w1 = i1/l1, j1/l1, k1/l1, w1/l1

                    cos_half_theta = i0*i1 + j0*j1 + k0*k1 + w0*w1
                    print(cos_half_theta)
                    print(i0, j0, k0, w0)
                    print(i1, j1, k1, w1)
                    print()
                    if cos_half_theta < 0:
                        cos_half_theta = -cos_half_theta
                        i0, j0, k0 = -i0, -j0, -k0
                        i1, j1, k1 = -i1, -j1, -k1

                    # slerp interpolation code
                    if abs(cos_half_theta) >= 1.0:
                        half_theta = 0.0
                    else:
                        half_theta = acos(cos_half_theta)
                        
                    sin_half_theta = sqrt(max(1 - cos_half_theta**2, 0))

                    # angle is not well defined in floating point at this point
                    if sin_half_theta <= 0.000001:
                        r = 0.5
                    else:
                        r = sin(0.5*half_theta) / sin_half_theta

                    new_frame_data += pack(">4h",
                        int((i0 + i1)*r*32767), int((j0 + j1)*r*32767),
                        int((k0 + k1)*r*32767), int((w0 + w1)*r*32767))
                    '''
                    off += 8

                # if this node has translations, make a new one
                if trans_flags[n]:
                    x0, y0, z0 = unpack(">3f", curr_frame[off: off+12])
                    x1, y1, z1 = unpack(">3f", next_frame[off: off+12])
                    new_frame_data += pack(
                        ">3f", (x0 + x1)/2, (y0 + y1)/2, (z0 + z1)/2)
                    off += 12

                # if this node has scales, make a new one
                if scale_flags[n]:
                    s0 = unpack(">f", curr_frame[off: off+4])[0]
                    s1 = unpack(">f", next_frame[off: off+4])[0]
                    new_frame_data += pack(
                        ">f", (s0 + s1)/2)
                    off += 4

        else:
            # copy a frame and get frames for interpolating

            if f_info_ct:
                info = unpack(pack_code, frame_info[i_off: i_off+f_info_ct*4])
                i_off += f_info_ct*4
                if f+1 != new_frame_count or anim.flags.final_velocity_kept:
                    # not the last frame, so halve the dx, dy, dz, dyaw
                    half_info = [val/2 for val in info]
                    if len(half_info) == 4:
                        # don't cut the dyaw in half
                        half_info[-1] = info[-1]
                    info = half_info

                # write the info to the new_frame_info for the current frame
                new_frame_info += pack(pack_code, *info)
                    
            # get the current and next frames data to copy and interpolate them
            curr_frame = frame_data[    old_f*f_size: (old_f+1)*f_size]
            next_frame = frame_data[(1+old_f)*f_size: (old_f+2)*f_size]

            # copy the current frame
            new_frame_data += curr_frame
            off = 0

    # replace the frame info and data
    anim.frame_info.data = new_frame_info
    anim.frame_data.data = new_frame_data

    # change header information
    anim.frame_count = new_frame_count
    anim.frame_size = f_size
    anim.flags.fps_60 = True

    index_scale = new_frame_count/old_frame_count

    # recalculate the frame indices
    anim.loop_frame_index       = int((anim.loop_frame_index + 0.5)*index_scale)
    anim.key_frame_index        = int((anim.key_frame_index + 0.5)*index_scale)
    anim.second_key_frame_index = int((anim.second_key_frame_index + 0.5)*index_scale)
    anim.sound_frame_index      = int((anim.sound_frame_index + 0.5)*index_scale)
    anim.left_foot_frame_index  = int((anim.left_foot_frame_index + 0.5)*index_scale)
    anim.right_foot_frame_index = int((anim.right_foot_frame_index + 0.5)*index_scale)
    return 1


def convert_60fps_to_30fps(anim):
    rot_flags, trans_flags, scale_flags = get_transform_flags(anim)
    rot_count   = sum(rot_flags)
    trans_count = sum(trans_flags)
    scale_count = sum(scale_flags)

    f_size = rot_count*8 + trans_count*12 + scale_count*4
    f_info_ct = 0
    if anim.frame_info_type.data:
        f_info_ct = anim.frame_info_type.data + 1
    f_info_size = f_info_ct*4
    old_frame_count = anim.frame_count

    # dont divide out the first and last frames, since they will ALWAYS be kept
    new_frame_count = (old_frame_count - 2)//2 + 2

    frame_info = anim.frame_info.data
    frame_data = anim.frame_data.data

    new_frame_info = b''
    # copy the first frame
    new_frame_data = frame_data[:f_size]

    # copy all even numbered frames, except the last one
    pack_code = ">%sf" % f_info_ct

    for i in range(new_frame_count-1):
        f = i*2
        # have to add together the changes in position and rotation rather
        # than just drop them like we can with the frame data
        merged_info = unpack(
            pack_code, frame_info[f*f_info_size: (f+1)*f_info_size])
        skipped_info = unpack(
            pack_code, frame_info[(f+1)*f_info_size: (f+2)*f_info_size])

        merged_info = [skipped_info[j]+merged_info[j] for j in range(f_info_ct)]
        new_frame_info += pack(pack_code, *merged_info)

    for i in range(1, new_frame_count-1):
        new_frame_data += frame_data[i*2*f_size: (i*2+1)*f_size]

    info = unpack(pack_code, frame_info[-1*f_info_size:])

    if anim.flags.final_velocity_kept:
        # last frame needs to have its dx/dy/dz doubled
        double_info = [val*2 for val in info]
        if len(double_info) == 4:
            # don't double the dyaw
            double_info[-1] = info[-1]
        info = double_info

    # copy the last frame
    new_frame_info += pack(pack_code, *info)
    new_frame_data += frame_data[(old_frame_count-1)*f_size:
                                 old_frame_count*f_size]

    # replace the frame info and data
    anim.frame_info.data = new_frame_info
    anim.frame_data.data = new_frame_data

    # change header information
    anim.frame_size = f_size
    anim.flags.fps_60 = False
    anim.frame_count = new_frame_count

    index_scale = new_frame_count/old_frame_count
    

    anim.loop_frame_index       = int(ceil(anim.loop_frame_index*index_scale) - 0.5)
    anim.key_frame_index        = int(ceil(anim.key_frame_index*index_scale) - 0.5)
    anim.second_key_frame_index = int(ceil(anim.second_key_frame_index*index_scale) - 0.5)
    anim.sound_frame_index      = int(ceil(anim.sound_frame_index*index_scale) - 0.5)
    anim.left_foot_frame_index  = int(ceil(anim.left_foot_frame_index*index_scale) - 0.5)
    anim.right_foot_frame_index = int(ceil(anim.right_foot_frame_index*index_scale) - 0.5)
    return 1


def convert_30fps_to_60fps_compressed(anim):
    old_frame_count = anim.frame_count
    new_frame_count = old_frame_count*2 - 1

    index_scale = new_frame_count/old_frame_count
    frame_data = anim.frame_data.data

    uncomp_frame_data = frame_data[: anim.offset_to_compressed_data]
    comp_frame_data = frame_data[anim.offset_to_compressed_data: ]
    frame_data = compressed_frames.build(rawdata=comp_frame_data)

    # make new frame_info by halving all the old values
    if anim.frame_info_type.data:
        f_info_ct = anim.frame_info_type.data + 1
        pack_code = ">%sf" % f_info_ct
        i_off = 0
        frame_info = anim.frame_info.data
        new_frame_info = b''

        for f in range(new_frame_count):
            if not (f%2):
                info = unpack(pack_code, frame_info[i_off: i_off+f_info_ct*4])
                i_off += f_info_ct*4
                if f+1 != new_frame_count or anim.flags.final_velocity_kept:
                    # not the last frame, so halve the dx, dy, dz, dyaw
                    half_info = [val/2 for val in info]
                    if len(half_info) == 4:
                        # don't cut the dyaw in half
                        half_info[-1] = info[-1]
                    info = half_info

            # write the info to the new_frame_info for the current frame
            new_frame_info += pack(pack_code, *info)
                
        # put the new_frame_info into the anim block
        anim.frame_info.data = new_frame_info

    # scale all the frame numbers
    for transform in (frame_data.rotation, frame_data.translation, frame_data.scale):
        frame_nums = transform.frame_nums
        for i in range(len(frame_nums)):
            frame_nums[i] = int((frame_nums[i] + 0.5)*index_scale)

    # change header information
    anim.frame_count = new_frame_count
    anim.offset_to_compressed_data = anim.frame_size*new_frame_count
    anim.flags.fps_60 = True

    # put the uncompressed frame data back into the anim block
    anim.frame_data.data = uncomp_frame_data

    # pad the frame_data with 0x00 to fill in the new, empty frames
    anim.frame_data.data += b'\x00'*(anim.frame_size*(new_frame_count-old_frame_count))

    # add the new 
    anim.frame_data.data += frame_data.serialize()

    # recalculate the frame indices
    anim.loop_frame_index       = int((anim.loop_frame_index + 0.5)*index_scale)
    anim.key_frame_index        = int((anim.key_frame_index + 0.5)*index_scale)
    anim.second_key_frame_index = int((anim.second_key_frame_index + 0.5)*index_scale)
    anim.sound_frame_index      = int((anim.sound_frame_index + 0.5)*index_scale)
    anim.left_foot_frame_index  = int((anim.left_foot_frame_index + 0.5)*index_scale)
    anim.right_foot_frame_index = int((anim.right_foot_frame_index + 0.5)*index_scale)
    return 1


class AntrFpsConvertor(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Animation Fps Changer v1.5")
        self.geometry("400x120+0+0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.fps = IntVar(self)
        self.overwrite_old = IntVar(self)
        self.tags_dir.set(os.path.join(curr_dir + 'tags', ''))
        self.fps.set(60)

        # make the frames
        self.tags_dir_frame = LabelFrame(self, text="Tags directory")
        self.checkbox_frame = LabelFrame(self, text="Conversion settings")
        
        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.convert_btn = Button(
            self, text="Convert animations", width=22, command=self.convert)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        self.checkbox_30_to_60 = Checkbutton(
            self.checkbox_frame, variable=self.fps,
            offvalue=30, onvalue=60, text="30 to 60")
        self.checkbox_60_to_30 = Checkbutton(
            self.checkbox_frame, variable=self.fps,
            offvalue=60, onvalue=30, text="60 to 30")
        self.checkbox_overwrite_tags = Checkbutton(
            self.checkbox_frame, variable=self.overwrite_old,
            offvalue=0, onvalue=1, text="Overwrite old tags")

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='both', side='left')

        for w in (self.checkbox_30_to_60, self.checkbox_60_to_30,
                  self.checkbox_overwrite_tags):
            w.pack(fill='both', expand=True, side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.convert_btn.pack(fill='both', padx=5, pady=5)
        self.checkbox_frame.pack(fill='both', padx=5, pady=5)

    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def destroy(self):
        Tk.destroy(self)
        #raise SystemExit(0)
        os._exit(0)

    def convert(self):
        start = time()
        fps = self.fps.get()
        tags_dir = os.path.join(self.tags_dir.get(), '')
        prefix = '%sfps_' % fps
        overwrite_old = self.overwrite_old.get()
        convert_to_60 = (fps == 60)
        all_count = 0

        print('Converting animations to %s fps\n' % fps)

        for root, dirs, files in os.walk(tags_dir):
            root = os.path.join(root, '')

            for filename in files:
                filepath = root + filename
                if os.path.splitext(filename)[-1].lower() != '.model_animations':
                    continue

                blam_header = tag_header_def.build(filepath=filepath)
                if bool(blam_header.flags.fps_60) == convert_to_60:
                    # tag is already the correct fps, so skip it
                    del blam_header
                    continue

                print('Converting %s' % filepath.split(tags_dir)[-1])

                antr_tag = antr_def.build(filepath=filepath)

                # rename the tag to the converted filepath
                if not overwrite_old:
                    dirpath, filename = os.path.split(filepath)
                    antr_tag.filepath = os.path.join(dirpath, prefix + filename)

                anims = antr_tag.data.tagdata.animations.STEPTREE
                count = 0
                for i in range(len(anims)):
                    anim = anims[i]
                    compressed = anim.flags.compressed_data
                    if anim.flags.special:
                        # animation is marked as a special overlay. ignore it
                        del antr_tag
                        continue
                    elif not anim.frame_count:
                        print("    '%s' has a frame count of zero. Cannot convert.")
                        del antr_tag
                        continue

                    try:
                        if convert_to_60 and not anim.flags.fps_60:
                            if compressed:
                                print("    [COMPRESSED] %s" % anim.name)
                                count += convert_30fps_to_60fps_compressed(anim)
                            else:
                                print("    %s" % anim.name)
                                count += convert_30fps_to_60fps(anim)
                        elif not convert_to_60 and anim.flags.fps_60:
                            if compressed:
                                print(("    '%s' is compressed. 60fps " +
                                       "compressed animations cannot be " +
                                       "converted to 30fps.") % anim.name)
                                continue
                            else:
                                print("    %s" % anim.name)
                                count += convert_60fps_to_30fps(anim)
                    except Exception:
                        print(format_exc())
                        print("        Could not convert the above animation.")

                if count:
                    print("\n    Converted %s animations." % count)
                    antr_tag.data.blam_header.flags.fps_60 = bool(convert_to_60)
                    antr_tag.serialize(temp=False, backup=False)
                    all_count += count
                else:
                    print("    No animations needed to be converted.")

                del antr_tag
        print('\nFinished. Took %s seconds' % (time() - start))
        print('Converted %s animations in total.' % all_count)

try:
    converter = AntrFpsConvertor()
    converter.mainloop()
except SystemExit:
    pass
except Exception:
    print(format_exc())
    input()

