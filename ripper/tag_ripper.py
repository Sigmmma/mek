from hashlib import md5
from os import makedirs
from os.path import dirname, exists
from supyr_struct.buffer import *
from supyr_struct.field_types import FieldType
from supyr_struct.blocks import VoidBlock
from traceback import format_exc

from .hash_cacher import HashCacher
from reclaimer.halo.constants import *
from reclaimer.halo.meta.handler import MapLoader

curr_dir = dirname(__file__)

class TagRipper(MapLoader):

    rebuild_paths = False
    rebuild_classes = False

    cached_tag_paths = None

    def __init__(self, **kwargs):
        MapLoader.__init__(self, **kwargs)

        self.hash_cacher = HashCacher()
        self.tag_id_map = {}  # maps tag ids to the meta header
        self.path_id_map = {}  # maps tag ids to the tag path
        self.tag_lib = self.hash_cacher.tag_lib

        self.rebuild_paths = kwargs.pop('rebuild_paths', True)
        self.rebuild_classes = kwargs.pop('rebuild_classes', False)

        #make a cache of all the different headers for
        #each type of tag to speed up writing tags
        self.tag_headers = {}

        #make a collection of all the tag paths in the cache files
        self.cached_tag_paths = cached = {}

        cached['bitm'] = []
        cached['snd!'] = []
        cached['font'] = cached['hmt '] = cached['str#'] = cached['ustr'] = []

        #try to build a list of all the bitmap cache tag paths
        try:
            paths = cached['bitm']
            with open(curr_dir + '\\resources\\bitmaps tag list.txt') as f:
                for line in f:
                    paths.append(line[:-1])
        except Exception:
            print(format_exc())

        #try to build a list of all the sounds cache tag paths
        try:
            paths = cached['snd!']
            with open(curr_dir + '\\resources\\sounds tag list.txt') as f:
                for line in f:
                    paths.append(line[:-1])
        except Exception:
            print(format_exc())

        #try to build a list of all the sounds cache tag paths
        try:
            paths = cached['font']
            with open(curr_dir + '\\resources\\loc tag list.txt') as f:
                for line in f:
                    paths.append(line[:-1])
        except Exception:
            print(format_exc())


        for def_id in sorted(self.tag_lib.defs):
            if len(def_id) != 4:
                continue
            h_desc = self.tag_lib.defs[def_id].descriptor[0]
            
            h_block = [None]
            h_desc['TYPE'].parser(h_desc, parent=h_block, attr_index=0)
            b_buffer = h_block[0].serialize(buffer=BytearrayBuffer(),
                                            calc_pointers=False)
            
            self.tag_headers[def_id] = bytes(b_buffer)

        #load all the hash caches we have
        self.hash_cacher.load_all_hashmaps()

        #create a mapping to map tag class id's to their string representation
        self.def_id_int_name_map = {}

        for val in self.tag_lib.id_ext_map:
            key = int.from_bytes(bytes(val, encoding='latin1'), byteorder='big')
            self.def_id_int_name_map[key] = val


    def rip_tags(self, mappath):
        print('Loading map...')

        mapdata = get_rawdata(filepath=mappath)

        halomap = self.build_tag(rawdata=mapdata, def_id='map')
        tag_array = halomap.data.tag_index
        tag_lib = self.tag_lib
        id_ext_map = tag_lib.id_ext_map
        tag_id_map = self.tag_id_map = {}
        path_id_map = self.path_id_map = {}

        hashmap = self.hash_cacher.main_hashmap

        tag_ref_cache   = tag_lib.tag_ref_cache
        reflexive_cache = tag_lib.reflexive_cache
        raw_data_cache  = tag_lib.raw_data_cache

        def_id_map = self.def_id_int_name_map
        tag_headers = self.tag_headers
        tags_by_class = {}

        rebuild_paths = self.rebuild_paths
        rebuild_classes = self.rebuild_classes
        tagsdir = self.tagsdir.replace('/', '\\')

        if not tagsdir.endswith('\\'):
            tagsdir = tagsdir + '\\'

        magic = (PC_TAG_INDEX_HEADER_SIZE - PC_INDEX_MAGIC +
                 halomap.data.map_header.tag_index_offset)

        #change the endianness of the library since we're now
        #going to treat all the meta data as if they were tags
        FieldType.force_big()

        extra_ops = ''
        if rebuild_paths:
            extra_ops += ' and rebuilding tag paths'
        if rebuild_classes:
            extra_ops += ' and tag classes'
        print('Ripping tags%s...' % extra_ops)

        try:
            # make a map of all tags by their ids,
            # a map of all tags by their classes,
            # and a map of all tag paths by their ids,
            for header in tag_array:
                try:
                    def_id = def_id_map[header.class_1.data]
                except Exception:
                    continue
                tag_id = header.id
                curr_tags = tags_by_class[def_id] = tags_by_class.get(def_id,{})

                tag_id_map[tag_id] = curr_tags[tag_id] = header

                if not rebuild_paths:
                    path_id_map[tag_id] = header.tag_data.tag_path

            for def_id in tags_by_class:
                curr_tags = tags_by_class[def_id]

                tag_ref_paths = tag_ref_cache.get(def_id)
                reflexive_paths = reflexive_cache.get(def_id)
                rawdata_paths = raw_data_cache.get(def_id)
                meta_header = tags_by_class[def_id]
                tag_header = tag_headers[def_id]

                print('[%s] %s' % (def_id, len(curr_tags)))

                for tag_id in curr_tags:
                    try:
                        tag_buffer, tag_path = self.get_meta_path(
                            hashmap, curr_tags[tag_id], def_id,
                            set(), rebuild_paths, mapdata,
                            tag_ref_paths, reflexive_paths, rawdata_paths)
                    except Exception:
                        print(format_exc())
                        continue

                    if tag_buffer is None or tag_path is None:
                        #either the tag doesnt actually exist in the map,
                        #or we couldnt determine its path in any way.
                        continue
                    elif rebuild_paths:
                        print('HASH HIT: [%s] %s' % (def_id, tag_path))

                    #print that there was a match and write the tag
                    filepath = tagsdir + tag_path + id_ext_map[def_id]

                    try:
                        # If the path doesnt exist, create it
                        folderpath = dirname(filepath)
                        if not exists(folderpath):
                            makedirs(folderpath)
                        with open(filepath, 'w+b') as f:
                            f.write(tag_header)
                            f.write(tag_buffer)
                    except Exception:
                        print(format_exc())
        except Exception:
            FieldType.force_normal()
            raise

        FieldType.force_normal()


    def get_meta_path(self,
                      hashmap, meta_header, def_id,
                      seen,rebuild_paths, mapdata,
                      tag_ref_paths, reflexive_paths, rawdata_paths):
        tag_path = meta_header.tag_data.tag_path
        tag_meta = meta_header.tag_data.tag_meta

        if meta_header.indexed or isinstance(tag_meta, VoidBlock):
            '''The tag meta data doesnt actually exist, so
            try to get it from the list of tag cache paths.'''
            if rebuild_paths and meta_header.indexed:
                if def_id != 'snd!':
                    tag_path = self.cached_tag_paths.get(def_id, {})\
                               [meta_header.meta_offset]

                    if tag_path is not None:
                        print('CACHE HIT: [%s] %s' % (def_id, tag_path))
            return None, tag_path

        get_nodes = self.tag_lib.get_nodes_by_paths

        #null out the fields that are normally nulled out in tags
        if tag_ref_paths:
            for b in get_nodes(tag_ref_paths[1], tag_meta):
                b.path_pointer = b.path_length = 0
                b.id = 0xFFFFFFFF
        if reflexive_paths:
            for b in get_nodes(reflexive_paths[1], tag_meta):
                b.id = b.pointer = 0
        if rawdata_paths:
            for b in get_nodes(rawdata_paths[1], tag_meta):
                b.unknown = b.raw_pointer = b.pointer = b.id = 0

        #write the tag data to the hash buffer
        tag_buffer = BytearrayBuffer()
        tag_meta.TYPE.writer(tag_meta, writebuffer=tag_buffer)

        if rebuild_paths:
            #get the tag data's hash and try to match it to a path
            tag_path = hashmap.get(md5(tag_buffer).digest())

        return tag_buffer, tag_path
