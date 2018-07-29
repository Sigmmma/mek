The MEK(Mo's Editing Kit) is my collection of tools I've made for editing Halo.
This will be updated whenever I commit changes, which means you guys can check in
whenever to see if something is new. Here's a quick rundown of what each thing is
as of the time of me writing this:


Halo_TeXource:
Capable of ripping the uncompressed source textures from a directory of tags to tga files.


Mozzarilla:
A tag editor that almost entirely replaces and surpasses Guerilla(can't preview sounds).
Read mozzarilla readme.txt for more details.


Pool:
A nice little wrapper for tool.exe with a lot of ease-of-use enhancements.
Read the pool_readme.txt for more information.


Refinery:
A new tag extractor that works for all types of Halo 1 maps and can extract open sauce tags
and MUCH more. Read the refinery_readme.txt for more information.




Additional readmes can be found for the scraps and convertors in the READMES folder.



The MEK also contains a scripts folder with any Maxscripts that I've made or modified.
Currently there are Gbxmodel Importer and an Animation Importer scripts, which are
both modified variants of TheGhost's scripts.

The model importer is now also capable of importing xbox models, and shader bugs found
in previous versions as well as various crash related bugs have been fixed.

The animation importer can now import model_animiation_yelo tags, can use xbox models 
when prompted for a model, and has been fixed to work with tags containing more than
255 reflexives. This means you can finally open tags that have 256 or more animations.




Installation:

1. Install python 3.5 or higher(newest version is recommended)
    When installing, make sure to check "Add python to PATH"
2. Run MEK_Installer.pyw
3. Choose whether or not to install it in a portable fashion(to
    a local directory) or to the machine you are running.
4. Click "Install/Update"

Mozzarilla and all the programs in the MEK should be ready to run now by double clicking.



Updating:

1. Run MEK_Installer.pyw
2. Click "Install/Update"



Troubleshooting:

* If programs wont run at all, add the version of python you installed to your PATH
environment variable. Google how to do that.


* If programs wont load or save tags then you have a permissions issue where python isnt
being allowed to modify/make files in the directory you are in.

One potential way to fix this is to change the folder permissions on the folder you
are trying to edit tags in. It turns out that this is caused by certain versions of
windows due to some of their security measures, like UAC.

If this is too inconvenient or doesn't work you can drag and drop the python file onto
the "Run Python as Admin.bat" or "Run Python as Admin(console).bat" to make it run with
admin privileges. The one you use determines if a python console window will show up.
This will fail if the path to the python file contains any of these special characters:
	- % & ^


* If you changed config settings and now it wont load or stuff is too screwed up to use,
delete the config. You can find it at PYTHON\Lib\site-packages\mozzarilla\mozzarilla.cfg
where PYTHON is the location of your python installation. If you don't know where this is,
you can find it in your PATH variable. If not, then go looking lol.