# Tag classes aren't stored in the cache maps, so we need to
# have a cache of them somewhere. Might as well do it manually
ustr = 'unicode_string_list'

bitmap_tag_extensions     = ('bitmap',)*853
sound_tag_extensions      = ('sound',)*376
loc_tag_extensions = _loc = [ustr]*176

# set the fonts
_loc[0] = _loc[1] = _loc[56] = _loc[58] = 'font'

# set the hud_message_text
_loc[4] = 'hud_message_text'

loc_tag_extensions = tuple(loc_tag_extensions)
