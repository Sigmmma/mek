from reclaimer.hek.defs.bitm import bitm_def
import os

input("""
This tool will add an empty 4x4 bitmap block to every bitmap in
the current folder which doesn't already have one on the end.
This is to trick tool into compiling the bitmap into the map,
even if a bitmap of that size and name exists in bitmaps.map

Press any key to start...""")

print("\nScanning...")
for root, dirs, files in os.walk(".\\"):
    for fname in files:
        if not fname.endswith(".bitmap"):
            continue

        filepath = os.path.join(root, fname)
        try:
            tag = bitm_def.build(filepath=filepath)
        except Exception:
            print("Could not load: %s" % filepath)
            continue

        bitmaps = tag.data.tagdata.bitmaps.STEPTREE
        if not bitmaps:
            continue

        b = bitmaps[-1]
        if (len(bitmaps) > 1 and b.mipmaps == 0 and
            b.height == 4 and b.width == 4 and b.depth == 1 and
            b.format.enum_name == "dxt1" and b.pixels_offset == 0):
            continue

        bitmaps.append()
        b = bitmaps[-1]
        b.width = b.height = 4
        b.depth = 1
        b.format.set_to("dxt1")
        b.flags.power_of_2_dim = b.flags.compressed = True
        b.registration_point_x = b.registration_point_y = 2

        tag.serialize(temp=False, backup=True)
        print(tag.filepath)
            
input("\nFinished")
