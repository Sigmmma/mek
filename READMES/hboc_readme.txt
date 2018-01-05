There are two main purposes that this program serves:
    1: Allowing users to easily batch optimize their bitmaps.
    2: Converting any and all bitmap tags to/from PC/Xbox format for use by Arsenic/Halo CE.

Make sure to read all the stuff below before you start using it AND look in the "Useful help" window in the program if you have questions. There are some VERY important things you should be aware of that are explained in there.

This program requires Python 3.3 or higher to run.

The majority of you who will end up finding this useful are those messing with Arsenic. Halo Custom Edition will find it useful for it's ability to optimize bitmaps, convert bitmaps to different formats, make DXT textures using a different method than Tool does(which may end up looking better), it's general ability to help you get an idea of where you can optimize your maps the most as far as bitmaps go, and the ability to prune useless data from tags(thus freeing up space in your tags folder).



Steps:

1: Hit "Browse..." and select the folder containing bitmaps that you want to operate on. This does not have to be a root tags folder, just a folder containing bitmap tags.

2: Hit "Load" and wait for the program to say it is finished indexing and loading all the tags.

3: Choose a tag or multiple tags in the "Tag List" window and, in the main window, specify what format you want them converted to, how many times to cut the resolution in half, and any other conversion settings.

4: Hit "Convert"

5: Go make a sandwich cause this may take a while(even longer if you dont have the C accelerators installed).

6: Once the conversion is finished, a debug log will be created in the folder where the bitmap converter is located and the tag list will be cleared. The log's name will be the timestamp of when it was created.



Miscellaneous things to know:

* This program is capable of utilizing accelerator modules written in C for more than a 100x speed up, but they are distributed as source files that need to be compiled into binaries when you install the mek. If you dont have a certain version of the visual c++ compiler installed(depends on the version of python you're running) then it will default to the slow python functions.

Follow these instructions to install the correct compiler if you're interested in getting that massive speed up(more than 100x faster)https://blog.ionelmc.ro/2014/12/21/compiling-python-extensions-on-windows/. After the compiler is installed, just run the reinstall_arbytmap.py script.

* If the program encounters an error it will be displayed on the Python CLI screen(the black empty CMD screen).

* If you wish to move the windows independent of each other click "Un-dock Windows" on the menu bar.

* The "Tag List" window can sort the tags 4 different ways. If the same sorting method is clicked again it will reverse the order the tags are displayed.

* If you want to only show certain types of tags you can enable and disable which ones show up in the Tag List window. Look under the "Enable/Disable Types" and "Enable/Disable Formats" and uncheck the types/formats you don't want to show up.

* I was originally planning a preview thumbnail, but because it would slow down browsing through tags and would be more annoying to implement than I care to deal with, I decided not to. Just open the tags in guerilla to see what they look like.

* During the tag load/conversion process the text box at the bottom of the main window will give information on which tag is being processed

* A Tag being highlighted in green signifies that, based on the tags current conversion settings, it will be processed in some way when "Convert" is clicked. If a tag is white it will be ignored when "Convert" is clicked.

* The "Selected Tag Information" window will display information about the selected tag, but ONLY if JUST one tag is selected. If more than one tag is selected the info displayed will not update. Selecting a different bitmap index on the same window will change which bitmap the window is displaying information about.

* If the program seems to be frozen then check the Python CLI screen(the black empty CMD screen). If it shows an error then the program may indeed have frozen or crashed. If not then just give it time. Depending on how you are converting it and the bitmaps dimensions, a conversion may take from a tenth of a second to 3 minutes if the accelerators arent installed.


V1.5 includes:
    * ability to extract textures to DDS and TGA
    * ability to convert to and from all formats
    * ability to generate mipmaps for textures
    * easier window management
    * entirely rebuilt tag loading and bitmap editing structures
    * miscellaneous under the hood changes

V2.0 includes:
    * replacement of "dont reprocess tags" option with "prune tiff data"
    * accelerator modules written in C that can provide more than a 100x speedup in most cases
    * miscellaneous under the hood changes and bug fixes

V2.2 includes:
    * ability to save to PNG
    * miscellaneous under the hood changes and bug fixes