import os

from traceback import format_exc
from reclaimer.hek.handler import HaloHandler
from reclaimer.hek.defs.schi import schi_def
from reclaimer.hek.defs.scex import scex_def
from supyr_struct.field_types import Void

class ShaderRectifier(HaloHandler):
    # set this to "scex" to convert schi to scex, or "schi" for scex to schi
    target_id = "schi"
    # scex == shader_transparent_chicago_extended
    # schi == shader_transparent_chicago

    backup   = False
    log_filename = "Chicago_Shader_Rectifier.log"
    
    #initialize the class
    def __init__(self, **kwargs):
        self.target_id = kwargs.get("target_id", self.target_id)
        self.backup    = kwargs.get("backup", self.backup)
        kwargs["valid_def_ids"] = ("schi", "scex")

        tmp = self.default_defs_path

        self.default_defs_path = ''
        HaloHandler.__init__(self, **kwargs)

        self.add_def(schi_def)
        self.add_def(scex_def)

        # make slots in self.tags for the types we want to load
        self.reset_tags(self.defs.keys())

        self.default_defs_path = tmp

    #This is used to convert extended chicago tags
    #into regular ones and remove all extra layers
    def convert_shaders(self, **kwargs):
        #this is the string to store the entire debug log
        logstr = ("Debug log for CE-XBOX Shader Rectifier\n\n\n" +
                  "Removed extra layers from:\n\n")

        target_def = self.get_def(self.target_id)

        ################################################################
        '''WARNING: THIS NEXT STEP WILL TOTALLY EFF UP THE DEFINITIONS!!
        DONT LOAD ANY schi OR scex TAGS AFTER CALLING convert_shaders'''
        ################################################################
        __dsi__ = dict.__setitem__
        if self.target_id == 'schi':
            body_desc = self.get_def('scex').descriptor[1]  # body index = 1
            scex_desc = body_desc[1]  # scex index = 1
            attr_offs = list(scex_desc['ATTR_OFFS'])

            #scex extra flags index = 11
            attr_offs[6] = 96
            __dsi__(scex_desc[3], 'TYPE', Void)  # void the extra layers
            __dsi__(scex_desc[5], 'TYPE', Void)  # void the 2-stage maps
            __dsi__(scex_desc, 'ATTR_OFFS', attr_offs)  # replace offsets
            __dsi__(scex_desc, 'SIZE', 68)   # change the struct size
            __dsi__(body_desc, 'SIZE', 108)  # change the struct size
            
        elif self.target_id == 'scex':
            body_desc = self.get_def('schi').descriptor[1]  # body index = 1
            schi_desc = body_desc[1]  # schi index = 1
            attr_offs = list(schi_desc['ATTR_OFFS'])

            #schi extra flags index = 10
            attr_offs[5] = 108
            __dsi__(schi_desc[3], 'TYPE', Void)  # void the extra layers
            __dsi__(schi_desc, 'ATTR_OFFS', attr_offs)  # replace offsets
            __dsi__(schi_desc, 'SIZE', 80)   # change the struct size
            __dsi__(body_desc, 'SIZE', 120)  # change the struct size

        
        '''loop through both chicago and extended chicago tag types'''
        for def_id in self.tags:

            '''loop through each tag and remove extra
            layers and log them to a debug file'''
            for filepath in sorted(self.tags[def_id]):
                tag = self.tags[def_id][filepath]
                try:

                    '''CONVERT THE TAG'''
                    if def_id == 'schi' and self.target_id == 'scex':
                        tag.convert_to_scex()
                        del self.tags[def_id][filepath]
                    elif def_id == 'scex' and self.target_id == 'schi':
                        tag.convert_to_schi()
                        del self.tags[def_id][filepath]

                    el = tag.data.tagdata[1].extra_layers.extra_layers_array
                    '''REMOVE THE EXTRA LAYERS FROM THE TAG'''
                    if len(el):
                        logstr += "\n"+tag.filepath +"\nExtra Layers:"
                        
                        #we loop through each extra layer for the debug log
                        for layer in el:
                            #add the extra layer's path to the debug log
                            try:
                                ext = '.' + layer.tag_class.enum_name
                            except Exception:
                                ext = ''
                            logstr += "\n    " + layer.STEPTREE + ext

                    new_tag_path = tag.filepath.split(self.tagsdir)[1]
                    self.tags[def_id][new_tag_path] = tag
                    tag.definition = target_def
                except:
                    print("ERROR OCCURRED WHILE ATTEMPTING TO CONVERT:\n" +
                          '    ' + tag.filepath + '\n')
                    print(format_exc())
        #swap the tags around in the tag collection
        if self.target_id == 'scex':
            self.tags['scex'].update(self.tags['schi'])
            self.tags['schi'].clear()
        else:
            self.tags['schi'].update(self.tags['scex'])
            self.tags['scex'].clear()


        report, write_exceptions = self.write_tags(print_errors=False,
                                                   backup=self.backup)
        logstr += write_exceptions
        
        #create the debug and take care of renaming and deleting tags
        logstr += self.make_write_log(report, backup=self.backup)
        
        return logstr
        

    def run_test(self):
        input('This program will scan the tags directory and any \n"shader_'+
              'transprent_chicago_extended" tags that it finds will be \n'+
              'converted to regular chicago shaders to fix blending issues.\n'+
              
              '\nExtended chicago tags will NOT be deleted after being '+
              'converted. \nExtra layers will be removed from all '+
              'shader_transprent_chicago tags \nand converted '+
              'shader_transprent_chicago_extended tags.\n'+
              
              '\nAfter conversion a log will be created in this folder '+
              'detailing \nwhich tags had extra layers removed, the paths of '+
              'those extra \nlayers, and errors that occurred.\n'+
              '\nPress Enter to begin converting the shaders in:'+
              '\n    %s\n\n' % self.tagsdir)
        
        #Stream the data from the tags to class
        #constructs so the program can work with them
        if self.index_tags():
            self.load_tags()
        
            #now we finally fix/convert the shaders
            results = self.convert_shaders()
            
            #save the debug log to a file
            self.make_log_file(results)
        else:
            #if something went wrong earlier this will notify the user
            input('Tags directory is either empty, doesnt '+
                  'exist, or cannot be accessed')
            raise SystemExit()
        
        input('-'*80 + '\nFinished rectifying shaders.\nCheck the tags '+
              'directory for the changelog.\n' + '-'*80 +
              '\n\nPress enter to exit.')

if __name__ == "__main__":
    try:
        rectifier = ShaderRectifier(target_id="scex")
        rectifier.run_test()
    except Exception:
        print(format_exc())
        input()
