Refinery is a map extractor for games utilizing Bungie's Blam engine.

Here's a list of what Refinery can currently do:
    * Load and extract tags and data from Halo 1 Xbox, PC, CE, PC Demo, and Yelo maps
    * Load and extract tags and data from Stubbs the Zombie maps on PC and Xbox
    * Load and extract tags and data from CE(not PC) resource maps(loc.map, bitmaps.map, 
        and sounds.map)
    * Load and extract data from Halo 2 Vista maps

    * Display all pertinent information contained in the map's header, tag index, 
        scenario bsp headers, and Open sauce header(if it exists).
    * Has 3 ways to view the map contents: hierarchy, class, and hybrid
        Hierarchy sorts the tags by folder, like a regular directory structure.
        Class sorts all tags by their class(bitmap, gbxmodel, weapon, etc)
        Hybrid combines the two. It sorts everything by class, then inside
        each class is a directory structure of all tags of that class.

    * Extract all Halo 1 tags
    * Extract all Open sauce tags
    * Extract the cheape.map from Yelo maps
    * Extract most Stubbs the Zombie tags(excludes vege, imef, terr, bipd, vehi, and
        obje tag classes)
    * Fix mangled class names(aka Zteam protection)

    * Decompress and save Xbox maps
    * Save any loaded non-resource map(rearranges structures and renames protected
        tags so the map can be opened by other map tools)

    * Allows you to rename tags and folders of tags in any loaded non-resource map(tags
        have to at least partially exist in the map to rename them, i.e. they cannot be
        in a resource map.)
    * Allowspreviewing any tag in the map as if loaded in Mozzarilla. Changes made
        to the tag will NOT be saved to the map. Exporting works in the window, but rawdata
        will be in little-endian and other meta-specific details will not have been tweaked,
        so don't expect to be able to properly import ANY exported block into a tag.
    * Allows extraction by tag class as well as by folder or individual tags.


Here are all the known bugs that I can think of right now(I plan to fix them):
    * Tag explorers might not be sorted if you edit them(if you rename an entire folder
        and it disappears from the tree, it will be added to the bottom instead of alphabetically)


So now that you've read all that, here's a few tips on using Refinery:
    * You can double click an item in the map explorer(or select multiple and hit enter) to
        either rename it/them, add it/them to the queue, or preview the tag(only if selecting
        individual tags).
    * Renaming a folder to one that already exists puts all tags in that folder into the new one.
    * Renaming is case insensitive, and everything gets converted to lowercase. It's just
        easier this way.
    * If you just want stuff from the bitmaps.map, sounds.map, or loc.map just load that map
        up instead of an actual map.
    * If you only want one type of tag(all bitmaps) then change the explorer to "class" view,
        select the tag class(bitm in this case), and add it to the queue.
    * You can edit the details of something in the queue by double clicking it.