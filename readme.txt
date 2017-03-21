This is my collection of tools I've made for editing Halo. You guys wont find all of them useful,
but many of them are. This will be updated whenever I commit changes, which means you guys can
check in whenever to see if something is new. Here's a quick rundown of what each thing is as
of the time of me writing this:

Convertor-Coll_to_Mod2:
Converts a directory of model_collision_geometry tags into gbxmodel tags so they can be imported
into 3dsmax. The converter requires that you also provide the gbxmodel that the collision goes to,
otherwise it wont be able to rig anything or position the nodes. It will try to locate a gbxmodel
with the same name as the collision, but if it cant it'll ask you to select it.
The converted model will have the same name as the gbxmodel, but with "_COLLISION" on the end.

For importing the model into max, it's best to use the gbxmodel importer that comes with the
MEK(in the scripts folder) as it has some fixes and upgrades. Also, import the models with
"attach parts within region" as unchecked. This way you wont get all the pieces lumped into
one mesh. You'll need to weld together parts that use different materials in the same mesh,
but that's fine.

Convertor-Mode_to_Mod2:
Converts a directory of xbox models to gbxmodels.

Halo_Animation_Fps_Changer:
Can convert a directory of animation tags from 30 fps to 60 fps, or from 60 to 30. In order to preserve the original animation, the new frame count is actually 1 less than double, so a 30 frame animation will be turned into a 59 frame one. Converting an animation tag from 30 to 60 then back to 30 should give you the exact same animation(save for some floating point rounding errors).
Certain animations shouldn't have their animations changed though, such as aiming, suspension, talking, etc. There is a new "special overlay" flag in each animation to specify it as one of these special animations. Check that flag for each animation you dont want converted.

Halo_Bitmap_Optimizer_&_Converter:
You all know what this is.

Halo_TeXource:
Capable of ripping the uncompressed source textures from a directory of tags to tga files.

Mozzarilla:
The highlight of the library, Mozzarilla is essentially a replacement Guerilla with some huge improvements. Just ask Masterz! Here is a current list of the most prominent features of mozz:

    Is able to switch between creating regular tags, open sauce tags, and gametypes.

    Is able to view/edit hidden data(edit the config to enable it)

    Is able to load corrupt tags for debugging purposes.

    Can export/import blocks(pieces of a tag)

    Makes backups of tags before editing.

    Highly customizable user interface colors, widget sizes, hotkeys, etc.

    Contains a customizable undo/redo feature.

    Contains a hierarchy view for easily browsing a tags directory and loading tags.

    Allows choosing any number of tags directories and switching between them at will.


Mozzarilla also contains a few special tools for aiding in modding:

    Broken dependency scanner: For locating broken dependencies in the specified types of tags in the specified folder.

    Dependency viewer: For easily seeing which tags a tag refers to and opening any of them.

    Tag zipper: For making a zip folder containing a tag and every tag it depends on.



If you encounter a bug, send me the mozzarilla.log(if it creates one) and/or the startup_crash.log(if it creates one) and fully describe what happened and what you did to cause it. We've been having some issues with it running on Windows 10(it works for R93 Sniper, but not Masterz), but it seems to run fine on Windows 7, somewhat fine on Linux, and crashes on OSX.


Mozzarilla(console):
Same as the above, except it runs with a console window so you get a printout of errors if
it crashes when starting up.

Stubbs_Antr_Compiler:
Capable of compiling meta data extracted from a Stubbs the Zombie map into a working animation tag.

Stubbs_Mode_Compiler:
Capable of compiling meta data extracted from a Stubbs the Zombie map into a working model tag.

Stubbs_Soso_Compiler:
Capable of compiling meta data extracted from a Stubbs the Zombie map into a working open
sauce shader_model tag.

These next ones you shouldnt even bother with for now. They're either unfinished or just
little tests that I decided to keep around:

Convertor-Scex_to_Schi:
Converts a folder of shader_transparent_chicago_extended tags into shader_transparent_chicago tags.
Doesnt have the ability to choose the directory like all the other applications, but that's mainly
because this was actually my first app I ever wrote for editing Halo tags.

Halo_Meter_Extractor:
This is capable of extracting the bitmaps from all meter images in the tags folder to tga files.
This was a test, so dont even bother with it.

Halo_Tag_Hash_Cacher:
This was to go with my tag ripper that I was working on. Dont even bother with it, it doesnt
do anything right now.

Halo_Animation_Decompressor:
Decompresses compressed animations found in model_animation tags.
This one isnt completely finished, as the decompression is screwy and I haven't figured
out exactly what else needs to be done. Honestly, dont even bother with it.

Installation:

1. Install python 3, and make sure to check(newest version is recommended)
    When installing, make sure to check "Add python to PATH"
2. Run install.py

Mozzarilla and all the programs in the MEK should be ready to use now. To open mozz, run
Mozzarilla, or Mozzarilla(console). Either one works, but the console one will print any
errors that occur if mozz fails to load.

Troubleshooting:

    If programs wont load or save tags, locate your python installation, right click python.exe, and set it to run with administrator privileges. Do the same for pythonw.exe.

    If you changed config settings and now it wont load or stuff is too screwed up to use, delete the config. You can find it at PYTHON\Lib\site-packages\mozzarilla\mozzarilla.cfg where PYTHON is the location of your python installation. If you don't know where this is, you can find it in your PATH variable. If not, then go looking lol.


Updating:

1. Run upgrade.py
2. Yeah, thats it.