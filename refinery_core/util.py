from .hashcacher_window import RESERVED_WINDOWS_FILENAME_MAP,\
     INVALID_PATH_CHARS


def is_protected(tagpath):
    return tagpath in RESERVED_WINDOWS_FILENAME_MAP or (
        not INVALID_PATH_CHARS.isdisjoint(set(tagpath)))


def fourcc(value):
    return value.to_bytes(4, byteorder='big').decode(encoding='latin-1')
