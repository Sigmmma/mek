'''
Used for extracting tag definitions to a format that can be easily read.
'''
from reclaimer.field_types import Reflexive
from reclaimer.h2.field_types import H2MetaReflexive, H2Reflexive
from traceback import format_exc
from supyr_struct.tag import Tag


def find_next_blocks(block, next_blocks):
    typ = block.TYPE
    if typ in (Reflexive, H2MetaReflexive, H2Reflexive):
        block.STEPTREE.append()
        next_blocks.append(block.STEPTREE[-1])
        return

    if typ.is_array:
        if block.get_desc('TYPE', 'SUB_STRUCT').is_block:
            if len(block) == 0:
                block.append()
            find_next_blocks(block[0], next_blocks)

    elif typ.is_container or typ.is_struct:
        for i in range(len(block)):
            if block.get_desc('TYPE', i).is_block:
                find_next_blocks(block[i], next_blocks)

    if (hasattr(block, "STEPTREE") and
            block.get_desc('TYPE', 'STEPTREE').is_block):
        find_next_blocks(block.STEPTREE, next_blocks)


def print_tag_def(tag_def):
    # make an empty tag to do w/e with
    new_tag = tag_def.build()

    # write the tag definition to a file
    with open("%s_def.txt" % tag_def.def_id, "w") as f:
        if isinstance(new_tag, Tag):
            blocks = [new_tag.data.blam_header, new_tag.data.tagdata]
            f.write("%s (%s)\n\n" % (tag_def.def_id, tag_def.ext[1:]))
        else:
            blocks = [new_tag]
            f.write("%s\n\n" % tag_def.def_id)

        # loop over each block until they are exhausted
        while blocks:
            new_blocks = []

            for block in blocks:
                if not hasattr(block, "NAME"):
                    continue

                f.write("\n")
                f.write("\n")
                f.write("#"*60 + "\n")
                f.write("#" + (" "*20) + block.NAME + "\n")
                f.write("#"*60 + "\n")
                f.write("\n")
                f.write(block.pprint(show=("name", "type", "offset",
                                           "steptrees", "flags", "size")))

                find_next_blocks(block, new_blocks)

            blocks = new_blocks

tag_defs = {}

#import the tag definition so it can be used for making a blank tag
while not tag_defs:
    engine = input("Type in the definition set to use.\n"
                   "Valid values are hek, os_hek, os_v3_hek, and os_v4_hek.\n"
                   ">>> ")
    engine = engine.strip(" ").lower()
    print()
    classes = input("Type in the four character codes of the tag classes to write.\n"
                    "Use commas to separate each one. Spaces are ignored.\n"
                    "Examples include jpt!, vehi, DeLa, snd!, and bitm.\n"
                    ">>> ")
    print()
    classes = classes.replace("!", "_").replace("#", "_").replace("+", "_").\
              replace(" ", '').split(",")
    fixed_classes = []
    for cls in classes:
        fixed_classes.append(cls + " " * (4 - len(cls)))

    classes = []
    for cls in fixed_classes:
        try:
            def_name = cls
            if "_meta" in cls:
                def_name = cls.replace("_meta", "")
            exec("from reclaimer.%s.defs.%s import %s_def as tag_def" %
                 (engine, def_name, cls))
            tag_defs[cls] = tag_def
            classes.append(cls)
        except Exception:
            print("Could not load the %s definition" % cls)
            #print(format_exc())

for cls in classes:
    try:
        print_tag_def(tag_defs[cls])
    except Exception:
        print("Could not print the %s definition" % cls)
        print(format_exc())

input("Finished. Hit enter to exit. . .")
