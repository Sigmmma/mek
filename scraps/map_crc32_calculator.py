import gc

from os import walk
from os.path import splitext, dirname, join
from traceback import format_exc
from zlib import crc32


CE_INDEX_OFFSET = 0x40440000


for root, directories, files in walk(dirname(__file__)):
    for file in files:
        if splitext(file)[-1].lower() != ".map":
            continue

        try:
            crc = 0
            with open(join(root, file), "rb") as f:
                if f.read(4) != b"daeh":
                    continue

                f.seek(100)
                print(join(root, file))
                print("%08x" % (int.from_bytes(f.read(4), 'little')) + " : In header")

                f.seek(16)
                tagdata_offset = int.from_bytes(f.read(4), 'little') ###
                tagdata_size = int.from_bytes(f.read(4), 'little') ###


                f.seek(tagdata_offset)
                tagindex_offset = int.from_bytes(f.read(4), 'little')
                tagindex_offset += tagdata_offset - CE_INDEX_OFFSET
                scenario_tagid = int.from_bytes(f.read(2), 'little')
                f.seek(tagindex_offset + 32 * scenario_tagid + 20)
                scenario_metadata_offset = int.from_bytes(f.read(4), 'little')
                scenario_metadata_offset += tagdata_offset - CE_INDEX_OFFSET


                f.seek(tagdata_offset + 20)
                modeldata_offset = int.from_bytes(f.read(4), 'little') ###
                f.seek(tagdata_offset + 32)
                modeldata_size = int.from_bytes(f.read(4), 'little') ###

                f.seek(scenario_metadata_offset + 1444)
                bsp_count = int.from_bytes(f.read(4), 'little')
                bsps_offset = int.from_bytes(f.read(4), 'little')
                bsps_offset += tagdata_offset - CE_INDEX_OFFSET


                chunk_offsets = [] ###
                chunk_sizes = [] ###


                f.seek(bsps_offset)
                for i in range(bsp_count):
                    chunk_offsets.append(int.from_bytes(f.read(4), 'little'))
                    chunk_sizes.append(int.from_bytes(f.read(4), 'little'))
                    f.seek(24, 1)

                chunk_offsets += [modeldata_offset, tagdata_offset]
                chunk_sizes   += [modeldata_size, tagdata_size]

                crc = 0
                for i in range(len(chunk_offsets)):
                    if chunk_sizes[i]:
                        #print(chunk_offsets[i], chunk_sizes[i])
                        f.seek(chunk_offsets[i])
                        crc = crc32(f.read(chunk_sizes[i]), crc)
                        gc.collect()

                print("%08x" % (crc ^ 0xFFffFFff) + " : Calculated")
        except Exception:
            print(format_exc())

input("Finished...")
