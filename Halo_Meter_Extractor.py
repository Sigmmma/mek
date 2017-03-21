from os.path import splitext
from traceback import format_exc

RED_FILL = b'\x00\x00\xff\x00'

try:
    from reclaimer.hek.handler import HaloHandler
    from supyr_struct import buffer
    from supyr_struct.defs.bitmaps.tga import tga_def

    #used for loading all meter tags that can be found
    metr_loader = HaloHandler(valid_def_ids="metr", print_test=False)

    metrdef = metr_loader.defs['metr']

    #replace the raw data struct of the meter image with the organized one
    meter_image_struct = metrdef.subdefs['meter_image'].descriptor
    
    #override the immutability of the frozendict
    dict.__setitem__(metrdef.descriptor[1][14], 'STEPTREE', meter_image_struct)
    
    tagsdir = metr_loader.datadir
    
    print("Press enter to begin extracting meter images.")
    input()

    metr_loader.index_tags()
    metr_loader.load_tags()
    
    tga_buffer = buffer.BytearrayBuffer()
    
    for meter_path in metr_loader.tags['metr']:
        try:
            print("Extracting '%s'..." % meter_path)
            #clear the buffer
            del tga_buffer[:]
            tga_buffer.seek(0)
            
            meter = metr_loader.tags['metr'][meter_path]

            tgaout = tga_def.build()
            tgaout.filepath = tagsdir + splitext(meter_path)[0] + '.tga'

            meterdata = meter.data.tagdata
            tgaheader = tgaout.data.header
            
            tgaheader.image_type.format.set_to("unmapped_rgb")
            tgaheader.width  = meterdata.width
            tgaheader.height = meterdata.height
            tgaheader.bpp = 32
            tgaheader.image_descriptor.alpha_bit_count = 8
            tgaheader.image_descriptor.screen_origin.set_to("upper_left")

            tgaout.data.pixels_wrapper.pixels = tga_buffer
            #write a solid red color to the image for the background
            tga_buffer.write(RED_FILL * tgaheader.width * tgaheader.height)

            lines = meterdata.meter_data.data

            #write each of the lines to the appropriate location
            for line in lines:
                tga_buffer.seek((line.x_pos + line.y_pos*tgaheader.width)*4)
                tga_buffer.write(line.line_data)
                
            tgaout.serialize(temp=False, int_test=False, backup=False)
        except Exception:
            print(format_exc())
            print("Above exception occurred while trying to extract " +
                  "meter image for:\n    %s\n\n" % meter_path)

    input("\nExtraction finished. Hit enter to exit.")

except Exception:
    print(format_exc())
    input()
