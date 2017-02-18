Mo's Editing Kit is a collection of tools for aiding in editing the game Halo Custom Edition. The most prominent of these tools is Mozzarilla, so here is a description of it:

Mozzarilla is intended to be a complete replacement for Guerilla with additional tools and ease of use upgrades.
![mozzarilla_0_9_3_by_chief_01-dasy581.png](https://bitbucket.org/repo/75eEL8/images/1306443699-mozzarilla_0_9_3_by_chief_01-dasy581.png)

This is the last version that I'll be releasing for a while, since I'm going back to school and looking for a job. Mozzarilla is still incomplete, however it is completely capable of replacing most of Guerilla's features right now(except previewing bitmaps and sounds). New in this version is a fully functional undo/redo system. The only thing you cant undo is importing blocks, which will warn you that it will erase your undo history. Here is a current list of the most prominent features of mozz:

*     Is able to switch between creating regular tags, open sauce tags, and gametypes.

*     Is able to view/edit hidden data(edit the config to enable it)

*     Is able to load corrupt tags for debugging purposes.

*     Can export/import blocks(pieces of a tag)

*     Makes backups of tags before editing.

*     Highly customizable user interface colors, widget sizes, hotkeys, etc.

*     Contains a customizable undo/redo feature.

*     Contains a hierarchy view for easily browsing a tags directory and loading tags.

*     Allows choosing any number of tags directories and switching between them at will.



Mozzarilla also contains a few special tools for aiding in modding:


*     Broken dependency scanner: For locating broken dependencies in the specified types of tags in the specified folder.

*     Dependency viewer: For easily seeing which tags a tag refers to and opening any of them.

*     Tag zipper: For making a zip folder containing a tag and every tag it depends on.


A preview video is in the works, but I think this is stable enough to release right now, so you guys can have it anyway. Just remember that if you encounter a bug, send me the mozzarilla.log(if it creates one) and/or the startup_crash.log(if it creates one) and fully describe what happened and what you did to cause it. We've been having some issues with it running on Windows 10(it works for R93 Sniper, but not Masterz), but it seems to run fine on Windows 7, somewhat fine on Linux, and crashes on OSX.

You need to install Python 3.4 or higher to run Mozzarilla. Python is a virtual machine like Java; you need to install java to run java programs and python to run python programs.


Troubleshooting:


*    If Mozzarilla wont load or save tags, locate your python installation, find the python.exe and pythonw.exe, right click each one and set them to run as an administrator.

*    If you changed config settings and now it wont load or stuff is too screwed up to use, delete the config. You can find it at reclaimer\halo\hek\programs\mozzarilla\mozzarilla.cfg

*    Cant think of anything else, but I'll add anything I can think of.