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


Convertor-Scex_to_Schi:
Converts a folder of shader_transparent_chicago_extended tags into shader_transparent_chicago tags.
Doesnt have the ability to choose the directory like all the other applications, but that's mainly
because this was actually my first app I ever wrote for editing Halo tags.


Halo_Animation_Fps_Changer:
Can convert a directory of animation tags from 30 fps to 60 fps, or from 60 to 30. In order to
preserve the original animation, the new frame count is actually 1 less than double, so a 30
frame animation will be turned into a 59 frame one. Converting an animation tag from 30 to 60
then back to 30 should give you the exact same animation(save for some floating point rounding errors).
Certain animations shouldn't have their animations changed though, such as aiming, suspension,
talking, etc. There is a new "special overlay" flag in each animation to specify it as one of
these special animations. Check that flag for each animation you dont want converted.


Halo_Tagset_Fps_Changer:
Can convert a directory of tags from 30 fps to 60 fps, or from 60 to 30. This differs from the
above program in that this converts every tag type OTHER than animations(and scenarios, but more
on that in a minute). Not all types of tags contain fps related variables though, so those that
dont wont need to be converted. Any tags that dont contain any fps related fields(or those whose
fps related fields are all zero) will be skipped. Scenarios contain fps related data, but most of
it is stuff that has to be manually changed, such as recorded animations, scripts, and cutscenes.

My parsing libraries add a flag to the header of all tags which determines if the tag is 60fps.
My tools use this flag to know if a tag needs to be converted to/from 60fps, so it is important.
All my libraries will preserve that flag(and Mozzarilla will check/uncheck it based on whether
or not 60fps is set in mozz when you save), but guerilla, sapien, and tool wont. This is why
the "Do nothing except flag all tags as 30 or 60fps" checkbox exists. This will go through the
specified directory of tags and set the flag to whatever mode the converter is set to convert to.
This is so you can easily flag your manually converted tags as 60fps, or fix the flag if you
accidentally opened a tag in tool/guerilla/sapien and saved it.


Halo_Bitmap_Optimizer_&_Converter:
Read the hboc readme.txt


Halo_TeXource:
Capable of ripping the uncompressed source textures from a directory of tags to tga files.


Mozzarilla:
Read the mozzarilla readme.txt


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


Halo_Meter_Extractor:
This is capable of extracting the bitmaps from all meter images in the tags folder to tga files.
This was a test, so dont even bother with it.


Halo_Animation_Decompressor:
Decompresses compressed animations found in model_animation tags.
This one isnt completely finished, as the decompression is screwy and I haven't figured
out exactly what else needs to be done. Honestly, dont even bother with it.


The MEK also contains a scripts folder with any Maxscripts that I've made or modified.
Currently there are Gbxmodel Importer and an Animation Importer scripts, which are
both modified variants of TheGhost's scripts.

The model importer is now also capable of importing xbox models, and shader bugs found
in previous versions as well as various crash related bugs have been fixed.

The animation importer can now import model_animiation_yelo tags, can use xbox models 
when prompted for a model, and has been fixed to work with tags containing more than
255 reflexives. This means you can finally open tags that have 256 or more animations.


Installation:

1. Install python 3.4 or higher(newest version is recommended)
    When installing, make sure to check "Add python to PATH"
2. Run MEK_Installer.pyw
3. Choose whether or not to install it portably(to a local
    directory) or to the machine you are running.
4. Click "Install"

Mozzarilla and all the programs in the MEK should be ready to use now. To open mozz, run
Mozzarilla, or Mozzarilla(console). Either one works, but the console one will print any
errors that occur if mozz fails to load.

Troubleshooting:

* If the updater doesn't seem to actually update anything, then clear your pip cache.
You can find it in users\app_data\pip\Cache
See here for more information: http://stackoverflow.com/a/41111916

* If programs wont run at all, add the version of python you installed to your PATH
environment variable. Google how to do that.

* If programs wont load or save tags then you have a permissions issue where python isnt
being allowed to modify/make files in the directory you are in.

One potential way to fix this is to locate your python installation, right click python.exe,
and set it to run with administrator privileges. Do the same for pythonw.exe.

Some users claim that this fix prevents their python programs from running at all, so if it
does then undo that administrator change and change the folder permissions on the folder
you are trying to edit tags in. It turns out that this is caused by certain versions of
windows due to some of their security measures, like UAC.

* If you changed config settings and now it wont load or stuff is too screwed up to use,
delete the config. You can find it at PYTHON\Lib\site-packages\mozzarilla\mozzarilla.cfg
where PYTHON is the location of your python installation. If you don't know where this is,
you can find it in your PATH variable. If not, then go looking lol.


Updating:

1. Run MEK_Installer.pyw
2. Choose whether or not to force reinstalling components.
3. Click "Upgrade"

If you need to try to reinstall the arbytmap module(because you installed the Visual C++
compiler and you are trying to get the accelerator modules to install) then simply run
the uninstall.py script and then the install.py script.