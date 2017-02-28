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

Halo_Bitmap_Optimizer_&_Converter:
You all know what this is.

Halo_TeXource:
Capable of ripping the uncompressed source textures from a directory of tags to tga files.

Mozzarilla:
The highlight of the library, Mozzarilla is essentially a replacement Guerilla with some
huge improvements. Just ask Masterz! Read the readme.txt for more information.

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
This one doesnt work right now due to changes I made, so dont even bother with it.

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


Updating:

1. Run upgrade.py
2. Yeah, thats it.