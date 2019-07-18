import gc
import os

from reclaimer.meta.halo_map import get_map_header, get_index_magic
from refinery import crc_functions


def do_checksum_spoof(in_filepath, out_filepath, crc_str):
    try:
        crc = int(crc_str.replace(" ", ""), 16)
    except ValueError:
        print("Invalid crc checksum. Must be an 8 character hex string")
        return

    if not out_filepath:
        out_filepath = in_filepath

    in_filepath = os.path.abspath(in_filepath)
    out_filepath = os.path.abspath(out_filepath)
    crc = crc & 0xFFffFFff
    if not os.path.isfile(in_filepath):
        print("Specified input map does not exist.")
        return

    try:
        os.makedirs(os.path.join(os.path.dirname(out_filepath), ""), True)
    except FileExistsError:
        pass

    # use r+ mode rather than w if the file exists
    # since it might be hidden. apparently on windows
    # the w mode will fail to open hidden files.
    if in_filepath.lower() == out_filepath.lower():
        in_file = out_file = open(in_filepath, 'r+b')
    else:
        in_file = open(in_filepath, 'rb')
        if os.path.isfile(out_filepath):
            out_file = open(out_filepath, 'r+b')
            out_file.truncate(0)
        else:
            out_file = open(out_filepath, 'w+b')

    map_header = get_map_header(in_file.read(2048))
    if map_header is None:
        print("Input file does not appear to be a halo map.")
        return
    elif map_header.version.enum_name != "halo1ce":
        print("Input file does not appear to be a halo custom edition map.")
        return

    index_magic = get_index_magic(map_header)
    in_file.seek(0)
    if in_file is not out_file:
        # copy the map to the location
        chunk = True
        while chunk:
            chunk = in_file.read(4*1024**2)  # work with 4Mb chunks
            out_file.write(chunk)
            gc.collect()

        in_file.close()
        out_file.flush()

    map_header.crc32 = crc
    crc_functions.E.__defaults__[0][:] = [0, 0x800000000 - crc, crc]
    out_file.seek(0)
    out_file.write(map_header.serialize(calc_pointers=False))
    out_file.flush()
    if hasattr(out_file, "fileno"):
        os.fsync(out_file.fileno())

    # write the map header so the calculate_ce_checksum can read it
    crc_functions.U(
        [crc_functions.calculate_ce_checksum(out_file, index_magic)^0xFFffFFff,
         out_file, map_header.tag_index_header_offset + 8])

    out_file.flush()
    if hasattr(out_file, "fileno"):
        os.fsync(out_file.fileno())

    out_file.close()


# EXAMPLE
do_checksum_spoof(".\\test.map", ".\\test_spoofed.map", "12345678")
input("Finished")
