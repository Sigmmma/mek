'''
This whole module is a horrid mess from years back. I want to throw it all
away and replace it, but that would be a lot of effort, and this DOES work
'''
from .mtTkinter import *

import threading
import tkinter.filedialog

from time import time, sleep
from os.path import dirname, join
from reclaimer.hek.defs.objs.bitm import *

'''Constants that determine which index
each of the flags are in per tag'''
PRUNE_TIFF = 0
RENAME_OLD = 1
READ_ONLY = 2
WRITE_LOG = 3
PLATFORM = 4
SWIZZLED = 5
DOWNRES = 6
MULTI_SWAP = 7
CUTOFF_BIAS = 8
P8_MODE = 9
MONO_KEEP = 10
MONO_SWAP = 11
CK_TRANS = 12
NEW_FORMAT = 13
MIP_GEN = 14
GAMMA = 15
EXTRACT_TO = 16

#used when displaying the format and type in windows
BITMAP_TYPE_STRINGS = ("2D Texture", "3D Texture", "Cubemap", "????")
BITMAP_FORMAT_STRINGS = ("A8", "Y8", "AY8", "A8Y8", "????", "????", "R5G6B5",
                         "????", "A1R5G5B5", "A4R4G4B4", "X8R8G8B8", "A8R8G8B8",
                         "????", "????", "DXT1", "DXT3", "DXT5", "P8 Bump")
BITMAP_SHORT_TYPE_STRINGS = ("2D", "3D", "CUBE", "WHITE")

_unknown = "UNKNOWN FORMAT  "
BITMAP_FORMAT_LITERALS = ("A8"+" "*16, "Y8"+" "*16, "AY8"+" "*14,
                          "A8Y8"+" "*12, _unknown, _unknown, "R5G6B5"+" "*7,
                          _unknown, "A1R5G5B5"+" "*2, "A4R4G4B4"+" "*2,
                          "X8R8G8B8"+" "*3,"A8R8G8B8"+" "*3, _unknown,
                          _unknown, "DXT1"+" "*12, "DXT3"+" "*12,
                          "DXT5"+" "*12,"P8"+" "*16)
BITMAP_TYPE_LITERALS = ("2D Bitmap   ", "3D Bitmap   ",
                        "Cube Map    ", "White      ")


def extracting_texture(tag):
    '''determines if a texture extraction is to take place'''
    return tag.tag_conversion_settings[EXTRACT_TO] != " "

def process_bitmap_tag(tag):
    '''this function will return whether or not the conversion
    routine below should be run on a bitmap based on its format,
    type, etc and how they compare to the conversion variablers'''
    
    flags = tag.tag_conversion_settings
    
    #check if the bitmap has already been processed, or
    #is a PC bitmap or if we are just creating a debug log
    if tag.processed_by_hboc or not(tag.is_xbox_bitmap):
        format = tag.bitmap_format()

        #if all these are true we skip the tag
        if ( flags[DOWNRES]=='0' and flags[MULTI_SWAP] == 0 and
             flags[NEW_FORMAT] == FORMAT_NONE and flags[MIP_GEN]== False and
             tag.is_xbox_bitmap == flags[PLATFORM] and
             (flags[MONO_SWAP] == False or format!= FORMAT_A8Y8) and
             (tag.swizzled() == flags[SWIZZLED] or
              FORMAT_NAME_MAP[format] in ab.DDS_FORMATS) ):
            return False
    return True

#compares all the conversion settings of the tag
#with the tag's data to tell if it will be processed
"""THIS IS USED TO DETERMINE IF THE Convert_Bitmap_Tags SHOULD EVEN BE RUN"""
def get_will_be_processed(tag, conv_flags):
    #only run if the bitmap contains bitmaps and we are NOT in read-only mode
    if (tag.bitmap_count()==0) or conv_flags[READ_ONLY]:
        return False
    
    return conv_flags[PRUNE_TIFF] or (process_bitmap_tag(tag) or extracting_texture(tag))


'''ENTER A DESCRIPTION FOR THIS CLASS WHEN I HAVE TIME'''
class BitmapConverterMainWindow(Tk):

    help_window = None

    def __init__(self, handler, **options):
        Tk.__init__(self, **options )
        
        '''THE PROGRAM MUST BE CLASS WITH VARIABLES SUCH AS TAG_COLLECTION'''
        self.handler = handler

        self.title("Halo Bitmap Optimizer & Converter v2.0")
        self.geometry("745x405+0+0")
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", self.close_main_window)

        #this is used to make it so only 1 window update can be called at a time
        self.window_updating = False
        self.window_docking_updating = False
        
        self.window_update_interval = 0.33
        self.window_docking_interval = 0.1

        
        self.save_all_tags_as = True

        self.proceed_with_conversion = False #False = do nothing
                                             #True  = index and load tags, or
                                             #  convert tags if already loaded
        
        self.tags_indexed = False #False = program is still indexing tags
                                  #True  = tags indexed and ready to be loaded
        
        self.tags_loaded = False #False = program just loaded
                                 #True  = tags indexed and ready to convert
        
        #used to signal to the conversion routine to cancel conversion
        self.conversion_cancelled = False


        #Statistics variables
        self.bitmaps_found_2d = self.bitmaps_found_3d = self.cubemaps_found = 0
        self.total_bitmaps = 0
        self.elapsed_time = self.Estimated_Time_Remaining = 0.0
        self.total_pixel_data_to_process = 0
        self.remaining_bitmaps = self.remaining_pixel_data_to_process = 0
        
        #we'll use this to know how many tags we've
        #skipped while iterating the tag collection
        self.bad_bitmaps = 0
        
        self.scan_start_time = 0.0
        #set this to true when wanting to have the program
        #display exactly what's in the "current_tag" string
        self.display_new_text = False
        
        #used for setting the position of the child windows
        #so when you move the main it moves the others
        self.prev_pos_x = 0
        self.prev_pos_y = 0
        self.docking_state = True

        #Window variables that we'll use as an intermediary
        #between user input and giving to the program
        self.tk_tags_directory = StringVar(self)
        
        self.tk_prune_tiff = IntVar(self)
        self.tk_backup_edited_tags = IntVar(self)
        self.tk_read_only = IntVar(self)
        self.tk_write_debug_log = IntVar(self)
        
        self.tk_platform_to_save_as = IntVar(self)
        self.tk_swizzle_bitmap = IntVar(self)
        self.tk_number_of_times_to_halve_resolution = StringVar(self)
        
        self.tk_multipurpose_swap_setting = IntVar(self)

        self.tk_alpha_cutoff_bias = StringVar(self)
        self.tk_alpha_cutoff_bias.set("127")
        self.tk_p8_conversion_mode = IntVar(self)
        self.tk_channel_to_keep = IntVar(self)
        self.tk_swap_a8y8_alpha_and_intensity = IntVar(self)
        self.tk_preserve_ck_transparency = IntVar(self)
        
        self.tk_conversion_format_string = IntVar(self)
        self.tk_target_extract_format = StringVar(self)
        self.tk_mipmap_gen_setting = IntVar(self)
        self.tk_target_extract_format.set(" ")
        
        self.displayed_info_string = ('For information on what each '+
                          'setting does and how to use this program,\n'+
                          'open and look through the "Useful help" window.')

        #Make the menu bar
        self.menubar = Menu(self)
        self.menubar.add_command(label="Useful help",
                                 command=self.show_help)
        self.menubar.add_command(label="Toggle all tags to Xbox",
                                 command=self.set_save_all_tags_as)
        self.menubar.add_command(label="Un-dock windows",
                                 command=self.toggle_window_docking)
        self.menubar.add_command(label="Invert selection",
                                 command=self.invert_selection)
        self.config(menu=self.menubar)

        #--------------------------------------------------------------
        #Create the TAGS DIRECTORY field
        self.tags_field_name = Canvas(self, width=487,
                                      height=45, highlightthickness=0)
        self.tags_field_name.place(x=4, y=4, anchor=NW)
        self.tags_field_name.config(bd=2, relief=GROOVE)
        self.tags_field_text = self.tags_field_name.create_text(13, 3,
                                                                anchor="nw")
        self.tags_field_name.itemconfig(self.tags_field_text,
                                        text="tags folder")

        #Create the TAGS DIRECTORY box
        self.tags_directory_field = Entry(self,
                                          textvariable=self.tk_tags_directory)
        self.tags_directory_field.place(x=18, y=24, anchor=NW)
        self.tags_directory_field.insert(INSERT, self.handler.tagsdir)
        self.tags_directory_field.config(width=57, state=DISABLED)

        #Add the buttons
        self.btn_browse = Button(self.tags_field_name,
                                 text="Browse...", width=10,
                                 command=self.make_bitmap_converter_browse)
        self.btn_browse.place(x=362, y=16, anchor=NW)

        self.btn_start = Button(self.tags_field_name,
                                text="Load", width=7,
                                command=self.run_pressed)
        self.btn_start.place(x=432, y=16, anchor=NW)

        #--------------------------------------------------------------
        #Create the GLOBAL PARAMETERS field
        self.global_param_root = Canvas(self, width=135,
                                        height=95, highlightthickness=0)
        self.global_param_root.place(x=4, y=51, anchor=NW)
        self.global_param_name_text = self.global_param_root.\
                                      create_text(8, 5, anchor="nw")
        self.global_param_root.itemconfig(self.global_param_name_text,
                                          text="Global Parameters")
        self.global_param_root.config(bd=2, relief=GROOVE)

        #Create the GLOBAL PARAMETERS check buttons
        self.checkbox_prune_tiff = Checkbutton(
            self.global_param_root, 
            variable=self.tk_prune_tiff,
            onvalue=1, offvalue=0, text="Prune Tiff data",
            command=self.set_prune_tiff_variable)
        
        self.checkbox_backup_old_tags = Checkbutton(
            self.global_param_root,
            variable=self.tk_backup_edited_tags,
            onvalue=1, offvalue=0, text="Backup old tags",
            command=self.set_backup_old_tags_variable)
        
        self.checkbox_read_only = Checkbutton(
            self.global_param_root,
            variable=self.tk_read_only,
            onvalue=1, offvalue=0, text="Read only mode",
            command=self.set_read_only_variable)
        
        self.checkbox_write_debug_log = Checkbutton(
            self.global_param_root,
            variable=self.tk_write_debug_log,
            onvalue=1, offvalue=0, text="Write debug log",
            command=self.set_write_debug_log_variable)

        self.checkbox_backup_old_tags.select()
        self.checkbox_write_debug_log.select()
        
        self.checkbox_prune_tiff.place(x=4, y=23, anchor=NW)
        self.checkbox_backup_old_tags.place(x=4, y=41, anchor=NW)
        self.checkbox_read_only.place(x=4, y=59, anchor=NW)
        self.checkbox_write_debug_log.place(x=4, y=77, anchor=NW)
        #--------------------------------------------------------------
        
        #Create the GENERAL PARAMETERS field
        self.general_param_root = Canvas(self, width=236,
                                         height=95, highlightthickness=0)
        self.general_param_root.place(x=137, y=51, anchor=NW)
        self.general_param_name_text = self.general_param_root.\
                                            create_text(8, 5, anchor="nw")
        self.general_param_root.itemconfig(self.global_param_name_text,
                                           text="General Conversion Parameters")
        self.general_param_root.config(bd=2, relief=GROOVE)

        #Create the GENERAL PARAMETERS buttons
        self.radio_save_as_xbox = Radiobutton(
            self.general_param_root, text="Save as Xbox tag",
            variable=self.tk_platform_to_save_as, value=1,
            command=self.set_platform_to_save_as_variable)
        
        self.radio_save_as_pc = Radiobutton(
            self.general_param_root, text="Save as PC tag",
            variable=self.tk_platform_to_save_as, value=0,
            command=self.set_platform_to_save_as_variable)

        self.radio_save_as_swizzled = Radiobutton(
            self.general_param_root, text="Save as swizzled",
            variable=self.tk_swizzle_bitmap, value=1,
            command=self.set_swizzle_mode_variable)
        
        self.radio_save_as_unswizzled = Radiobutton(
            self.general_param_root, text="Save as un-swizzled",
            variable=self.tk_swizzle_bitmap, value=0,
            command=self.set_swizzle_mode_variable)
        
        self.spinbox_times_to_halve_resolution = Spinbox(
            self.general_param_root, from_=0, to=12, width=3, state="readonly",
            textvariable=self.tk_number_of_times_to_halve_resolution,
            command=self.set_number_of_times_to_halve_variable)
        
        self.times_to_halve_resolution_text = self.general_param_root.\
                                              create_text(45, 75, anchor="nw")
        
        self.radio_save_as_xbox.place(x=4, y=23, anchor=NW)
        self.radio_save_as_pc.place(x=112, y=23, anchor=NW)
        self.radio_save_as_swizzled.place(x=4, y=49, anchor=NW)
        self.radio_save_as_unswizzled.place(x=112, y=49, anchor=NW)
        self.spinbox_times_to_halve_resolution.place(x=8, y=72, anchor=NW)
        self.general_param_root.itemconfig(self.times_to_halve_resolution_text,
                                   text="Number of times to halve resolution")
        #--------------------------------------------------------------

        #Create the MULTIPURPOSE SWAP field
        self.multipurpose_swap_root = Canvas(self, width=116,
                                             height=95, highlightthickness=0)
        self.multipurpose_swap_root.place(x=375, y=51, anchor=NW)
        self.multipurpose_swap_name_text = self.multipurpose_swap_root.\
                                           create_text(8, 5, anchor="nw")
        self.multipurpose_swap_root.itemconfig(self.multipurpose_swap_name_text,
                                               text="Multipurpose Swap")
        self.multipurpose_swap_root.config(bd=2, relief=GROOVE)

        #Create the MULTIPURPOSE SWAP radio buttons
        self.radio_dont_swap_multipurpose = Radiobutton(
            self.multipurpose_swap_root, text="None",
            variable=self.tk_multipurpose_swap_setting, value=0,
            command=self.set_multipurpose_swap_variable)
        
        self.radio_swap_multipurpose_to_xbox = Radiobutton(
            self.multipurpose_swap_root, text="Swap PC to Xbox",
            variable=self.tk_multipurpose_swap_setting, value=1, 
            command=self.set_multipurpose_swap_variable)
        
        self.radio_swap_multipurpose_to_pc = Radiobutton(
            self.multipurpose_swap_root, text="Swap Xbox to PC",
            variable=self.tk_multipurpose_swap_setting, value=2,
            command=self.set_multipurpose_swap_variable)

        self.radio_dont_swap_multipurpose.select()
        self.radio_dont_swap_multipurpose.place(x=4, y=23, anchor=NW)
        self.radio_swap_multipurpose_to_xbox.place(x=4, y=48, anchor=NW)
        self.radio_swap_multipurpose_to_pc.place(x=4, y=73, anchor=NW)
        #--------------------------------------------------------------
        
        #Create the FORMAT SPECIFIC PARAMETERS field
        self.format_param_root = Canvas(self, width=238,
                                        height=133, highlightthickness=0)
        self.format_param_root.place(x=4, y=148, anchor=NW)
        self.format_param_name_text = self.format_param_root.\
                                      create_text(8, 5, anchor="nw")
        self.format_param_root.itemconfig(self.format_param_name_text,
                                          text="Format Specific Parameters")
        self.format_param_root.config(bd=2, relief=GROOVE)

        #Create the FORMAT SPECIFIC PARAMETERS buttons
        self.spinbox_alpha_cutoff_bias = Spinbox(
            self.format_param_root, from_=0, to=255, width=3,
            textvariable=self.tk_alpha_cutoff_bias, state="readonly",
            command=self.set_alpha_cutoff_bias_variable, repeatinterval=5)
        
        self.radio_auto_bias_mode = Radiobutton(
            self.format_param_root, text="Auto-bias",
            variable=self.tk_p8_conversion_mode, value=0,
            command=self.set_p8_conversion_mode_variable)
        
        self.radio_average_bias_mode = Radiobutton(
            self.format_param_root, text="Average-bias",
            variable=self.tk_p8_conversion_mode, value=1,
            command=self.set_p8_conversion_mode_variable)
        
        self.radio_keep_intensity_channel = Radiobutton(
            self.format_param_root, text="Intensity(RGB)",
            variable=self.tk_channel_to_keep, value=0,
            command=self.set_monochrome_channel_to_keep_variable)
        
        self.radio_keep_alpha_channel = Radiobutton(
            self.format_param_root, text="Alpha",
            variable=self.tk_channel_to_keep, value=1,
            command=self.set_monochrome_channel_to_keep_variable)
        
        self.checkbox_swap_a8y8_channels = Checkbutton(
            self.format_param_root, text="Swap A8Y8 channels",
            variable=self.tk_swap_a8y8_alpha_and_intensity, onvalue=1,
            command=self.set_swap_alpha_and_intensity_variable, offvalue=0)
        
        self.checkbox_preserve_ck_transparency = Checkbutton(
            self.format_param_root, text="C-Key Transparent",
            variable=self.tk_preserve_ck_transparency, onvalue=1, offvalue=0,
            command=self.set_preserve_ck_transparency_variable)

        self.spinbox_alpha_cutoff_bias.place(x=28, y=20, anchor=NW)
        self.radio_auto_bias_mode.place(x=18, y=53, anchor=NW)
        self.radio_average_bias_mode.place(x=126, y=53, anchor=NW)
        self.radio_keep_intensity_channel.place(x=18, y=90, anchor=NW)
        self.radio_keep_alpha_channel.place(x=126, y=90, anchor=NW)
        self.checkbox_swap_a8y8_channels.place(x=2, y=113, anchor=NW)
        self.checkbox_preserve_ck_transparency.place(x=123, y=113, anchor=NW)
        
        self.alpha_cutoff_bias_text = self.format_param_root.\
                                      create_text(69, 23, anchor="nw")
        self.p8_bump_conversion_mode_text = self.format_param_root.\
                                            create_text(8, 40, anchor="nw")
        self.monochrome_channel_to_keep_text = self.format_param_root.\
                                               create_text(6, 75, anchor="nw")
        
        self.format_param_root.itemconfig(self.alpha_cutoff_bias_text,
                                          text="Alpha cutoff bias")
        self.format_param_root.itemconfig(self.p8_bump_conversion_mode_text,
                                          text="P-8 Bump conversion mode")
        self.format_param_root.itemconfig(self.monochrome_channel_to_keep_text,
                                          text="Monochrome channel to keep")
        #--------------------------------------------------------------
        
        #Create the FORMAT TO CONVERT TO field
        self.format_to_convert_to_root = Canvas(self, width=247, height=133,
                                                highlightthickness=0)
        self.format_to_convert_to_root.place(x=244, y=148, anchor=NW)
        self.format_to_convert_to_name_text = self.format_to_convert_to_root.\
                                              create_text(8, 5, anchor="nw")
        self.format_to_convert_to_root.itemconfig(
            self.format_to_convert_to_name_text, text="Format to convert to")
        self.format_to_convert_to_root.config(bd=2, relief=GROOVE)

        #Create the FORMAT TO CONVERT TO radio buttons
        self.radio_dont_change_format = Radiobutton(
                                 self.format_to_convert_to_root,
                                 text="Unchanged", value=FORMAT_NONE,
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_dxt1 = Radiobutton(self.format_to_convert_to_root,
                                 text="DXT1", value=FORMAT_DXT1, 
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_dxt3 = Radiobutton(self.format_to_convert_to_root,
                                 text="DXT3",value=FORMAT_DXT3, 
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_dxt5 = Radiobutton(self.format_to_convert_to_root,
                                 text="DXT5", value=FORMAT_DXT5,
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_r5g6b5 = Radiobutton(self.format_to_convert_to_root,
                                 text="R5G6B5",value=FORMAT_R5G6B5, 
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_a1r5g5b5 = Radiobutton(
                                 self.format_to_convert_to_root,
                                 text="A1R5G5B5*", value=FORMAT_A1R5G5B5, 
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_a4r4g4b4 = Radiobutton(
                                 self.format_to_convert_to_root,
                                 value=FORMAT_A4R4G4B4, text="A4R4G4B4",
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_p8_bump = Radiobutton(self.format_to_convert_to_root,
                                 text="P8*/32Bit", value=FORMAT_P8,
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_a8y8 = Radiobutton(self.format_to_convert_to_root,
                                 text="A8Y8*", value=FORMAT_A8Y8,
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_ay8 = Radiobutton(self.format_to_convert_to_root,
                                 text="AY8*", value=FORMAT_AY8, 
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)
        self.radio_save_as_a8_or_y8 = Radiobutton(
                                 self.format_to_convert_to_root,
                                 text="A8/Y8*",value=FORMAT_A8,
                                 variable=self.tk_conversion_format_string,
                                 command=self.set_format_to_save_as_variable)

        self.checkbox_mipmap_gen = Checkbutton(self.format_to_convert_to_root,
                                 text="Mipmap Gen", onvalue=1, offvalue=0,
                                 variable=self.tk_mipmap_gen_setting,
                                 command=self.set_mipmap_gen_setting_variable)
        self.option_menu_extract_to = OptionMenu(self.format_to_convert_to_root,
                                 self.tk_target_extract_format, ' ', 'DDS',
                                'TGA', command=self.set_target_extract_variable)

        self.option_menu_extract_to.config(width=3)

        self.radio_dont_change_format.place(x=5, y=24, anchor=NW)
        self.radio_save_as_dxt1.place(x=84, y=24, anchor=NW)
        self.radio_save_as_dxt3.place(x=138, y=24, anchor=NW)
        self.radio_save_as_dxt5.place(x=188, y=24, anchor=NW)
        self.radio_save_as_r5g6b5.place(x=5, y=52, anchor=NW)
        self.radio_save_as_a1r5g5b5.place(x=68, y=52, anchor=NW)
        self.radio_save_as_a4r4g4b4.place(x=150, y=52, anchor=NW)
        self.radio_save_as_p8_bump.place(x=5, y=78, anchor=NW)
        self.radio_save_as_a8y8.place(x=78, y=78, anchor=NW)
        self.radio_save_as_ay8.place(x=132, y=78, anchor=NW)
        self.radio_save_as_a8_or_y8.place(x=180, y=78, anchor=NW)
        
        self.checkbox_mipmap_gen.place(x=10, y=106, anchor=NW)
        self.option_menu_extract_to.place(x=160, y=103, anchor=NW)
        
        self.extract_to_text = self.format_to_convert_to_root.create_text(105,
                                                              110, anchor="nw")
        self.format_to_convert_to_root.itemconfig(self.extract_to_text,
                                                  text="Extract to:")  

        
        #--------------------------------------------------------------

        #Create SCAN STATUS field
        self.scan_status_root = Canvas(self, width=495, height=65,
                                       highlightthickness=0)
        self.scan_status_root.place(x=1, y=286, anchor=NW)
        self.scan_status_text_1 = self.scan_status_root.create_text(5, 5,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_1,
                                         text="2D bitmaps found:-")    
        self.scan_status_text_2 = self.scan_status_root.create_text(5, 25,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_2,
                                         text="3D bitmaps found:-")    
        self.scan_status_text_3 = self.scan_status_root.create_text(5, 45,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_3,
                                         text="Cubemaps found: -")
        
        self.scan_status_text_4 = self.scan_status_root.create_text(150, 45,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_4,
                                         text="Elapsed time:--")
        self.scan_status_text_5 = self.scan_status_root.create_text(150, 25,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_5,
                                         text="Total bitmaps:-")
        self.scan_status_text_6 = self.scan_status_root.create_text(150, 5,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_6,
                                         text="Total data:-----")
        
        self.scan_status_text_7 = self.scan_status_root.create_text(310, 25,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_7,
                                         text="Remaining bitmaps:-")    
        self.scan_status_text_8 = self.scan_status_root.create_text(310, 5,
                                                                    anchor="nw")
        self.scan_status_root.itemconfig(self.scan_status_text_8,
                                         text="Remaining data:-----")

        self.text_scan_status_2d_bitmaps_found = Text(self.scan_status_root,
                                                      height=1, bg='#ece9d8',
                                                      state=DISABLED, width=6)
        self.text_scan_status_2d_bitmaps_found.place(x=100, y=5, anchor=NW)
        self.text_scan_status_3d_bitmaps_found = Text(self.scan_status_root,
                                                      height=1, bg='#ece9d8',
                                                      state=DISABLED, width=6)
        self.text_scan_status_3d_bitmaps_found.place(x=100, y=25, anchor=NW)
        self.text_scan_status_cubemaps_found = Text(self.scan_status_root,
                                                    height=1, bg='#ece9d8',
                                                    state=DISABLED, width=6)
        self.text_scan_status_cubemaps_found.place(x=100, y=45, anchor=NW)

        self.text_scan_status_elapsed_time = Text(self.scan_status_root,
                                                  height=1, bg='#ece9d8',
                                                  state=DISABLED, width=11)
        self.text_scan_status_elapsed_time.place(x=225, y=45, anchor=NW)
        self.text_scan_status_total_bitmaps = Text(self.scan_status_root,
                                                   height=1, bg='#ece9d8',
                                                   state=DISABLED, width=11)
        self.text_scan_status_total_bitmaps.place(x=225, y=25, anchor=NW)
        self.text_scan_status_total_data = Text(self.scan_status_root,
                                                height=1, bg='#ece9d8',
                                                state=DISABLED, width=11)
        self.text_scan_status_total_data.place(x=225, y=5, anchor=NW)

        self.text_scan_status_remaining_bitmaps = Text(self.scan_status_root,
                                                       height=1, bg='#ece9d8',
                                                       state=DISABLED, width=11)
        self.text_scan_status_remaining_bitmaps.place(x=410, y=25, anchor=NW)
        self.text_scan_status_remaining_data = Text(self.scan_status_root,
                                                    height=1, bg='#ece9d8',
                                                    state=DISABLED, width=11)
        self.text_scan_status_remaining_data.place(x=410, y=5, anchor=NW)
        #--------------------------------------------------------------

        #Create DISPLAYED INFO field
        self.current_tag_root = Canvas(self, width=490, height=45)
        self.current_tag_root.place(x=0, y=354, anchor=NW)

        self.displayed_info_text_box = Text(self.current_tag_root,
                                            height=3, bg='#ece9d8',
                                            state=NORMAL, width=70)
        self.displayed_info_text_box.insert(INSERT, self.displayed_info_string)
        self.displayed_info_text_box.config(state=DISABLED)
        self.displayed_info_text_box.place(x=0, y=0, anchor=NW)

        
        self.disable_settings_window_buttons()
        self.tag_list_window = BitmapConverterListWindow(handler, self)
        
        self.tag_data_canvas = BitmapConverterDataWindow(handler, self)
        self.tag_data_canvas.place(x=495, y=2, anchor=NW)

        self.child_windows = (self.tag_list_window,)

        #Create and start the window update thread
        self.window_docking_thread = threading.Thread(
            target=self.window_docking_daemon)
        self.window_docking_thread.daemon = True
        self.window_docking_thread.start()

        #Create and start the window update thread
        self.window_update_thread = threading.Thread(
            target=self._main_window_update)
        self.window_update_thread.daemon = True
        self.window_update_thread.start()


    def window_docking_daemon(self):
        '''AFTER THE WINDOW IS CREATED THIS FUNCTION WILL
        LOOP CONTINUOUSLY DOCK MOVEMENT OF CHILD WINDOWS'''
        while not self.handler.close_program:
            #we don't want it to run too often or it'll be laggy
            sleep(self.window_docking_interval)
            
            #calls a function to lock the position of the
            #provided child windows to the provided parent window
            if not(self.window_docking_updating):
                self.after(0, (lambda:(self.dock_window_movement(
                    self.child_windows))))

    def dock_window_movement(self, child_windows):
        self.window_docking_updating = True
        
        #the .geometry() returns the dimensions as a string that looks like
        #"widthxheight+posx+posy". an example would be "200x200+50+50".
        #Because of that we need to split them apart at the x and +
        root_dim = self.geometry().split('+')
        
        #we want to move the child windows with the main,
        #but keep their relative position to the main
        if ((int(root_dim[1]) != self.prev_pos_x) or
            (int(root_dim[2]) != self.prev_pos_y)):
            
            #get the amount that the main window has been moved
            root_x_shift = (int(root_dim[1]) - self.prev_pos_x)
            root_y_shift = (int(root_dim[2]) - self.prev_pos_y)

            #set the new parent window's location
            self.prev_pos_x = int(root_dim[1])
            self.prev_pos_y = int(root_dim[2])

            if self.docking_state:
                
                #move each of the child windows with the parent
                for child_window in child_windows:
                    child_dim = child_window.geometry().split('+')
                    
                    child_window.prev_pos_x = int(child_dim[1])
                    child_window.prev_pos_y = int(child_dim[2])
                    
                    child_dim = ("%s+%s+%s" % (child_dim[0],
                                 str(root_x_shift+child_window.prev_pos_x),
                                 str(root_y_shift+child_window.prev_pos_y)))
                    
                    child_window.geometry(child_dim)

        self.window_docking_updating = False

    def _main_window_update(self):
        '''AFTER THE WINDOW IS CREATED THIS FUNCTION WILL
        LOOP CONTINUOUSLY AND UPDATE ALL INFO IT'''
        while not self.handler.close_program:
            #we don't want it to run too often or it'll be laggy
            sleep(self.window_update_interval)
                
            #if the program is being told to display new, literal text
            if self.display_new_text:
                if not(self.window_updating):
                    self.after(0, (lambda:\
                       (self.update_bitmap_converter_main_window\
                        (self.handler.current_tag))))
                    self.display_new_text = False
            elif self.proceed_with_conversion:
                if self.tags_indexed:
                    if self.tags_loaded:
                        if (self.handler.default_conversion_flags\
                            ["bitm"][READ_ONLY]):
                            update_string = ("Compiling detailed "+
                                             "list of all tags: ")
                        else:
                            update_string = ("Processing tag: " +
                                             self.handler.current_tag)
                    else:
                        if self.tags_indexed:
                            update_string = ("tags indexed... Loading: " +
                                             self.handler.current_tag)
                            self.total_bitmaps = self.handler.tags_indexed
                            self.remaining_bitmaps = self.handler.tags_loaded
                        else:
                            update_string = ""
                else:
                    update_string = ("Searching for bitmap tags... "+
                                     "Currently looking at: " +
                                     self.handler.current_tag)
                    self.total_bitmaps = self.handler.tags_indexed

                if not(self.window_updating):
                    self.after(0, (lambda:
                    (self.update_bitmap_converter_main_window(update_string))))


            
    #This function is to make the window to browse for the tags folder
    def make_bitmap_converter_browse(self):
        if not(self.proceed_with_conversion):
            tags_dir_str = tkinter.filedialog.askdirectory(
                initialdir=self.handler.tagsdir,
                title='Select a folder that contains bitmap tags')
            tags_dir_str = tags_dir_str.replace('/', '\\')
            
            if(len(tags_dir_str)):
                if not tags_dir_str.endswith('\\'):
                    tags_dir_str += "\\"
                self.tags_directory_field.config(state=NORMAL)
                self.tags_directory_field.delete(0,END)
                self.tags_directory_field.insert(0,tags_dir_str)
                self.handler.tagsdir = join(self.tags_directory_field.get(), '')
                self.handler.datadir = join(dirname(dirname(
                    self.handler.tagsdir)), 'data', '')
                self.tags_directory_field.config(state=DISABLED)


    def show_help(self):
        try:
            if self.help_window is None:
                self.help_window = BitmapConverterHelpWindow(self)
        except Exception:
            pass

    def close_help(self):
        try:
            self.help_window.destroy()
        except Exception:
            pass
            
    def close_main_window(self):
        self.proceed_with_conversion = False
        self.handler.close_program = True
        self.destroy()


    #this function applies the xbox and swizzle conversion flags to all bitmaps
    def set_save_all_tags_as(self):
        if self.tags_loaded:
            bitm_coll = self.handler.tags["bitm"]
            list_window = self.tag_list_window
            save_as = self.save_all_tags_as
            
            for index in range(len(list_window.displayed_tag_index_mapping)):
                filepath = list_window.displayed_tag_index_mapping[index]
                bitm_coll[filepath].tag_conversion_settings[PLATFORM] = save_as
                bitm_coll[filepath].tag_conversion_settings[SWIZZLED] = save_as
                list_window.set_listbox_entry_color(index, filepath)
              
            if save_as:
                self.menubar.entryconfig(2,label="Toggle all tags to PC")
            else:
                self.menubar.entryconfig(2,label="Toggle all tags to Xbox")

            self.save_all_tags_as = not(save_as)

            if len(list_window.selected_tags):
                if bitm_coll[list_window.selected_tags[0]].\
                   tag_conversion_settings[PLATFORM]:
                    self.radio_save_as_xbox.select()
                else:
                    self.radio_save_as_pc.select()
                    
                if bitm_coll[list_window.selected_tags[0]].\
                   tag_conversion_settings[SWIZZLED]:
                    self.radio_save_as_swizzled.select()
                else:
                    self.radio_save_as_unswizzled.select()

        
    def toggle_window_docking(self):
        if self.docking_state:
            self.docking_state = False
            self.menubar.entryconfig(3, label="Dock Windows")
        else:
            self.docking_state = True
            self.menubar.entryconfig(3, label="Un-dock Windows")


    def invert_selection(self):
        self.tag_list_window.invert_selection()
            

    #These function disables all buttons when starting a scan
    def run_pressed(self):
        if self.proceed_with_conversion:
            if self.tags_loaded and not(
                self.handler.default_conversion_flags["bitm"][READ_ONLY]):
                self.cancel_conversion()
        elif not(self.conversion_cancelled):
            self.proceed_with_conversion = True
            
            self.close_help()
            self.disable_global_settings()
            self.disable_settings_window_buttons()
            
            if self.tags_loaded:
                if self.handler.default_conversion_flags["bitm"][READ_ONLY]:
                    self.btn_start.config(text="Logging")
                else:
                    self.btn_start.config(text="Cancel")
            else:
                self.btn_start.config(text="Indexing")
                self.btn_browse.config(state=DISABLED)
                self.btn_start.config(state=DISABLED)


    #These function enables all buttons when a scan finishes
    def finish_scanning(self):
        self.proceed_with_conversion = False
        
        self.display_new_text = True
        self.btn_start.config(state=NORMAL)
        self.btn_start.config(text="Run")
        self.enable_global_settings()
        self.enable_settings_window_buttons()

    #These function enables all buttons when a conversion finishes
    def finish_conversion(self):
        self.handler.reset_tags()
        self.tags_indexed = False
        self.tags_loaded = False
        self.proceed_with_conversion = False
        
        self.tag_list_window.initialize_tag_sort_mappings()
        self.tag_list_window.reset_lists()
        
        self.display_new_text = True
        self.btn_start.config(text="Load")
        self.btn_start.config(state=NORMAL)
        self.btn_browse.config(state=NORMAL)
        self.enable_global_settings()

    #These function enables all buttons when a conversion is cancelled
    def cancel_conversion(self):
        self.handler.current_tag = "Cancelling conversion... Please wait..."
        self.btn_start.config(text="Wait...")
        self.display_new_text = True
        self.proceed_with_conversion = False
        
        self.conversion_cancelled = True

    def disable_global_settings(self):
        for widget in(self.checkbox_prune_tiff,
                      self.checkbox_backup_old_tags,
                      self.checkbox_read_only, self.checkbox_write_debug_log):
            widget.config(state=DISABLED)
            
    def enable_global_settings(self):
        for widget in(self.checkbox_prune_tiff,
                      self.checkbox_backup_old_tags,
                      self.checkbox_read_only, self.checkbox_write_debug_log):
            widget.config(state=NORMAL)

    def disable_settings_window_buttons(self):
        for widget in(self.radio_save_as_xbox, self.radio_save_as_pc,
                self.radio_save_as_swizzled, self.radio_save_as_unswizzled,
                self.spinbox_times_to_halve_resolution,
                self.radio_dont_swap_multipurpose,
                self.radio_swap_multipurpose_to_xbox,
                self.radio_swap_multipurpose_to_pc,
                self.spinbox_alpha_cutoff_bias,
                self.radio_auto_bias_mode, self.radio_average_bias_mode,
                self.radio_keep_intensity_channel,
                self.radio_keep_alpha_channel, self.checkbox_swap_a8y8_channels,
                self.checkbox_preserve_ck_transparency,
                self.radio_dont_change_format, self.radio_save_as_dxt1,
                self.radio_save_as_dxt3, self.radio_save_as_dxt5,
                self.radio_save_as_r5g6b5, self.radio_save_as_a1r5g5b5,
                self.radio_save_as_a4r4g4b4, self.radio_save_as_p8_bump,
                self.radio_save_as_a8y8, self.radio_save_as_ay8,
                self.radio_save_as_a8_or_y8,
                self.option_menu_extract_to, self.checkbox_mipmap_gen):
            widget.config(state=DISABLED)


    def enable_settings_window_buttons(self):
        widget_list = (self.radio_save_as_xbox, self.radio_save_as_pc,
            self.radio_save_as_swizzled, self.radio_save_as_unswizzled,
            self.spinbox_times_to_halve_resolution,
            self.radio_dont_swap_multipurpose,
            self.radio_swap_multipurpose_to_xbox,
            self.radio_swap_multipurpose_to_pc, self.spinbox_alpha_cutoff_bias,
            self.radio_auto_bias_mode, self.radio_average_bias_mode,
            self.radio_keep_intensity_channel, self.radio_keep_alpha_channel,
            self.checkbox_swap_a8y8_channels, self.radio_dont_change_format,
            self.checkbox_preserve_ck_transparency,
            self.radio_save_as_dxt1, self.radio_save_as_dxt3,
            self.radio_save_as_dxt5, self.radio_save_as_r5g6b5,
            self.radio_save_as_a1r5g5b5,
            self.radio_save_as_a4r4g4b4, self.radio_save_as_p8_bump,
            self.radio_save_as_a8y8, self.radio_save_as_ay8,
            self.radio_save_as_a8_or_y8,
            self.option_menu_extract_to, self.checkbox_mipmap_gen)

        for widget in widget_list:
            widget.config(state=NORMAL)
        
        self.spinbox_times_to_halve_resolution.config(state="readonly")
        self.spinbox_alpha_cutoff_bias.config(state="readonly")


    #this function selects the proper buttons based
    #on what tag has been selected if multiple tags
    #have been selected this function is skipped
    def select_proper_settings_window_settings(self):
        widget_list = []

        tag = self.handler.tags["bitm"][self.tag_list_window.selected_tags[0]]
        conversion_flags = tag.tag_conversion_settings
        
        if tag.bitmap_count() != 0 and tag.bitmap_format() == 14:
            conversion_flags[CK_TRANS] = True
            self.tk_preserve_ck_transparency.set(1)

        if conversion_flags[PLATFORM]:
            self.radio_save_as_xbox.select()
        else: self.radio_save_as_pc.select()
            
        if conversion_flags[SWIZZLED]:
            self.radio_save_as_swizzled.select()
        else: self.radio_save_as_unswizzled.select()
            
        self.tk_number_of_times_to_halve_resolution.set(
            conversion_flags[DOWNRES])
        
        if conversion_flags[MULTI_SWAP] == 1:
            self.radio_swap_multipurpose_to_xbox.select()
        elif conversion_flags[MULTI_SWAP] == 2:
            self.radio_swap_multipurpose_to_pc.select()
        else: self.radio_dont_swap_multipurpose.select()
            
        self.tk_alpha_cutoff_bias.set(conversion_flags[CUTOFF_BIAS])
        
        if conversion_flags[P8_MODE]:
            self.radio_average_bias_mode.select()
        else: self.radio_auto_bias_mode.select()
            
        if conversion_flags[MONO_KEEP]:
            self.radio_keep_alpha_channel.select()
        else: self.radio_keep_intensity_channel.select()
            
        if conversion_flags[MONO_SWAP]:
            self.tk_swap_a8y8_alpha_and_intensity.set(1)
        else: self.tk_swap_a8y8_alpha_and_intensity.set(0)
            
        if conversion_flags[CK_TRANS]:
            self.tk_preserve_ck_transparency.set(1)
        else: self.tk_preserve_ck_transparency.set(0)
            
        if conversion_flags[NEW_FORMAT] == FORMAT_DXT1:
            self.radio_save_as_dxt1.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_DXT3:
            self.radio_save_as_dxt3.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_DXT5:
            self.radio_save_as_dxt5.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_R5G6B5:
            self.radio_save_as_r5g6b5.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_A1R5G5B5:
            self.radio_save_as_a1r5g5b5.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_A4R4G4B4:
            self.radio_save_as_a4r4g4b4.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_P8:
            self.radio_save_as_p8_bump.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_A8Y8:
            self.radio_save_as_a8y8.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_AY8:
            self.radio_save_as_ay8.select()
        elif conversion_flags[NEW_FORMAT] == FORMAT_A8:
            self.radio_save_as_a8_or_y8.select()
        else:
            self.radio_dont_change_format.select()

        self.tk_target_extract_format.set(conversion_flags[EXTRACT_TO])
        
        self.tk_mipmap_gen_setting.set(conversion_flags[MIP_GEN])
            

    #This function updates all the information in the main window's widgets
    def update_bitmap_converter_main_window(self, newtext=None):
        self.window_updating = True
            
        #Update the message text if supplied with a non-blank string
        if (newtext is not None and newtext!=(
            self.displayed_info_text_box.get('0.0',END+"-1c"))):
            
            self.displayed_info_text_box.config(state=NORMAL)
            self.displayed_info_text_box.delete('0.0', END)
            self.displayed_info_text_box.insert(INSERT, newtext)
            self.displayed_info_text_box.config(state=DISABLED)

        
        self.elapsed_time = int(time() - self.scan_start_time)
        
        elapsed_time_string = (str(self.elapsed_time//3600)+"h:"+
                               str((self.elapsed_time%3600)//60)+"m:"+
                               str(self.elapsed_time%60)+"s")
        
        total_pixel_data_string = (str(
            self.total_pixel_data_to_process//1048576)[:9]+"MB")
        remaining_pixel_data_string = tmpstr = (str(
            self.remaining_pixel_data_to_process//1048576)[:9]+"MB")

        widget_values = (self.bitmaps_found_2d, self.bitmaps_found_3d,
                         self.cubemaps_found, self.total_bitmaps,
                         self.remaining_bitmaps, elapsed_time_string,
                         total_pixel_data_string, remaining_pixel_data_string)
        widgets = (self.text_scan_status_2d_bitmaps_found,
                   self.text_scan_status_3d_bitmaps_found,
                   self.text_scan_status_cubemaps_found,
                   self.text_scan_status_total_bitmaps,
                   self.text_scan_status_remaining_bitmaps,
                   self.text_scan_status_elapsed_time,
                   self.text_scan_status_total_data,
                   self.text_scan_status_remaining_data)

        for i in range(len(widget_values)):
            if (widgets[i].get('0.0',END+"-1c") != str(widget_values[i])):
                widgets[i].config(state=NORMAL)
                widgets[i].delete('0.0', END)
                widgets[i].insert(INSERT, str(widget_values[i]))
                widgets[i].config(state=DISABLED)

        self.window_updating = False



    """
    THESE NEXT FUNCTIONS ARE FOR CHANGING CONVERSION
    VARIABLES BASED ON WHICH SETTING IS CLICKED
    """


    def set_prune_tiff_variable(self):
        self.handler.default_conversion_flags["bitm"][
            PRUNE_TIFF] = self.tk_prune_tiff.get()
        self._set_selection_color(range(len(
            self.tag_list_window.displayed_tag_index_mapping)))
        
    def set_backup_old_tags_variable(self):
        self.handler.default_conversion_flags["bitm"][
            RENAME_OLD] = self.tk_backup_edited_tags.get()
        
    def set_read_only_variable(self):
        self.handler.default_conversion_flags["bitm"][
            READ_ONLY] = self.tk_read_only.get()
        self._set_selection_color(range(
            len(self.tag_list_window.displayed_tag_index_mapping)))
        
    def set_write_debug_log_variable(self):
        self.handler.default_conversion_flags["bitm"][
            WRITE_LOG] = self.tk_write_debug_log.get()
        
    def set_platform_to_save_as_variable(self):
        self._set_selection_flag(PLATFORM, self.tk_platform_to_save_as, bool)
        self._set_selection_color()
        
    def set_swizzle_mode_variable(self):
        self._set_selection_flag(SWIZZLED, self.tk_swizzle_bitmap, bool)
        self._set_selection_color()
        
    def set_number_of_times_to_halve_variable(self):
        self._set_selection_flag(DOWNRES,
                                 self.tk_number_of_times_to_halve_resolution)
        self._set_selection_color()
        
    def set_multipurpose_swap_variable(self):
        self._set_selection_flag(MULTI_SWAP, self.tk_multipurpose_swap_setting)
        self._set_selection_color()
        
    def set_alpha_cutoff_bias_variable(self):
        self._set_selection_flag(CUTOFF_BIAS, self.tk_alpha_cutoff_bias)
        
    def set_p8_conversion_mode_variable(self):
        self._set_selection_flag(P8_MODE, self.tk_p8_conversion_mode, bool)
                
    def set_monochrome_channel_to_keep_variable(self):
        self._set_selection_flag(MONO_KEEP, self.tk_channel_to_keep, bool)
        
    def set_swap_alpha_and_intensity_variable(self):
        self._set_selection_flag(MONO_SWAP,
                                 self.tk_swap_a8y8_alpha_and_intensity, bool)
        self._set_selection_color()
        
    def set_preserve_ck_transparency_variable(self):
        self._set_selection_flag(CK_TRANS,
                                 self.tk_preserve_ck_transparency, bool)
        
    def set_format_to_save_as_variable(self):
        self._set_selection_flag(NEW_FORMAT, self.tk_conversion_format_string)
        self._set_selection_color()
        
    def set_mipmap_gen_setting_variable(self):
        self._set_selection_flag(MIP_GEN, self.tk_mipmap_gen_setting)
        self._set_selection_color()
        
    def set_target_extract_variable(self, *args):
        self._set_selection_flag(EXTRACT_TO, self.tk_target_extract_format)
        self._set_selection_color()

    def _set_selection_flag(self, flag_name, window_var, b_type=None):
        for filepath in self.tag_list_window.selected_tags:
            flags = self.handler.tags["bitm"][filepath].tag_conversion_settings
            if b_type:
                flags[flag_name] = b_type(window_var.get())
            else:
                flags[flag_name] = window_var.get()

    def _set_selection_color(self, indexes=None):
        if indexes is None:
            indexes = self.tag_list_window.tag_list_listbox.curselection()
        for i in indexes:
            filepath = self.tag_list_window.displayed_tag_index_mapping[int(i)]
            self.tag_list_window.set_listbox_entry_color(i, filepath)



class BitmapConverterDataWindow(Canvas):

    def __init__(self, handler, parent, **options):
        options.update({"width":250, "height":155, "highlightthickness":0})
        Canvas.__init__(self, parent, **options )
        
        self.handler = handler
        self.parent  = parent

        self.tk_selected_bitmap_index = StringVar(self)
        self.tk_selected_bitmap_index.set("")

        #--------------------------------------------------------------
        
        #Create BITMAP INDEX SELECTION field

        self.tag_data_sel_bitmap_root = Canvas(self, width=236,
                                               height=142, highlightthickness=0)
        self.tag_data_sel_bitmap_root.config(bd=2, relief=GROOVE)
        self.tag_data_sel_bitmap_root.place(x=5, y=2, anchor=NW)
        self.tag_data_sel_bitmap_data_text = self.tag_data_sel_bitmap_root.\
                                             create_text(60, 28, anchor="nw")
        self.tag_data_sel_bitmap_root.itemconfig(
            self.tag_data_sel_bitmap_data_text,
            text="Selected Bitmap Information")

        self.tag_data_sel_bitmap_text = self.tag_data_sel_bitmap_root.\
                                        create_text(8, 7, anchor="nw")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_sel_bitmap_text,
                                     text="Current bitmap:"+" "*14 + "out of:")
        
        self.selected_bitmap_index = Spinbox(self.tag_data_sel_bitmap_root,
                                     from_=0, to=0, width=2, state="readonly",
                                     textvariable=self.tk_selected_bitmap_index,
                                     command=self.display_selected_bitmap)
        self.tag_data_bitmap_count_box = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=2)
        self.selected_bitmap_index.place(x=90, y=7, anchor=NW)
        self.tag_data_bitmap_count_box.place(x=165, y=7, anchor=NW)

        #--------------------------------------------------------------
        #Create SELECTED BITMAP DATA field

        self.tag_data_height_text   = self.tag_data_sel_bitmap_root.create_text(
            10, 48, anchor="nw")
        self.tag_data_width_text    = self.tag_data_sel_bitmap_root.create_text(
            10, 71, anchor="nw")
        self.tag_data_depth_text    = self.tag_data_sel_bitmap_root.create_text(
            10, 94, anchor="nw")
        self.tag_data_mipmaps_text  = self.tag_data_sel_bitmap_root.create_text(
            10, 119, anchor="nw")
        self.tag_data_type_text     = self.tag_data_sel_bitmap_root.create_text(
            125, 48, anchor="nw")
        self.tag_data_format_text   = self.tag_data_sel_bitmap_root.create_text(
            115, 71, anchor="nw")
        self.tag_data_swizzled_text = self.tag_data_sel_bitmap_root.create_text(
            110, 94, anchor="nw")
        self.tag_data_platform_text = self.tag_data_sel_bitmap_root.create_text(
            110, 119, anchor="nw")
        
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_height_text,
                                                 text="Height:")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_width_text,
                                                 text="Width:")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_depth_text,
                                                 text="Depth:")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_type_text,
                                                 text="Type:")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_format_text,
                                                 text="Format:")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_swizzled_text,
                                                 text="swizzled:")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_mipmaps_text,
                                                 text="Mipmaps:")
        self.tag_data_sel_bitmap_root.itemconfig(self.tag_data_platform_text,
                                                 text="Platform:")

        self.tag_data_height_box   = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=5)
        self.tag_data_width_box    = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=5)
        self.tag_data_depth_box    = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=5)
        self.tag_data_mipmaps_box  = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=5)
        self.tag_data_type_box     = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=8)
        self.tag_data_format_box   = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=8)
        self.tag_data_swizzled_box = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=8)
        self.tag_data_platform_box = Text(self.tag_data_sel_bitmap_root,
                              height=1, bg='#ece9d8', state=DISABLED, width=8)
        
        self.tag_data_height_box.place(x=58, y=46, anchor=NW)
        self.tag_data_width_box.place(x=58, y=69, anchor=NW)
        self.tag_data_depth_box.place(x=58, y=92, anchor=NW)
        self.tag_data_mipmaps_box.place(x=58, y=115, anchor=NW)
        self.tag_data_type_box.place(x=160, y=46, anchor=NW)
        self.tag_data_format_box.place(x=160, y=69, anchor=NW)
        self.tag_data_swizzled_box.place(x=160, y=92, anchor=NW)
        self.tag_data_platform_box.place(x=160, y=115, anchor=NW)
        
                    
    #when called this function will update the info in the
    #tag data box to show the single tag that is selected
    def display_selected_bitmap(self):
        handler   = self.handler
        selection = self.parent.tag_list_window.tag_list_listbox.curselection()
        #only run if just 1 bitmap is selected
        if len(selection) == 1:
            filepath = self.parent.tag_list_window.\
                       displayed_tag_index_mapping[int(selection[0])]
            tag = handler.tags["bitm"][filepath]
            
            #only run if the tag contains bitmaps
            bitmap_count = tag.bitmap_count()
            if bitmap_count:
                for widget in(self.tag_data_height_box, self.tag_data_width_box,
                        self.tag_data_depth_box, self.tag_data_mipmaps_box,
                        self.tag_data_type_box, self.tag_data_format_box,
                        self.tag_data_swizzled_box, self.tag_data_platform_box,
                        self.tag_data_bitmap_count_box):
                    widget.config(state=NORMAL)

                self.selected_bitmap_index.config(to=(bitmap_count-1))
                bitmap_block_index = int(self.selected_bitmap_index.get())
                b_type   = tag.bitmap_type(bitmap_block_index)
                b_format = tag.bitmap_format(bitmap_block_index)

                for widget in (self.tag_data_bitmap_count_box,
                           self.tag_data_height_box, self.tag_data_width_box,
                           self.tag_data_depth_box, self.tag_data_mipmaps_box,
                           self.tag_data_type_box, self.tag_data_swizzled_box,
                           self.tag_data_format_box,self.tag_data_platform_box):
                    widget.delete('1.0', END)
                
                self.tag_data_bitmap_count_box.insert(INSERT,
                            str(bitmap_count-1))
                self.tag_data_height_box.insert(INSERT,
                            str(tag.bitmap_height(bitmap_block_index)))
                self.tag_data_width_box.insert(INSERT,
                            str(tag.bitmap_width(bitmap_block_index)))
                self.tag_data_depth_box.insert(INSERT,
                            str(tag.bitmap_depth(bitmap_block_index)))
                self.tag_data_mipmaps_box.insert(INSERT,
                            str(tag.bitmap_mipmaps_count(bitmap_block_index)))
                self.tag_data_swizzled_box.insert(INSERT,
                            str(bool(tag.swizzled())).upper())
                self.tag_data_format_box.insert(INSERT,
                            BITMAP_FORMAT_STRINGS[b_format])

                if b_type < len(BITMAP_SHORT_TYPE_STRINGS):
                    self.tag_data_type_box.insert(INSERT,
                                              BITMAP_SHORT_TYPE_STRINGS[b_type])
                else:
                    self.tag_data_type_box.insert(INSERT, "UNKNOWN")
                    
                if tag.is_xbox_bitmap:
                    if tag.processed_by_hboc():
                        self.tag_data_platform_box.insert(INSERT, 'XBOX')
                    else:
                        self.tag_data_platform_box.insert(INSERT, 'ARSENIC')
                else:
                    self.tag_data_platform_box.insert(INSERT, 'PC')

                for widget in(self.tag_data_height_box, self.tag_data_width_box,
                        self.tag_data_depth_box,  self.tag_data_mipmaps_box,
                        self.tag_data_type_box,   self.tag_data_format_box,
                        self.tag_data_swizzled_box, self.tag_data_platform_box,
                        self.tag_data_bitmap_count_box):
                    widget.config(state=DISABLED)





'''ENTER A DESCRIPTION FOR THIS CLASS WHEN I HAVE TIME'''
class BitmapConverterListWindow(Toplevel):

    def __init__(self, handler, parent, **options):
        Toplevel.__init__(self, parent, **options )
        
        '''THE PROGRAM MUST BE CLASS WITH VARIABLES SUCH AS TAG_COLLECTION'''
        self.handler = handler
        self.parent = parent

        #used to determine if it is safe to try to populate the taglist window
        self.populating_tag_window = False
        #this is used for determining how the list is currently sorted
        self.tag_list_sort_type = 0
        #this is used for determining whether the list is reversed or not
        self.tag_list_sort_reversed = False        
        
        self.initialize_tag_sort_mappings()
        
        self.protocol("WM_DELETE_WINDOW", self.parent.close_main_window)
        self.title("Tag List")

        self.prev_pos_x = 0
        self.prev_pos_y = 457
        self.geometry("743x200+"+str(self.prev_pos_x)+"+"+str(self.prev_pos_y))

        self.resizable(0, 1)
        self.minsize(width=743, height=200)
        self.maxsize(width=743, height=2048)

        #Make the menu bar
        self.tag_list_menubar = Menu(self)
        tag_list_menubar = self.tag_list_menubar
        
        tag_list_menubar.add_command(label="Sort by Path",
                         command=lambda:(self.sort_displayed_tags_by(0, True)) )
        tag_list_menubar.add_command(label="Sort by Type",
                         command=lambda:(self.sort_displayed_tags_by(2, True)) )
        tag_list_menubar.add_command(label="Sort by Format",
                         command=lambda:(self.sort_displayed_tags_by(4, True)) )
        tag_list_menubar.add_command(label="Sort by Pixel Data Bytes",
                         command=lambda:(self.sort_displayed_tags_by(6, True)) )
        
        self.types_settings_menu = Menu(tag_list_menubar, tearoff=False)
        self.formats_settings_menu = Menu(tag_list_menubar, tearoff=False)
        
        #we'll reference these locally to save screen space
        types_settings_menu = self.types_settings_menu
        formats_settings_menu = self.formats_settings_menu
        
        tag_list_menubar.add_cascade(label="Enable/Disable Types",
                                     menu=types_settings_menu)
        tag_list_menubar.add_cascade(label="Enable/Disable Formats",
                                     menu=formats_settings_menu)
        
        self.config(menu=tag_list_menubar)


        i = 0
        for b_type in (0,1,2):
            types_settings_menu.add_command(
                label=(BITMAP_TYPE_STRINGS[b_type]+" "+u'\u2713'),
                command=lambda T=b_type:self.toggle_types_allowed(T))
            
        for b_format in (0,1,2,3,6,8,9,10,11,14,15,16,17):
            formats_settings_menu.add_command(
                label=(BITMAP_FORMAT_STRINGS[b_format]+" "+u'\u2713'),
                command=lambda i=i, F=b_format:self.toggle_formats_allowed(i,F))
            i += 1

        self.tag_list_scrollbar_y = Scrollbar(self, orient="vertical")
        self.tag_list_scrollbar_x = Scrollbar(self, orient="horizontal")
        self.tag_list_listbox = Listbox(self, width=90,
                                   selectmode=EXTENDED, highlightthickness=0,
                                   xscrollcommand=self.tag_list_scrollbar_x.set,
                                   yscrollcommand=self._scroll_tag_list)
        
        self.tag_data_listbox = Listbox(self, width=25,
                                    selectmode=EXTENDED, highlightthickness=0,
                                    yscrollcommand=self._scroll_tag_data,)
        
        self.tag_list_scrollbar_x.config(command=self.tag_list_listbox.xview)
        self.tag_list_scrollbar_y.config(command=self._scroll_both_listboxes)

        self.tag_list_scrollbar_x.pack(side="bottom", fill="x")
        self.tag_list_scrollbar_y.pack(side="right",  fill="y")
        self.tag_list_listbox.pack(side="left", fill="both", expand=True)
        self.tag_data_listbox.pack(side="right",fill="both", expand=True)
        self.tag_list_listbox.bind('<<ListboxSelect>>',
                                   self.set_selected_tags_list )
        self.tag_data_listbox.bind('<<ListboxSelect>>',
                                   self.move_selection_to_paths_list )
        self.transient(self.parent)


    def reset_lists(self):
        self.tag_list_listbox.delete(0, END)
        self.tag_data_listbox.delete(0, END)


    def initialize_tag_sort_mappings(self):
        #since the order of the displayed tags can vary based on
        #how we want to display them, we use this list to map the
        #index's of the selected tags into the path of the tag 
        self.displayed_tag_index_mapping = []
        
        #this is used to store the paths of the tags that are
        #selected. this makes it easy to change the flags by
        #iterating through the list and changing them
        self.selected_tags = []
        
        #there are 4 types and 18 formats
        self.bitmap_formats_shown = [ True ]*18
        self.bitmap_types_shown   = [ True ]*4
        
        #we'll build these once the tags are loaded. they serve
        #the same purpose as the above list, to make it easy
        #and fast to change the displayed tags
        self.bitmaps_indexed_by_type_and_format = [[],[],[],[]]
        for b_type in range(4):
            for b_format in range(18):
                self.bitmaps_indexed_by_type_and_format[b_type].append([])
        self.bitmaps_indexed_by_size = {}


    def build_tag_sort_mappings(self):
        #we want to build the different sort
        #listsfor the displaying of the tags
        for filepath in self.handler.tags["bitm"]:
            #only run if the bitmap contains bitmaps
            tag = self.handler.tags["bitm"][filepath]
                
            b_type   = tag.bitmap_type()
            b_format = tag.bitmap_format()

            #put together the lists that'll allow us to
            #visually sort the tags in different ways
            pixel_bytesize = tag.pixel_data_bytes_size()
            
            if not pixel_bytesize in self.bitmaps_indexed_by_size:
                self.bitmaps_indexed_by_size[pixel_bytesize] = []

            self.bitmaps_indexed_by_type_and_format[b_type][
                b_format].append(filepath)
            self.bitmaps_indexed_by_size[pixel_bytesize].append(filepath)


    def set_selected_tags_list(self, event=None):
        '''used to set which tags are selected when the tags listbox
        is clicked so we can easily edit their conversion variables'''
        self.selected_tags = []
        indexes = self.tag_list_listbox.curselection()
        if len(indexes) > 1:
            for index in indexes:
                self.selected_tags.append(self.displayed_tag_index_mapping\
                                          [int(index)])
                
        elif len(indexes) == 1:
            self.selected_tags = [self.displayed_tag_index_mapping\
                                  [int(indexes[0])]]

            self.parent.select_proper_settings_window_settings()
            
            self.parent.tag_data_canvas.tk_selected_bitmap_index.set("0")
            self.parent.tag_data_canvas.display_selected_bitmap()


    def invert_selection(self):
        if self.parent.tags_loaded:
            self.tag_list_listbox.selection_clear(first=0,
                                     last=len(self.displayed_tag_index_mapping))
            
            for index in range(len(self.displayed_tag_index_mapping)):
                filepath = self.displayed_tag_index_mapping[index]
                
                #if the index wasn't selected we select it
                if filepath not in self.selected_tags:
                    self.tag_list_listbox.selection_set(index)
            self.set_selected_tags_list()


    #if we select a tag by clicking the data list
    #we'll select it in the paths list instead
    def move_selection_to_paths_list(self, event=None):
        if (len(self.tag_data_listbox.curselection()) > 0 ):
            self.tag_list_listbox.selection_set(self.tag_data_listbox.\
                                                curselection()[0])
            self.set_selected_tags_list()
        
        
    def toggle_types_allowed(self, b_type):
        if self.bitmap_types_shown[b_type]:
            self.types_settings_menu.entryconfig(b_type,
                             label=(BITMAP_TYPE_STRINGS[b_type]))
            self.bitmap_types_shown[b_type] = False
        else:
            self.types_settings_menu.entryconfig(b_type,
                             label=(BITMAP_TYPE_STRINGS[b_type]+" "+u'\u2713'))
            self.bitmap_types_shown[b_type] = True

        self.sort_displayed_tags_by(self.tag_list_sort_type)
        
    def toggle_formats_allowed(self, menu_element, b_format):
        if self.bitmap_formats_shown[b_format]:
            self.formats_settings_menu.entryconfig(menu_element,
                       label=(BITMAP_FORMAT_STRINGS[b_format]))
            self.bitmap_formats_shown[b_format] = False
        else:
            self.formats_settings_menu.entryconfig(menu_element,
                       label=(BITMAP_FORMAT_STRINGS[b_format]+" "+u'\u2713'))
            self.bitmap_formats_shown[b_format] = True

        self.sort_displayed_tags_by(self.tag_list_sort_type)


    def sort_displayed_tags_by(self, sortby, enable_reverse=False):
        if self.parent.tags_loaded and not self.populating_tag_window:
            self.displayed_tag_index_mapping = []

            formats_shown  = self.bitmap_formats_shown
            types_shown    = self.bitmap_types_shown
            display_map    = self.displayed_tag_index_mapping
            by_type_format = self.bitmaps_indexed_by_type_and_format

            bitmaps = self.handler.tags["bitm"]
            if sortby == 0:#sorting by path
                for filepath in sorted(bitmaps.keys()):
                    tag = bitmaps[filepath]
                    #only run if the bitmap contains bitmaps
                    if tag.bitmap_count()!= 0:
                        if (formats_shown[tag.bitmap_format()] and
                            types_shown[tag.bitmap_type()]):
                            display_map.append(filepath)
                            
            elif sortby == 2:#sorting by type
                for b_type in range(4):#loop through each format
                    for b_format in range(18):
                        #only add the tag index to the list if we've enabled it
                        if formats_shown[b_format] and types_shown[b_type]:
                            display_map.extend(by_type_format[b_type][b_format])
                            
            elif sortby == 4:#sorting by format
                for b_format in range(18):#loop through each format
                    for b_type in range(4):
                        #only add the tag index to the list if we've enabled it
                        if formats_shown[b_format] and types_shown[b_type]:
                            display_map.extend(by_type_format[b_type][b_format])
                            
            else:#sorting by size
                byte_sizes_in_order = sorted(self.bitmaps_indexed_by_size)
                for tagsize in byte_sizes_in_order:
                    for filepath in self.bitmaps_indexed_by_size[tagsize]:     
                        tag = bitmaps[filepath]
                        
                        if (formats_shown[tag.bitmap_format()] and
                            types_shown[tag.bitmap_type()]):
                            display_map.append(filepath)
                    
            self.tag_list_sort_type = sortby
            if not(self.tag_list_sort_reversed) and enable_reverse:
                self.tag_list_sort_reversed = True
                display_map.reverse()
            else:
                self.tag_list_sort_reversed = False
                
            self.populate_tag_list_boxes()


    def populate_tag_list_boxes(self):
        if not self.populating_tag_window:
            self.populating_tag_window = True
            self.reset_lists()

            #used to keep track of which index we are creating
            curr_tag_list_index = 0
            for index in range(len(self.displayed_tag_index_mapping)):
                filepath = self.displayed_tag_index_mapping[index]
                
                self.tag_list_listbox.insert(END,filepath)
                tag = self.handler.tags["bitm"][filepath]

                self.set_listbox_entry_color(END, filepath)
                
                curr_tag_list_index += 1

                b_type   = tag.bitmap_type()
                b_format = tag.bitmap_format()

                tag_str = (BITMAP_TYPE_LITERALS[b_type] +
                           BITMAP_FORMAT_LITERALS[b_format])

                bitmap_size = tag.pixel_data_bytes_size()
                if bitmap_size < 1024:
                    tag_str += str(bitmap_size) +"  B"
                elif bitmap_size < 1048576:
                    tag_str += str((bitmap_size+512)//1024) +"  KB"
                else:
                    tag_str += str((bitmap_size+524288)//1048576) +"  MB"
                
                self.tag_data_listbox.insert(END, tag_str)
                
            self.populating_tag_window = False
        

    def set_listbox_entry_color(self, listbox_index, filepath):
        if get_will_be_processed(self.handler.tags["bitm"][filepath],
                                 self.handler.default_conversion_flags["bitm"]):
            self.tag_list_listbox.itemconfig(listbox_index,
                                             bg='dark green', fg='white')
        else:
            self.tag_list_listbox.itemconfig(listbox_index,
                                             bg='white', fg='black')
            

    #these next functions are used for scrolling both tag list boxes at once.
    #they need to be in this class since they use the inherited handler
    #reference to know where the listbox and scrollbar objects are
    def _scroll_both_listboxes(self, *args):
        self.tag_list_listbox.yview(*args)
        self.tag_data_listbox.yview(*args)
        
    def _scroll_tag_list(self, *args):
        if (self.tag_data_listbox.yview() != self.tag_list_listbox.yview()):
            self.tag_data_listbox.yview_moveto(args[0])
        self.tag_list_scrollbar_y.set(*args)

    def _scroll_tag_data(self, *args):
        if (self.tag_list_listbox.yview() != self.tag_data_listbox.yview()):
            self.tag_list_listbox.yview_moveto(args[0])
        self.tag_list_scrollbar_y.set(*args)




'''ENTER A DESCRIPTION FOR THIS CLASS WHEN I HAVE TIME'''
class BitmapConverterHelpWindow(Toplevel):

    def __init__(self, parent, **options):
        Toplevel.__init__(self, parent, **options )
        
        self.parent = parent
        self.is_alive = True
        
        self.title("Useful Help")
        self.geometry("440x400")
        self.resizable(0, 1)
        self.minsize(width=300, height=300)
        self.protocol("WM_DELETE_WINDOW", self.close_help)

        #Make the menu bar
        self.help_window_menubar = Menu(self)
        str_tmp = ["Steps to using this program",
                   "Global Parameters", "General Parameters",
                   "Multipurpose Swap", "Format Specific Parameters",
                   "Format Conversion", "Miscellaneous"]
        for i in range(len(str_tmp)):
            self.help_window_menubar.add_command(label=str_tmp[i],
                             command=lambda i=i:(self.change_displayed_help(i)))
            
        self.config(menu=self.help_window_menubar)

        self.help_window_scrollbar_y = Scrollbar(self, orient="vertical")

        self.displayed_help_text_box = Text(self, bg='#ece9d8', state=NORMAL,
                                yscrollcommand=self.help_window_scrollbar_y.set)
        self.displayed_help_text_box.insert(INSERT,
                                        "Click a button on the menubar above.")
        self.displayed_help_text_box.config(state=NORMAL, wrap=WORD)
        
        self.help_window_scrollbar_y.config(
            command=self.displayed_help_text_box.yview)

        self.help_window_scrollbar_y.pack(side="right", fill="y")
        self.displayed_help_text_box.pack(side="left",fill="both", expand=True)
        self.transient(self.parent)

    def close_help(self):
        self.parent.help_window = None
        Toplevel.destroy(self)
    
    def change_displayed_help(self, help_type):
        self.displayed_help_text_box.delete('0.0', END)

        if help_type == 0:
            new_help_string = ('Steps:\n\n1: click "Browse..." and select the folder containing bitmaps that you want to operate on. ' +
                               'This does not have to be a root tags folder, just a folder containing bitmap tags.\n\n' +
                               '2: Hit "Load" and wait for the program to say it is finished indexing and loading all the tags.\n\n' +
                               '3: Choose a tag or multiple tags in the "tag List" window and, in the main window, specify what format you ' +
                               'want them converted to, how many times to cut the resolution in half, and any other conversion settings.\n\n' +
                               '4: Hit "Run"\n\n5: Go make a sandwich cause this may take a while.....\n\n' +
                               '6: Once the conversion is finished, a debug log will be created in the folder where the bitmap converter is ' +
                               "located and the tag list will be cleared. The log's name will be the timestamp of when it was created.")

        elif help_type == 1:
            new_help_string = ("---Prune Tiff data---\n   Removes the uncompressed original TIFF data from the tag to" +
                               ' reduce its size. This data is pruned by tool when the tag is compiled into a map, but if you wish to reduce'+
                               ' the size of your tags folder or reduce the size of tags you upload to Halomaps, then this may come of use.'+
                               '\n\n\n---Backup old tags---\n   Tells the program to rename the tag being modified with a ".backup" extension' +
                               ' after it has completely written the new, modified tag. Only the oldest backup will be kept.'+
                               '\n\n\n---Read only mode---\n   Prevents the program from making edits to tags. Instead, a detailed log will be' +
                               ' created containing a list of all the bitmaps located in the folder that was specified. The bitmaps will be sorted' +
                               ' by type(2d, 3d, cubemap), then format(r5g6b5, dxt1, a8r8g8b8, etc), then the number of bytes the pixel data takes up.'+
                               '\n\n\n---Write debug log---\n   Tells the program to write a log of any successes and errors encountered while' +
                               ' preforming the conversion. If a tag is skipped it will be reported as an error.')
        elif help_type == 2:
            new_help_string = ('---Save as Xbox/PC tag---\n   Xbox and PC bitmaps are slightly different in the way they are saved. Xbox has the' +
                               ' pixel data for each bitmap padded to a certain multiple of bytes and cubemaps have the order of their mipmaps and' +
                               ' faces changed. A few other differences exist, but these all make a big difference. Save to the correct format.' +
                               '\n\n---Save as swizzled/un-swizzled---\n   Texture swizzling is not supported on PC Halo, but is required for good' +
                               ' preformance in non-DXT bitmaps on Xbox Halo. Swizzling swaps pixels around in a texture and makes them unviewable to' +
                               ' humans. For PC, save as un-swizzled; for Xbox, save as swizzled. DXT textures can not be swizzled so'+" don't"+' worry.' +
                               '\n\n---Number of times to halve resolution---\n   I tried to think of a shorter way to phrase it, I really did. This is' +
                               ' pretty obvious, but what' + " isn't" + ' so obvious is that if a bitmap has mipmaps the way the program will halve' +
                               ' resolution is by removing however many of the biggest mipmaps you tell it to.' +
                               '\n   If no mipmaps exist (HUD elements for example) the program will use a slower method of downresing, using a simple' +
                               ' bilinear filter to merge pixels.')
        elif help_type == 3:
            new_help_string = ('   PC multipurpose bitmaps channel usage:\nAlpha: Color Change\nRed: Detail Mask\nGreen:' +
                               ' Self Illumination\nBlue: Specular\Reflection\n\n   Xbox multipurpose bitmaps channel usage:' +
                               ' \nAlpha: Detail Mask\nRed: Specular\Reflection\nGreen: Self Illumination\nBlue: Color change\n\n   This program can swap the' +
                               ' channels from PC order to Xbox order or vice versa. If you want to swap them though, make sure you are converting to a' +
                               " format that supports all the channels that you want to keep. For example, swapping an Xbox texture's channels to PC will" +
                               ' require an alpha channel in the new texture if you want to keep the color change channel.\n\n***NOTE*** If a' +
                               ' multipurpose swap setting is used then it will override the "Swap A8Y8 channels" setting if it is also set.')
        elif help_type == 4:
            new_help_string = ("---Alpha cutoff bias---\n   Some formats (DXT1 and A1R5G5B5) are able to have an alpha channel, but it's limited to one bit." +
                               ' This means the only possible values are solid white or solid black. "Alpha cutoff bias" is used as the divider where' +
                               ' an alpha value above it is considered solid white and a value below it is considered solid black. The default value is 127.' +
                               '\n\n---P-8 Bump Conversion Mode---\n   P8-bump only has a palette of 250 colors to choose from and when you compress a 32bit' +
                               ' or 16bit texture to it you are likely to lose some detail. This palette does not at all cover the full range of normals that' +
                               ' you may see in a normal map, and in fact actually misses a lot of the top left, top right, bottom left, and bottom right' +
                               ' tangent vectors that you may see. The two modes I have created each use the palette differently to achieve different results.' +
                               "\n   I could go into the specifics of this problem and how/why these two conversion methods exist, but here's the short simple" +
                               ' answer: Auto-bias is good when you want to preserve the depth of the normal map and Average-bias is good when you want to' +
                               ' preserve the smoothness of the normal map. Auto-bias sacrifices smoothness to allow the normal maps to stay vibrant and strong' +
                               " while Average-bias sacrifices the depth and strength of the normal map to allow the color gradient to stay more or less smooth." +
                               '\n   The default, and usually the best mode to use, is Auto-bias as the drop in smoothness is usually unnoticible.' +
                               '\n\n---Monochrome channel to keep---\n   In A8 format only the alpha data is stored and the intensity channel(RGB merged) is' +
                               ' assumed to be solid black.\n   In Y8 only the intensity channel is stored and the alpha is assumed to be solid white.' +
                               '\n   In AY8 only the pixel data of 1 channel is stored (just like in A8 and Y8), but this pixel data is used for both the' +
                               ' alpha and intensity channels. That means the same exact image is shared between the alpha and intensity channels no' +
                               ' matter what. This is useful for reticles for example.\n   This setting serves two purposes; to specify whether you want to' +
                               ' convert to A8 or Y8 when you select "A8/Y8*", and to specify which one of these two channels to keep when you convert to AY8.' +
                               ' Since only either the alpha or intensity pixel data is saved when converting to AY8 you need to specify which to use.' +
                               ' The default setting is intensity.\n\n---Swap A8Y8 channels---\n   On PC, HUD textures used in meters(like health and ammo)' +
                               ' have to be 32bit color. The RGB channels are used for the image that is displayed and the alpha is used for the gradient mask'
                               ' that erases parts of the meter if they are below a certain value.\n   On XBOX, HUD textures used in meters(like health and' +
                               ' ammo) have to be in a monochrome format. The alpha channel is used for the image that is displayed and the intensity channel' +
                               ' is used for the gradient mask that erases parts of the meter if they are below a certain value.\n   HUD meters converted from' +
                               ' PC to Xbox need to have their intensity and alpha channels swapped. This setting will swap them when you convert to or from' +
                               " an A8Y8 bitmap.\n\n---Color-Key Transparency---\n   You may know the DXT formats by Guerilla's names:" +
                               '"Compressed with color-key transparency"(DXT1), "Compressed with explicit alpha"(DXT3), and "Compressed with interpolated alpha"' +
                               '(DXT5). DXT1 bitmaps are actually capable of having an alpha channel, though it has some strict limitations. First off the alpha' +
                               " channel is 1bit, meaning either solid white or solid black. The other, BIGGER, limitation is that if a pixel's alpha is set to" +
                               ' full black then the red, green, and blue for that pixel are also full black.\n   This type of alpha channel is perfect for things' +
                               " where it renders as transparency, like on the holes for the warthog's chaingun belt, but should NEVER be used for things" +
                               ' where the alpha channel does not function as transparency, like in a multipurpose map or the base map in an environment shader.' +
                               '\n   This setting also determines whether or not an alpha channel is saved with P8 bitmaps. A transparent pixel, just like in DXT1'+
                               ', will be solid black in color.\n\n"Alpha cutoff bias" affects what is determined to be white and what is determined to be black.')
        elif help_type == 5:
            new_help_string = ('---Format to convert to---\nMore or less straight forward, but there are a few miscellaneous things you' +
                               ' should be aware of before you convert formats.\n\n* This program is capable of converting to the DXT formats,' +
                               ' though it uses a slightly different method for compression than Tool uses. This different method actually creates' +
                               ' better UI textures compressed as DXT5 than Tool, having little to no artifacts in most cases. My compression method' +
                               " isn't perfect though, and is absolute poopy crap when compressing normal maps to DXT. If a texture doesn't look good" +
                               ' as DXT when tool creates it try having tool compress it as 32 bit color and have this program turn it into DXT.' +
                               " The results may shock you.\n\n* Not all the formats this program can convert to are" +
                               ' supported by Custom Edition. P8-bump, A8Y8, AY8, Y8, and A8 are Xbox only formats.\n\n* Converting to 32bit color was' +
                               ' an afterthought and as such I did not make a button specifically for it. You CAN convert the Xbox only formats(P8,' +
                               ' A8Y8, AY8, Y8, A8) to 32 bit color though, as this would be the only way to make a usable Custom Edition texture from' +
                               ' them. When one of these formats is selected, the "P8*/32Bit"' + " button's function will be converting the bitmaps to" +
                               " 32 bit color. If a 32bit, 16bit, or DXT texture is selected though, the button's function will be converting the" +
                               ' selected tags to P-8 bump. If a mixture of these formats is selected the appropriate conversion will be used.' +
                               '\n\n* Bitmaps that are not a power of 2 dimensions will be skipped entirely. So much of this program revolves around' +
                               ' the bitmaps being in power of 2 dimensions that I did not want to try and rework all of it just to get those very' +
                               ' rare bitmap types incorporated. The CMD window will notify you of any bitmaps that are not power of 2 dimensions' +
                               ' and/or corrupt.\n\n---Extract to---\nSelf explanatory, but there are a few things you should be aware of.\n   1: ' +
                               'The folder that you selected when you hit "Browse" and "Load" will be considered as the "tags" folder. The folder that ' +
                               'the "tags" folder is in will have a "data" folder created in it'+"(if it doesn't already exist) and that is where the " +
                               'extracted bitmaps will be placed.\n   2: TGA can not handle having exactly 2 channels(A8Y8), nor can it handle 16 bit color ' +
                               'in the form of R5G6B6 or A4R4G4B4, nor ANY of the DXT formats. DDS will be used if you try to export one of these to TGA')
        elif help_type == 6:
            new_help_string = ('* If the program encounters an error it will be displayed on the Python CLI screen (the black empty CMD screen).' +
                               '\n\n* If you wish to move the windows independent of each other click "Un-dock Windows" on the menu bar.' +
                               '\n\n* The "tag List" window can sort the tags 4 different ways. If the same sorting method is clicked again it' +
                               ' will reverse the order the tags are displayed.\n\n* If you want to only show certain types of tags you can' +
                               ' enable and disable which ones show up in the tag List window. Look under the "Enable/Disable Types" and' +
                               ' "Enable/Disable Formats" and uncheck the types/formats you' + " don't want to show up." +
                               '\n\n* I was originally planning a preview thumbnail, but because it would slow down browsing through tags and' +
                               ' would be more annoying to implement than I care to deal with, I decided not to. Just deal with it and open' +
                               ' the tags in guerilla to see what they look like.\n\n* During the tag load/conversion process the text box at' +
                               ' the bottom of the main window will give information on which tag is being processed.' +
                               '\n\n* A tag being highlighted in green signifies that, based on the tags current conversion settings, it will be' +
                               ' processed in some way when "Run" is clicked. If a tag is white it will be ignored when "Run" is clicked.' +
                               '\n\n* The "Selected tag Information" window will display information about the selected tag, but ONLY if JUST one' +
                               ' tag is selected. If more than one tag is selected the info displayed will not update. Selecting a different bitmap' +
                               'index on the same window will change which bitmap the window is displaying information about.' +
                               '\n\n* If the program seems to be frozen then check the Python CLI screen(the black empty CMD screen). If it shows an' +
                               ' error then the program may indeed have frozen or crashed. If not then just give it time. Depending on how you are' +
                               ' converting it and the bitmaps dimensions, a conversion may take from a tenth of a second to 3 minutes.' +
                               " BUT AT LEAST IT'S AUTOMATED RIGHT?!?!?!\n\nMade by Moses")
        else:
            new_help_string = ""
        
        self.displayed_help_text_box.insert(INSERT, new_help_string)

