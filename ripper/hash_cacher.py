from os.path import dirname
from string import digits, ascii_letters
from traceback import format_exc

from reclaimer.halo.hek.handler import HaloHandler
from binilla.handler import Handler
from supyr_struct.tag import Tag


valid_path_chars = " ()-_%s%s" % (digits, ascii_letters)

def bytes_to_hex(taghash):
    hsh = hex(int.from_bytes(taghash, 'big'))[2:]
    return '0x' + '0'*(len(taghash)*2-len(hsh)) + hsh


class HashCacher(Handler):
    default_defs_path = "ripper.defs"
    
    #initialize the class
    def __init__(self, **kwargs):
        Handler.__init__(self, **kwargs)
        self.tagsdir = dirname(__file__)+"\\hash_caches\\"
        
        self.tag_lib = HaloHandler()
        self.tag_lib.print_to_console = True
        self.tag_lib.feedback_interval = 5

        self.hashsize = 16
        self.hashmethod = 'md5'
        self.main_hashmap = {}

    '''this will significantly speed up indexing tags since the default
    Handler.get_def_id method doesnt open each file and try to read
    the 4CC Tag_Cls from the header, but just matches file extensions'''
    get_def_id = Handler.get_def_id


    def build_hashcache(self, cache_name, description, tagsdir, subdir=''):
        tag_lib = self.tag_lib
        tag_lib.tagsdir = tagsdir

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
        
        print('Indexing...')
        tag_lib.mode = 1
        
        tag_lib.index_tags()
        tag_lib.mode = 2
        
        try:
            tagsdir = tag_lib.tagsdir
            tags    = tag_lib.tags

            print('\nFound %s tags of these types\n' % tag_lib.tags_indexed)
            print('    %s' % list(sorted(tags.keys())))

            initial_cache_filenames = set(hashmap.values())
            initial_cache_hashes = set(hashmap.keys())
            get_nodes = self.tag_lib.get_nodes_by_paths
            
            for def_id in sorted(tags):
                tag_coll = tags[def_id]

                if tag_lib.print_to_console:
                    tag_lib.print_to_console = False
                    print("Hashing %s '%s' tags..." % (len(tag_coll), def_id))
                    tag_lib.print_to_console = True
                    
                tag_ref_paths   = tag_lib.tag_ref_cache.get(
                    def_id, ((), ()))[1]
                reflexive_paths = tag_lib.reflexive_cache.get(
                    def_id, ((), ()))[1]
                raw_data_paths  = tag_lib.raw_data_cache.get(
                    def_id, ((), ()))[1]

                subdir = subdir.lstrip(' ')
                
                for filepath in sorted(tag_coll):
                    tag_lib.current_tag = filepath
                    if filepath in initial_cache_filenames:
                        continue
                    try:
                        #if this tag isnt located in the sub
                        #directory being scanned, then skip it
                        if subdir and not filepath.startswith(subdir):
                            continue
                        data = tag_lib.build_tag(
                            filepath=tagsdir + filepath).data

                        '''need to do some extra stuff for certain tags
                        with fields that are normally zeroed out as tags,
                        but arent as meta.'''
                        if def_id == 'effe':
                            # mask away the meta-only flags
                            data.tagdata.flags.data &= 3
                        elif def_id == 'pphy':
                            tagdata = data.tagdata
                            tagdata.wind_coefficient = 0
                            tagdata.wind_sine_modifier = 0
                            tagdata.z_translation_rate = 0

                        hash_buffer = tag_lib.get_tag_hash(
                            data[1], tag_ref_paths, reflexive_paths,
                            raw_data_paths)
                        taghash = hash_buffer.digest()

                        if taghash in initial_cache_hashes:
                            continue
                        
                        if taghash in hashmap:
                            tag_lib.print_to_console = False
                            print(("    COLLISION: hash already exists\n"+
                                   "        hash:%s\n"+
                                   "        path(existing): '%s'\n"+
                                   "        path(colliding):'%s'\n")
                                  % (bytes_to_hex(taghash),
                                     hashmap[taghash], filepath))
                            tag_lib.print_to_console = True
                        else:
                            hashmap[taghash] = filepath
                            
                        #delete the tag and hash buffer to help conserve ram
                        del tag_coll[filepath]
                        del hash_buffer
                        
                    except Exception:
                        print(format_exc())

            tag_lib.mode = 100
            if cache is None:
                print('Building hashcache...')
                cache = self.hashmap_to_hashcache(hashmap, cache_name,
                                                  description)
            
            print('Writing hashcache...')
            cache.serialize(temp=False, backup=False, int_test=False)
            return cache
        except:
            tag_lib.mode = 100
            print(format_exc())
        
        tag_lib.mode = 100


    def add_tag_to_hashmap(self, filepath, hashmap):
        tag_lib  = self.tag_lib
        
        tag  = tag_lib.build_tag(filepath=tag_lib.tagsdir + filepath)
        data = tag.data
        def_id  = tag.def_id      

        hash_buffer = tag_lib.get_tag_hash(data,
                                           tag_lib.tag_ref_cache[def_id],
                                           tag_lib.reflexive_cache[def_id],
                                           tag_lib.raw_data_cache[def_id])
        taghash = hash_buffer.digest()
        #hash buffer to help conserve ram
        del hash_buffer
        
        if taghash in hashmap:
            print(("WARNING: hash already exists\n"+
                   "    hash:%s\n"+
                   "    path(existing): '%s'\n"+
                   "    path(colliding):'%s'\n")
                  % (bytes_to_hex(taghash), hashmap[taghash], filepath))
        else:
            hashmap[taghash] = filepath
        
        return taghash


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
