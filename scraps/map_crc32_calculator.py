import gc

from os import walk
from os.path import splitext, dirname, join
from traceback import format_exc
from zlib import crc32


for root, directories, files in walk(dirname(__file__)):
    for file in files:
        if splitext(file)[-1].lower() != ".map":
            continue

        try:
            crc = 0
            with open(join(root, file), "rb") as f:
                if f.read(4) != b"daeh":
                    continue

                f.seek(2048)
                crc, chunk = 0, True
                while chunk:
                    chunk = f.read(4*1024**2)  # calculate in 4Mb chunks
                    crc = crc32(chunk, crc)
                    gc.collect()

            print("%08x" % (crc ^ 0xFFffFFff) + "  " + join(root, file))
        except Exception:
            print(format_exc())

input("Finished...")
