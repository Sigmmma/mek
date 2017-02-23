Installation:

1. Install python 3, and make sure to check(newest version is recommended)
    When installing, make sure to check "Add python to PATH"
2. Run install.py

Mozzarilla and all the programs in the MEK should be ready to use now. To open mozz, run Mozzarilla, or Mozzarilla(console). Either one works, but the console one will print any errors that occur if mozz fails to load.


Updating:

1. Run upgrade.py
2. Yeah, thats it.


About:

Mozzarilla is a file editing program, and is intended to be a complete replacement for Halo Custom Edition's Guerilla, with additional tools and ease of use upgrades. This is a screenshot of it with some of its extra tools shown. mozzarilla_0_9_3_by_chief_01-dasy581.png binilla test2.PNG

This is the last version that I'll be releasing for a while, since I'm going back to school and looking for a job. Mozzarilla is still incomplete, however it is completely capable of replacing most of Guerilla's features right now(except previewing bitmaps and sounds). New in this version is a fully functional undo/redo system. The only thing you cant undo is importing blocks, which will warn you that it will erase your undo history. Here is a current list of the most prominent features of mozz:

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

A preview video is in the works, but I think this is stable enough to release right now, so you guys can have it anyway. Just remember that if you encounter a bug, send me the mozzarilla.log(if it creates one) and/or the startup_crash.log(if it creates one) and fully describe what happened and what you did to cause it.

You need to install Python 3 to run Mozzarilla. Python is a virtual machine like Java; you need to install java to run java programs and python to run python programs.

Troubleshooting:

    If Mozzarilla wont load or save tags, locate your python installation, find the python.exe and pythonw.exe, right click each one and set them to run as an administrator.

    If you changed config settings and now it wont load or stuff is too screwed up to use, delete the config. You can find it at mozzarilla\mozzarilla.cfg

    Cant think of anything else, but I'll add anything I can think of.
