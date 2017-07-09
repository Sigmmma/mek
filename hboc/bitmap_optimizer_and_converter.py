import gc

from array import array
from os.path import getsize, splitext
from threading import Thread
from time import sleep, time
from traceback import format_exc

from reclaimer.hek.handler import HaloHandler
from reclaimer.hek.defs.bitm import bitm_def

from reclaimer.field_types import *
from supyr_struct.defs.util import *
from .bitmap_converter_windows import *


"""##################"""
### CHANNEL MAPPINGS ###
"""##################"""


"""These channel mappings are for swapping MULTIPURPOSE channels from
pc to xbox format and vice versa from 4 channel source to 4 channel target"""
#                      (A, R, G, B)
PC_ARGB_TO_XBOX_ARGB = (1, 3, 2, 0)
XBOX_ARGB_TO_PC_ARGB = (3, 0, 2, 1)

AY_COMBO_TO_AY   = ( 0, 0 )
AY_COMBO_TO_ARGB = ( 0,  0,  0,  0)

I_FORMAT_NAME_MAP = {
    "A8":0, "Y8":1, "AY8":2, "A8Y8":3,
    "UNUSED1":4, "UNUSED2":5,
    "R5G6B5":6, "UNUSED3":7, "A1R5G5B5":8, "A4R4G4B4":9,
    "X8R8G8B8":10, "A8R8G8B8":11,
    "UNUSED4":12, "UNUSED5":13,
    "DXT1":14, "DXT3":15, "DXT5":16, "P8-BUMP":17}


class BitmapConverter(HaloHandler):

    log_filename = "Bitmap_Converter.log"
    default_defs_path = ''
    
    close_program = False #if set to True the program will close
    main_delay = 0.03 #determines how often the main loop is run
    
    def __init__(self, **kwargs):
        HaloHandler.__init__(self, valid_def_ids=(), **kwargs)
        self.add_def(bitm_def)
        
        self.default_conversion_flags["bitm"] = self.make_default_flags()
        self.root_window = BitmapConverterMainWindow(self)

        #Create and start the tag scanning and editing thread
        self.conversion_main_thread = Thread(target=self.conversion_main)
        self.conversion_main_thread.daemon = True
        self.conversion_main_thread.start()

        
    #the main loop for continuous function handeling
    #add all continuous, non-self-looping, periodic functions here
    def _main_loop(self):
        while not hasattr(self, "root_window"):
            pass
        
        while not self.close_program:
            #we don't want it to run too often or it'll be laggy
            sleep(self.main_delay)
            self.root_window.total_bitmaps = (len(self.tags["bitm"]) -
                                              self.root_window.bad_bitmaps)
            
            #If the program is being told to close then close
            if self.close_program:
                raise SystemExit(0)
            

    def conversion_main(self):
        rw = self.root_window
        while True:
            #we don't want it to run too often or it'll be laggy
            sleep(self.main_delay)

            #if the tags havent been loaded and we are
            #telling the program to continue with conversion
            if (not rw.tags_loaded) and rw.proceed_with_conversion:
                #reset the status variables
                rw.total_pixel_data_to_process     = 0
                rw.remaining_pixel_data_to_process = 0
                rw.bitmaps_found_2d = rw.bitmaps_found_3d = rw.cubemaps_found=0
                rw.elapsed_time  = rw.estimated_time_remaining = 0.0
                rw.total_bitmaps = rw.remaining_bitmaps = rw.bad_bitmaps = 0
                rw.scan_start_time = time()

                if self.index_tags():
                    rw.tags_indexed = True

                    self.load_tags()
                    
                    rw.tags_loaded = True
                    tags = self.tags['bitm']
                    def_flags = self.default_conversion_flags['bitm']

                    #we need to build the list of conversion flags for each tag
                    for filepath in tags:
                        tags[filepath].tag_conversion_settings = list(def_flags)
                        
                    self.initialize_window_variables()
                else:
                    self.current_tag = "No tags found in selected directory."
                    rw.finish_conversion()
                    
                
            elif rw.tags_loaded and rw.proceed_with_conversion:
                #reset the status variables
                rw.elapsed_time = rw.estimated_time_remaining = 0.0
                rw.scan_start_time = time()
                rw.remaining_pixel_data_to_process = rw.total_pixel_data_to_process
                rw.remaining_bitmaps = rw.total_bitmaps
                
                #are we just scanning the folder or are we doing shiz
                if (self.default_conversion_flags["bitm"][READ_ONLY]):
                    #used below for writing the results of the scan
                    logstr = self.make_log_of_all_bitmaps()
                    self.current_tag = (
                        "Log of all bitmaps created successfully.")
                else:
                    """SPLIT OFF INTO THE MAIN PROCESSING ROUTINE"""
                    logstr = self.process_bitmap_tags()
                
                #to keep from bloating the RAM, we delete all loaded bitmap tags
                for filepath in tuple(self.tags['bitm']):
                    del self.tags['bitm'][filepath]
                gc.collect()

                #since we are done with the conversion we write
                #the debug log and change the window variables
                if not rw.conversion_cancelled:
                    if (self.default_conversion_flags["bitm"]
                        [WRITE_LOG] and not self.debug >= 1):
                        self.make_log_file(logstr) #save the debug log to a file
                    else:
                        #if we are debugging we don't want to clutter
                        #the folder with lots of logs, so we just print it
                        print(logstr)

                    rw.finish_conversion()


    #run the list update function on the main thread
    def create_initial_tag_list(self):
        self.root_window.tag_list_window.sort_displayed_tags_by(0)

    def make_default_flags(self):
        '''
        If no settings have been defined specifically
        for a tag then the flags below will be used
        
        the first 4 conversion flags are global conversion
        flags and aren't assigned on a per-tag basis

          PRUNE TIFF: Prune the compressed tiff data from the tags
          RENAME OLD: Rename old tags instead of deleting them
          READ ONLY: compiles a list of all bitmaps and what their types, 
                    sizes, etc are instead of converting in any way
          WRITE LOG: Write debug Log
        
          PLATFORM: Platform to save as(True = Xbox, False = PC)
          SWIZZLED: True = save as swizzled, False = save as deswizzled
          DOWNRES: Number of times to cut resolution in half
          MULTI SWAP: 0 = don't swap multipurpose channels,
                      1 = swap for xbox,  2= swap for pc
          CUTOFF BIAS: when reducing a channel to 1 bit, values above
                       this are snapped to 1 and below it are snapped to 0
          P8 MODE: P8-Bump Conversion Mode (True = Average Bias Mode,
                                            False = Auto Bias Mode)
          MONO KEEP: Channel to keep when converting to A8 or Y8
                     (True = Alpha, False = Intensity)
          MONO SWAP: Swap Alpha and Intensity (Only for A8Y8)
          CK TRANS: Preserve Color Key transparency  (A transparent pixel
                         in DXT1 has black for it's Red, Green, and Blue)
          MIP GEN: Generate mipmaps if a texture doesn't have them down to 1x1
          GAMMA: The gamma exponent to use when downressing
                 a bitmap by merging pixels
          NEW FORMAT: -1=unchanged, 0=A8, 1=Y8, 2=AY8, 3=A8Y8,
                       6=R5G6B5 8=A1R5G5B5, 9=A4R4G4B4, 14=DXT1,
                       15=DXT3, 16=DXT5, 17=P8/A8R8G8B8/X8R8G8B8
        '''
        
        flags = [False, True, False, True, False, False,
                 '0', 0, '127', False, False, False,
                 False, FORMAT_NONE, False, 1.0, " "]

        return flags


    def initialize_window_variables(self):
        rw = self.root_window
        rw.bitmaps_found_2d  = rw.bitmaps_found_3d = 0
        rw.cubemaps_found    = rw.total_bitmaps    = 0
        rw.remaining_bitmaps = rw.bad_bitmaps      = 0
        
        tags_to_remove = []

        #for the conversion variables we want to return
        #a count on how many bitmaps are of what type
        for filepath in self.tags['bitm']:

            #only run if the bitmap contains bitmaps
            tag = self.tags['bitm'][filepath]
            if tag.bitmap_count() and tag.is_power_of_2_bitmap():
                
                b_type = tag.bitmap_type()
                b_format = tag.bitmap_format()
                if b_type == 2:
                    rw.cubemaps_found += 1
                elif b_type == 1:
                    rw.bitmaps_found_3d += 1
                else:
                    rw.bitmaps_found_2d += 1
                
                rw.total_pixel_data_to_process += tag.pixel_data_bytes_size()
            else:
                if tag.bitmap_count():
                    print("Non power-of-2 bitmap found.\n%s\n\n"%tag.filepath)
                else:
                    print("Bitmap with no bitmap data found.\n%s\n\n"%
                          tag.filepath)
                tags_to_remove.append(filepath)
                rw.bad_bitmaps += 1
                
            rw.total_bitmaps += 1

        for filepath in tags_to_remove:
            del self.tags['bitm'][filepath]
        del tags_to_remove
            
        rw.tag_list_window.build_tag_sort_mappings()
        
        #set the status variables
        rw.remaining_pixel_data_to_process = rw.total_pixel_data_to_process
        rw.remaining_bitmaps = len(self.tags['bitm']) - rw.bad_bitmaps
        
        self.current_tag = ("Tags loaded... Please select tags in the "+
                            "tags list window and specify\nthe conversion "+
                            "settings for them in this window.\nWhen you "+
                            'are finished hit "Convert"')
        
        #set up the hack to allow the tag list to
        #be displayed instantly on loading a tagset
        rw.after(0, self.create_initial_tag_list)
        rw.finish_scanning()



    #this function is called by the conversion_main and
    #will loop through all the tags in the collection and
    #process them however each tag's conversion flags say to.
    def process_bitmap_tags(self):
        rw = None
        if hasattr(self, "root_window"):
            rw = self.root_window
        
        #used below for debug writing
        logstr = "Debug log for Halo Bitmap Converter\n"
        def_flags = self.default_conversion_flags['bitm']
        conversion_report = {'bitm':{}}

        #loop through each tag
        for filepath in sorted(self.tags['bitm']):
            tag = self.tags['bitm'][filepath]
            
            if rw is not None and rw.conversion_cancelled:
                break
            
            self.current_tag = filepath

            #this may change after the below function
            #so we get it before that happens
            tagsize = tag.pixel_data_bytes_size()
            if get_will_be_processed(tag, def_flags):
                """DO THE CONVERSION NOW"""
                try:
                    convert_bitmap_tag(tag, root_window=rw, filepath=filepath,
                                   conversion_report=conversion_report['bitm'], 
                                   prune_tiff=def_flags[PRUNE_TIFF])
                except:
                    print(format_exc())
                    conversion_report['bitm'][filepath] = False
            else:
                conversion_report['bitm'][filepath] = None
            rw.remaining_pixel_data_to_process -= tagsize
            rw.remaining_bitmaps -= 1


        if rw is not None and rw.conversion_cancelled:
            self.current_tag = "Conversion cancelled."
            
            rw.display_new_text = True
            rw.btn_start.config(text="Convert")
            rw.enable_global_settings()
            rw.conversion_cancelled = False
            logstr += "Conversion Cancelled."
        else:
            try:
                backup = self.default_conversion_flags['bitm'][RENAME_OLD]
                '''depending on the conversion settings we
                either rename or delete the original files'''
                logstr += self.make_write_log(conversion_report, backup=backup)
            except:
                print("ERROR OCCURRED WHILE TRYING TO WRITE "+
                      "DEBUG LOG AND/OR RENAME TEMP FILES")
                print(format_exc())
            
            self.current_tag = "Finished converting tags"

        return logstr



    #used when doing a read-only scan of a tagset to figure out what's what
    def make_log_of_all_bitmaps(self):
        logstr = ("CE-XBOX Bitmap Converter: tagset scan results\n\n\n"+
                  "These are the bitmaps located in the tags folder "+
                  "organized by type and then by format.\n\n")
        
        valid_formats = (0,1,2,3,6,8,9,10,11,14,15,16,17)

        base_str = "Bitmap %s --- WxHxD: %sx%sx%s --- Mipmaps: %s\n"

        tag_counts = [0, 0, 0]

        formatted_strs = {}
        tag_header_strs = ["\n\n2D Textures:\n    Count = ",
                           "\n\n3D Textures:\n    Count = ",
                           "\n\nCubemaps:\n    Count = "]
        format_names = ["A8", "Y8", "AY8", "A8Y8", '', '',
                        "R5G6B5", '', "A1R5G6B5", "A4R4G4B4",
                        "X8R8G8B8", "A8R8G8B8", '', '', "DXT1",
                        "DXT3", "DXT5", "P8-Bump"]

        #so we can sort bitmaps by filesize we'll create a dict to hold all
        #the strings before we concate them so we can sort them later by size
        tag_info_strs = {}


        #add dicts for all three types to the tag_info_strings
        for b_type in (0, 1, 2):
            formatted_strs[b_type] = ['']*18
            tag_info_strs[b_type]  = ['']*18

            #and add the formats to each of these new dicts
            for b_format in valid_formats:
                formatted_strs[b_type][b_format] = ("\n\n"+" "*4+"%s Format" %
                                                    format_names[b_format])
                tag_info_strs[b_type][b_format] = {}


        #loop through each tag and create a
        #string that details each bitmap in it
        for filepath in self.tags['bitm']:
            tag = self.tags['bitm'][filepath]
            filesize = (getsize(tag.filepath)-
                        tag.color_plate_data_bytes_size())//1024
            tagstrs  = tag_info_strs[tag.bitmap_type()][tag.bitmap_format()]
            
            #this is the string that holds the data pertaining to this tag
            tagstr = ("\n"+" "*8+filepath+" "*8+"Compiled tag size = %sKB\n" %
                      {True:"less than 1", False:str(filesize)}[filesize <= 0])

            for i in range(tag.bitmap_count()):
                tagstr += (" "*12 + base_str %
                           (i, tag.bitmap_width(i), tag.bitmap_height(i),
                            tag.bitmap_depth(i), tag.bitmap_mipmaps_count(i)) )

            #check if the strings list exists in the spot with 
            if filesize in tagstrs:
                tagstrs[filesize].append(tagstr)
            else:
                tagstrs[filesize] = [tagstr]


        #Take all the tag strings generated above and concatenate them
        #to the appropriate b_format string under the appropriate b_type
        for b_type in (0, 1, 2):
            for b_format in valid_formats:
                for b_size in reversed(sorted(tag_info_strs[b_type][b_format])):
                    for tagstr in tag_info_strs[b_type][b_format][b_size]:
                        tag_counts[b_type] += 1
                        formatted_strs[b_type][b_format] += tagstr


        #concate all the strings to the
        #log in order of b_type and b_format
        for b_type in (0, 1, 2):
            logstr += (tag_header_strs[b_type] + str(tag_counts[b_type]) +
                       "\n" + ''.join(formatted_strs[b_type]))

        return logstr


def convert_bitmap_tag(tag, **kwargs):
    '''tons of possibilities here. not gonna try to name
    them. Basically this is the main conversion routine'''
    conversion_flags = tag.tag_conversion_settings
    tagsdir = tag.handler.tagsdir

    root_window = kwargs.get("root_window",None)
    tagpath = kwargs.get("tagpath",tag.filepath.split(tagsdir)[-1])
    conversion_report = kwargs.get("conversion_report",{})
    prune_tiff = kwargs.get("prune_tiff", False)
    
    '''if ANY of the bitmaps does not have a power of 2
    dimensions height/width/depth then we need to break
    out of this since we can't work with it properly'''
    for i in range(tag.bitmap_count()):
        if not(tag.is_power_of_2_bitmap(i)):
            conversion_report[tagpath] = False
            return False
    

    """GET THE FLAGS FOR THE CONVERSION SETTINGS
    THAT DON'T DEPEND ON BITMAP FORMAT OR TYPE"""
    save_as_xbox = conversion_flags[PLATFORM]
    swizzle_mode = conversion_flags[SWIZZLED]
    downres_amount = int(conversion_flags[DOWNRES])
    alpha_cutoff_bias = int(conversion_flags[CUTOFF_BIAS])
    p8_mode = conversion_flags[P8_MODE]
    channel_to_keep = conversion_flags[MONO_KEEP]
    ck_transparency = conversion_flags[CK_TRANS]
    new_format = FORMAT_NAME_MAP[conversion_flags[NEW_FORMAT]]
    multi_swap = conversion_flags[MULTI_SWAP]
    mono_swap = conversion_flags[MONO_SWAP]
    gamma = conversion_flags[GAMMA]
    generate_mipmaps = conversion_flags[MIP_GEN]
    export_format = conversion_flags[EXTRACT_TO]

    processing = process_bitmap_tag(tag)

    """CREATE THE BITMAP CONVERTER MODULE"""
    bm = ab.Arbytmap()

    '''BEFORE WE TRY TO LOAD THE PIXEL DATA WE NEED TO
    MAKE SURE THE DESCRIPTION OF EACH BITMAP IS WORKABLE'''
    bad_bitmaps = tag.sanitize_mipmap_counts()

    if len(bad_bitmaps) > 0:
        print("WARNING: BAD BITMAP BLOCK INFORMATION ENCOUNTERED "+
              "WHILE PROCESSING THIS TAG:\n", tagpath, "\n",
              "THE INDEXES THAT WERE BAD ARE AS FOLLOWS:", bad_bitmaps,
              "\nCannot process bitmap until you manually fix this.\n")
        load_status = False
    else:
        '''CONVERT THE RAW PIXEL DATA INTO ORGANIZED ARRAYS OF PIXELS'''
        load_status = tag.parse_bitmap_blocks()

    #If an error was encountered during the load
    #attempt or the conversion was cancelled we quit
    if root_window and (not load_status or root_window.conversion_cancelled):
        conversion_report[tagpath] = False
        return False
        
    """LOOP THROUGH ALL THE BITMAPS, FIGURE OUT
    HOW THEY'RE BEING CONVERTED AND CONVERT THEM"""
    for i in range(tag.bitmap_count()):
        format = FORMAT_NAME_MAP[tag.bitmap_format(i)]
        type   = TYPE_NAME_MAP[tag.bitmap_type(i)]
        target_format = new_format

        #get the texture block to be loaded
        tex_block = list(tag.data.tagdata.processed_pixel_data.data[i])
        tex_info = tag.tex_infos[i]

        """MAKE SOME CHECKS TO FIGURE OUT WHICH FORMAT WE ARE
        REALLY CONVERTING TO (IT'S NOT STRAIGHTFORWARD)"""
        if target_format == ab.FORMAT_P8:
            #since this button is shared between
            #p-8 and 32 bit we make another check
            #also make sure this ISN'T a cubemap
            if (format in (ab.FORMAT_R5G6B5, ab.FORMAT_A1R5G5B5,
                           ab.FORMAT_A4R4G4B4, ab.FORMAT_X8R8G8B8,
                           ab.FORMAT_A8R8G8B8) and type != ab.TYPE_CUBEMAP):
                target_format = ab.FORMAT_P8
            elif format == ab.FORMAT_Y8:
                target_format = ab.FORMAT_X8R8G8B8
            else:
                target_format = ab.FORMAT_A8R8G8B8
                
        elif target_format not in ab.VALID_FORMATS:
            target_format = format
        else:
            if target_format in ab.DDS_FORMATS and type == "3D":
                target_format = format
                print("CANNOT CONVERT 3D TEXTURES TO DXT FORMAT.")
                
            if not(channel_to_keep) and target_format == ab.FORMAT_A8:
                target_format = ab.FORMAT_Y8
                
            """ SINCE THESE THREE FORMATS CAN BE EASILY INTERCHANGED JUST
            BY CHANGING THE FORMAT IDENTIFIER, THAT'S WHAT WE'LL DO"""
            if (format in (ab.FORMAT_A8, ab.FORMAT_Y8, ab.FORMAT_AY8) and
                target_format in (ab.FORMAT_A8, ab.FORMAT_Y8, ab.FORMAT_AY8)):
                tex_info["format"] = format = target_format


        """CHOOSE WHICH CHANNEL MAPPINGS TO USE
        AND DO EXTRA TARGET FORMAT CHECKS"""
        channel_mapping, channel_merge_mapping, target_format = \
                         get_channel_mappings(format, mono_swap, target_format,
                                              multi_swap, channel_to_keep)
        palette_picker = None
        palettize = True
        
        """IF WE ARE CONVERTING TO P8 THIS IS
        WHERE WE SELECT THE SPECIFIC SETTINGS"""
        if format == ab.FORMAT_P8:
            palette_picker = P8_PALETTE.argb_array_to_p8_array_auto
        elif target_format != ab.FORMAT_P8:
            palettize = False
        elif ab.FORMAT_CHANNEL_COUNTS[format] != 4:
            pass
        elif ck_transparency and format not in (ab.FORMAT_X8R8G8B8,
                                                ab.FORMAT_R5G6B5):
            #auto-bias
            if p8_mode == 0:
                palette_picker = P8_PALETTE.argb_array_to_p8_array_auto_alpha
            else:#average-bias
                palette_picker = P8_PALETTE.argb_array_to_p8_array_average_alpha
        elif p8_mode == 0:
            #auto-bias
            palette_picker = P8_PALETTE.argb_array_to_p8_array_auto
        else:
            #average-bias
            palette_picker = P8_PALETTE.argb_array_to_p8_array_average

        #we want to preserve the color key transparency of
        #the original image if converting to the same format
        if (format == target_format and
            target_format in (ab.FORMAT_P8, ab.FORMAT_DXT1)):
            ck_transparency = True

        """LOAD THE TEXTURE INTO THE BITMAP CONVERTER"""
        bm.load_new_texture(texture_block = tex_block,
                            texture_info = tex_info)
        
        #build the initial conversion settings list from the above settings
        conv_settings = dict(
            swizzle_mode=swizzle_mode, one_bit_bias=alpha_cutoff_bias,
            downres_amount=downres_amount, palettize=palettize,
            color_key_transparency=ck_transparency,
            gamma=gamma, generate_mipmaps=generate_mipmaps)


        #add the variable settings into the conversion settings list
        conv_settings["target_format"] = target_format
        if channel_mapping is not None:
            conv_settings["channel_mapping"] = channel_mapping
        if channel_merge_mapping is not None:
            conv_settings["channel_merge_mapping"] = channel_merge_mapping
        if palette_picker is not None:
            conv_settings["palette_picker"] = palette_picker

        if conv_settings["target_format"] != ab.FORMAT_P8:
            conv_settings["palettize"] = False

        """LOAD THE CONVERSION SETTINGS INTO THE BITMAP CONVERTER"""
        bm.load_new_conversion_settings(**conv_settings)

        """RUN THE CONVERSION ROUTINE ON THE BITMAP CONVERTOR"""
        status = True
        if processing:
            status = bm.convert_texture()
        if export_format != " ":
            path = bm.filepath
            if tag.bitmap_count() > 1:
                path += ("_"+str(i))
            bm.save_to_file(output_path=path, ext=export_format)
                

        """IF THE CONVERSION WAS SUCCESSFUL WE UPDATE THE
        TAG'S DATA TO THE NEW FORMAT AND SWIZZLE MODE.
        IF WE WERE ONLY EXTRACTING THE TEXTURE WE DON'T RESAVE THE TAG"""
        if status and processing:
            tex_root = tag.data.tagdata.processed_pixel_data.data[i]

            #set the data block to the newly converted one
            tex_root.parse(initdata=bm.texture_block)

            #set the flag showing that the bitmap
            #is either swizzled or not swizzled
            tag.swizzled(bm.swizzled, i)

            #change the bitmap format to the new format
            tag.bitmap_format(i, I_FORMAT_NAME_MAP[target_format])
        elif not (extracting_texture(tag) or prune_tiff):
            print("Error occurred while attempting to convert the tag:")
            print(tagpath+"\n")
            conversion_report[tagpath] = False
            return False

    #Prune the original TIFF data from the tag
    if prune_tiff:
        tag.data.tagdata.compressed_color_plate_data.data = bytearray()

    if processing:
        """RECALCULATE THE BITMAP HEADER AND FOOTER
        DATA AFTER POSSIBLY CHANGING IT ABOVE"""
        tag.sanitize_bitmaps()
        
        #SET THE TAG'S CHARACTERISTICS TO XBOX OR PC FORMAT
        tag.set_platform(save_as_xbox)

        #SET THE "PROCESSED BY RECLAIMER" FLAG
        tag.processed_by_hboc(True)
        
        #IF THE FORMAT IS P8 OR PLATFORM IS XBOX WE NEED TO ADD PADDING
        tag.add_bitmap_padding(save_as_xbox)

    """FINISH BY RESAVING THE TAG"""
    if processing or prune_tiff:
        try:
            save_status = tag.serialize()
            conversion_report[tagpath] = True
        except Exception:
            print(format_exc())
            conversion_report[tagpath] = save_status = False
        return save_status
    elif export_format == " ":
        conversion_report[tagpath] = False
        return False
    
    conversion_report[tagpath] = None
    return None

def get_channel_mappings(format, mono_swap, target_format,
                         multi_swap, channel_to_keep):
    """Goes through a ton of checks to figure out which channel
    mapping to use for converting(and returns it). Also checks a
    few exception cases where converting to that format would
    be bad and instead resets the target format to the source format"""
    
    channel_count = ab.FORMAT_CHANNEL_COUNTS[format]
    target_channel_count = ab.FORMAT_CHANNEL_COUNTS[target_format]
    channel_mapping = None
    channel_merge_mapping = None
    if channel_count == 4:
        if target_channel_count == 4:
            """THIS TAKES CARE OF ALL THE MULTIPURPOSE CHANNEL SWAPPING"""
            if multi_swap == 1:
                #SWAP CHANNELS FROM PC TO XBOX
                channel_mapping = PC_ARGB_TO_XBOX_ARGB

            elif multi_swap == 2:
                #SWAP CHANNELS FROM XBOX TO PC
                channel_mapping = XBOX_ARGB_TO_PC_ARGB

        elif target_format in (ab.FORMAT_A8, ab.FORMAT_Y8,
                             ab.FORMAT_AY8, ab.FORMAT_P8):
            """THIS AND THE NEXT ONE TAKE CARE OF CONVERTING
            FROM A 4 CHANNEL FORMAT TO MONOCHROME"""
            if channel_to_keep:
                #keep the alpha channel
                channel_mapping = ab.ANYTHING_TO_A
                if format == ab.FORMAT_P8:
                    channel_merge_mapping = ab.M_ARGB_TO_A
            else:
                #keep the intensity channel
                channel_merge_mapping = ab.M_ARGB_TO_Y

        elif target_format == ab.FORMAT_A8Y8:
            if mono_swap:
                channel_merge_mapping = ab.M_ARGB_TO_YA
            else:
                channel_merge_mapping = ab.M_ARGB_TO_AY

    elif channel_count == 2:
        """THIS TAKES CARE OF CONVERTING FROM A
        2 CHANNEL FORMAT TO OTHER FORMATS"""

        if format == ab.FORMAT_A8Y8:
            if mono_swap:
                if target_format == ab.FORMAT_A8Y8:
                    channel_mapping = ab.AY_TO_YA
                    
                elif target_channel_count == 4:
                    channel_mapping = ab.YA_TO_ARGB
                
            elif target_channel_count == 4:
                channel_mapping = ab.AY_TO_ARGB
                
            elif target_format in (ab.FORMAT_A8, ab.FORMAT_Y8, ab.FORMAT_AY8):
                if channel_to_keep:
                    #keep the alpha channel
                    channel_mapping = ab.ANYTHING_TO_A
                else:
                    #keep the intensity channel
                    channel_mapping = ab.AY_TO_Y
    
    elif channel_count == 1:
        """THIS TAKES CARE OF CONVERTING FROM A
        1 CHANNEL FORMAT TO OTHER FORMATS"""
        if target_channel_count == 4:
            if format == ab.FORMAT_A8:
                channel_mapping = ab.A_TO_ARGB
                    
            elif format == ab.FORMAT_Y8:
                channel_mapping = ab.Y_TO_ARGB
                    
            elif format == ab.FORMAT_AY8:
                channel_mapping = AY_COMBO_TO_ARGB
                
        elif target_channel_count == 2:
            if format == ab.FORMAT_A8:
                channel_mapping = ab.A_TO_AY
                
            elif format == ab.FORMAT_Y8:
                channel_mapping = ab.Y_TO_AY
                
            elif format == ab.FORMAT_AY8:
                channel_mapping = AY_COMBO_TO_AY
                
    return(channel_mapping, channel_merge_mapping, target_format)
