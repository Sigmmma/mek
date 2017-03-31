The highlight of this package of tools, Mozzarilla is essentially a replacement Guerilla with some huge improvements.
Here is a current list of the most prominent features of mozz:

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


Troubleshooting:

* If you changed config settings and now it wont load or stuff is too screwed up to use, delete the config. You can find it at PYTHON\Lib\site-packages\mozzarilla\mozzarilla.cfg where PYTHON is the location of your python installation.

* Cant think of anything else, but I'll add anything I can think of.


If you encounter a bug, send me the mozzarilla.log(if it creates one) and/or the
startup_crash.log(if it creates one) and fully describe what happened and what you
did to cause it. We've been having some issues with it running on Windows 10(it works
for R93 Sniper, but not Masterz), but it seems to run fine on Windows 7, somewhat
fine on Linux, and crashes on OSX.