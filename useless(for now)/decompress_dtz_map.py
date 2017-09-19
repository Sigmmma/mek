import zlib
import os

curr_dir = os.curdir

for root, dirs, files in os.walk(curr_dir):
    for file in files:
        filename, ext = os.path.splitext(file)
        if ext != ".dtz": continue

        print(file)
        with open(os.path.join(root, file), "rb") as fi:
            comp_data = fi.read()
            with open(os.path.join(root, filename), "wb+") as fo:
                decomp_obj = zlib.decompressobj()

                while comp_data:
                    # decompress map 64Mb at a time
                    fo.write(decomp_obj.decompress(comp_data, 64*1024*1024))
                    comp_data = decomp_obj.unconsumed_tail

