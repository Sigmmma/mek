from os.path import dirname
from time import time
from string import digits, ascii_letters
from traceback import format_exc

from reclaimer.hek.handler import HaloHandler,\
     bytes_to_hex, BAD_DEPENDENCY_HASH, CANT_PARSE_TAG_HASH
from binilla.handler import Handler
from supyr_struct.tag import Tag


valid_path_chars = " ()-_%s%s" % (digits, ascii_letters)


def clear_meta_only_fields(tagdata, def_id):
    if def_id == 'effe':
        # mask away the meta-only flags
        tagdata.flags.data &= 3
    elif def_id == 'pphy':
        # set the meta-only values to 0
        tagdata.wind_coefficient = 0
        tagdata.wind_sine_modifier = 0
        tagdata.z_translation_rate = 0
    elif def_id == 'scnr':
        # remove the sbsp references from the meta
        for b in tagdata.structure_bsps.STEPTREE:
            b.bsp_pointer = b.bsp_size = b.bsp_magic = 0
    elif def_id == 'bitm':
        # clear some meta-only fields
        for b in tagdata.bitmaps.STEPTREE:
            b.flags.data &= 63
            b.pixels_meta_size = 0
            b.bitmap_id_unknown1  = b.bitmap_id_unknown2 = 0
            b.bitmap_data_pointer = b.base_address = 0


def sort_tags_for_hashing(all_tag_paths):
    sorted_def_ids = []

    # the order these are sorted is chosen to minimize
    # the time it would take for each to be hashed.
    for def_id in (
        # hash the "leaf" tags first
        'bitm', 'boom', 'cdmg', 'colo', 'devc', 'hmt ', 'phys',
        'pphy', 'snde', 'shdr', 'str#', 'trak', 'ustr', 'wind',

        # then all the tags that can NEVER be self referential
        'senv', 'soso', 'sgla', 'smet', 'spla', 'swat', 'sotr',
        'schi', 'scex', 'hud#', 'metr', 'vcky', 'ant!', 'font',
        'flag', 'dobc', 'mply', 'ngpr', 'cont', 'deca', 'rain',
        'lens', 'ligh', 'mgs2', 'elec',

        # then all the tags that COULD be self referential
        'snd!', 'pctl', 'lsnd', 'jpt!', 'unhi', 'wphi', 'grhi',
        'udlg', 'mod2', 'mode', 'antr', 'coll', 'devi', 'item',
        'unit', 'obje', 'part', 'effe', 'foot',
        'garb', 'plac', 'scen', 'ssce', 'lifi', 'mach', 'ctrl',
        'Soul', 'DeLa', 'eqip', 'itmc', 'sky ', 'glw!', 'fog ', 
        'proj', 'vehi', 'weap', 'bipd', 'actr', 'actv',
        'tagc', 'hudg', ):  # 'sbsp', 'scnr', 'matg'):
        if def_id in all_tag_paths:
            sorted_def_ids.append(def_id)

    return sorted_def_ids


class HashCacher(Handler):
    default_defs_path = "refinery.defs"
    tag_lib = None
    stop_hashing = False
    
    #initialize the class
    def __init__(self, **kwargs):
        Handler.__init__(self, **kwargs)
        self.tagsdir = dirname(__file__) + "\\hashcaches\\"

        self.hashsize = 16
        self.hashmethod = 'md5'
        self.main_hashmap = {}

    def build_hashcache(self, cache_name, description, hash_dir=""):
        start = time()
        if self.tag_lib is None:
            raise TypeError("tag_lib not set. Cannot load tags for hashing.")
        tag_lib = self.tag_lib
        tagsdir = tag_lib.tagsdir
        if not hash_dir:
            hash_dir = tasgdir

        print('Attempting to load existing hashcache...')
        # its faster to try and just update the hashcache if it already exists
        try:
            cache = self.build_tag(
                filepath=self.tagsdir + cache_name + ".hashcache")
            hashmap = self.hashcache_to_hashmap(cache)
            description = description.rstrip('\n')
            if len(description):
                cache.data.cache_description = description
            print("Existing hashcache loaded.\n"+
                  "    Contains %s hashes" % len(hashmap))
        except Exception:
            cache = None
            hashmap = {}
            print("Failed to locate and/or load an existing hashcache.\n"+
                  "    Creating a hashcache from scratch instead.")

        if self.stop_hashing:
            print('Hashing cancelled.')
            self.stop_hashing = False
            return
        
        print('Indexing...')
        
        tag_lib.index_tags(hash_dir)
        try:
            tagsdir = tag_lib.tagsdir
            tags = tag_lib.tags
            defs = tag_lib.defs

            # we need to make a deep copy of the tags since the tags
            # will be deleted from the handler once they've been hashed
            all_tag_paths = {}
            for def_id in tags:
                if not tags.get(def_id):
                    continue
                all_tag_paths[def_id] = tuple(sorted(tags[def_id].keys()))

            sorted_def_ids = sort_tags_for_hashing(all_tag_paths)

            print('\nFound %s tags of these %s types' % (
                tag_lib.tags_indexed, len(sorted_def_ids)))
            print(sorted_def_ids)
            print("\nIf a tag already exists in the hashmap " +
                  "then its name wont be printed below.\n")

            init_cache_names = set(hashmap.values())
            init_cache_hashes = set(hashmap.keys())
            get_nodes = self.tag_lib.get_nodes_by_paths

            hashes = {}

            for def_id in sorted_def_ids:
                tag_paths = all_tag_paths[def_id]
                tag_def = defs.get(def_id)
                if tag_def is None:
                    continue

                if self.stop_hashing:
                    print('Hashing cancelled.')
                    self.stop_hashing = False
                    return

                print("Hashing %s '%s' tags..." % (len(tag_paths), def_id))
                
                for filepath in tag_paths:
                    if self.stop_hashing:
                        print('Hashing cancelled.')
                        self.stop_hashing = False
                        return

                    if filepath in init_cache_names or filepath in hashes:
                        taghash = hashes[filepath]
                        if taghash is BAD_DEPENDENCY_HASH:
                            print("        ERROR: Could not hash the above " +
                                  "tag due to a bad dependency.")
                        elif taghash is CANT_PARSE_TAG_HASH:
                            print("        ERROR: Could not hash the above " +
                                  "tag as an error occurred while parsing.")
                        continue
                    try:
                        print("    %s" % filepath)

                        tag = tag_def.build(filepath=tagsdir + filepath)

                        if self.stop_hashing:
                            print('Hashing cancelled.')
                            self.stop_hashing = False
                            return

                        tag_lib.get_tag_hash(tag.data[1], def_id, filepath,
                                             hashes)

                        # if the taghash isn't none, it's a tuple containing
                        # the md5 digest of the hash as bytes and a string
                        taghash = hashes.get(filepath)

                        if taghash is BAD_DEPENDENCY_HASH:
                            print("        ERROR: Could not hash the above " +
                                  "tag due to a bad dependency.")
                            continue
                        elif taghash is CANT_PARSE_TAG_HASH:
                            print("        ERROR: Could not hash the above " +
                                  "tag as an error occurred while parsing.")
                            continue

                        taghash = taghash[0]
                        
                        if taghash in init_cache_hashes or taghash in hashmap:
                            print(("        COLLISION: hash already exists\n" +
                                   "            hash: %s\n" +
                                   "            existing tag: '%s'\n")
                                  % (bytes_to_hex(taghash), hashmap[taghash]))
                        else:
                            hashmap[taghash] = filepath

                    except Exception:
                        print(format_exc())
                        print("Could not calculate the above tag's hash.")

            if self.stop_hashing:
                print('Hashing cancelled.')
                self.stop_hashing = False
                return

            if cache is None:
                print('Building hashcache...')
                cache = self.hashmap_to_hashcache(
                    hashmap, cache_name, description)

            if self.stop_hashing:
                print('Hashing cancelled.')
                self.stop_hashing = False
                return

            print('Writing hashcache...')
            cache.serialize(temp=False, backup=False,
                            int_test=False, calc_pointers=False)
        except:
            print(format_exc())
        print('Hashing completed. Took %s seconds' % (time() - start))
        return cache

    def hashmap_to_hashcache(self, hashmap, cache_name="untitled",
                             cache_description='<no description>'):
        cache = self.build_tag(def_id='hashcache')
        
        cache.data.header.hashsize   = self.hashsize
        cache.data.header.hashmethod = self.hashmethod
        cache.data.cache_name        = str(cache_name)
        cache.data.cache_description = str(cache_description)

        cache_name = ''.join(c for c in cache_name if c in valid_path_chars)
        if not cache_name:
            cache_name = "untitled"
        cache.filepath = self.tagsdir + cache_name + ".hashcache"
        
        cache_array = cache.data.cache
        cache_array.extend(len(hashmap))
        
        i = 0
        for taghash in sorted(hashmap):
            cache_array[i].hash  = taghash
            cache_array[i].value = hashmap[taghash]
            i += 1

        return cache

    def hashcache_to_hashmap(self, hashcache):
        hashmap = {}
        cache_array = hashcache.data.cache
        for mapping in cache_array:
            hashmap[mapping.hash] = mapping.value

        return hashmap

    def load_all_hashmaps(self):
        self.index_tags()
        self.load_tags()
        
        for hashcache in self.tags['hashcache'].values():
            self.update_hashmap(hashcache)

    def update_hashmap(self, new_hashes, hashmap=None, overwrite=False):
        if hashmap is None:
            hashmap = self.main_hashmap
            
        if isinstance(new_hashes, dict):
            if overwrite:
                hashmap.update(new_hashes)
                return
            
            for taghash in new_hashes:
                if taghash not in hashmap:
                    hashmap[taghash] = new_hashes[taghash]
                    
        elif isinstance(new_hashes, Tag):
            new_hashes = new_hashes.data.cache
            
            if overwrite:
                for mapping in new_hashes:
                    hashmap[mapping.hash] = mapping.value
                return
            
            for mapping in new_hashes:
                taghash = mapping.hash
                
                if taghash not in hashmap:
                    hashmap[taghash] = mapping.value
