'''
Used for extracting tag definitions to a format that can be easily read.
'''
from reclaimer.field_types import Reflexive
from reclaimer.h2.field_types import H2MetaReflexive, H2Reflexive
from traceback import format_exc
from supyr_struct.tag import Tag


def find_enums(block, next_blocks):
    typ = block.TYPE
    if "enum" in typ.name.lower():
        next_blocks.append(block)
        return

    if typ.is_array:
        if block.get_desc('TYPE', 'SUB_STRUCT').is_block:
            if len(block) == 0:
                block.append()
            find_enums(block[0], next_blocks)
    elif typ.is_container or typ.is_struct:
        for i in range(len(block)):
            if block.get_desc('TYPE', i).is_block:
                find_enums(block[i], next_blocks)

    if (hasattr(block, "STEPTREE") and
            block.get_desc('TYPE', 'STEPTREE').is_block):
        find_enums(block.STEPTREE, next_blocks)


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
        tagdata = new_tag
        def_id = tag_def.def_id
        if isinstance(new_tag, Tag):
            tagdata = new_tag.data.tagdata
            blocks = [new_tag.data.blam_header, tagdata]
            f.write("%s (%s)\n\n" % (def_id, tag_def.ext[1:]))
        else:
            blocks = [tagdata]
            f.write("%s\n\n" % def_id)

        f.write("#"*60 + "\n")
        f.write("#" + (" "*20) + "STRUCTURES\n")
        f.write("\n\n")

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
                f.write("\n")
                f.write(block.pprint(show=("name", "type", "offset",
                                           "flags", "size")).\
                        replace("[", "{").replace("]", "}"))

                find_next_blocks(block, new_blocks)

            blocks = new_blocks

        f.write("\n\n")
        f.write("#"*60 + "\n")
        f.write("#" + (" "*20) + "ENUMERATORS\n")
        f.write("\n\n")

        # loop over each block until they are exhausted
        enums = []
        find_enums(tagdata, enums)
        i = j = 0
        enum_strs = []
        enum_strs_map = {}
        enum_names = []
        for enum in enums:
            name = ""
            b = enum
            while hasattr(b, 'NAME') and hasattr(b, 'parent'):
                if not (b.TYPE.is_array or b.NAME in ("tagdata", def_id) or
                        b.TYPE in (Reflexive, H2MetaReflexive, H2Reflexive)):
                    name = "%s.%s" % (b.NAME, name)
                b = b.parent
            name = name.rstrip(".")

            if not name:
                name = "UNNAMED_ENUM_%s" % i
                i += 1

            desc = enum.desc
            enum_str = "%s" + ("%s {\n" % enum.TYPE.name)
            for k in range(enum.ENTRIES):
                enum_str += "    %s = %s,\n" % (desc[k]['NAME'],
                                                desc[k]['VALUE'])
            enum_str += "    }\n\n"

            if enum_str in enum_strs_map:
                enum_names[enum_strs_map[enum_str]].append(name)
                continue

            enum_strs_map[enum_str] = j
            enum_strs.append(enum_str)
            enum_names.append([name])
            j += 1

        for i in range(len(enum_names)):
            name = ""
            names = enum_names[i]
            for j in range(len(names)):
                name = "%s = %s" % (names[j], name)
            f.write(enum_strs[i] % name)

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
