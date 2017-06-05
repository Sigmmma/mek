from os.path import join, splitext, dirname, basename
from ..class_repair import tag_cls_int_to_fcc, tag_cls_int_to_ext

"""
Some of these are here for shorthand, but they are mainly here as
a reminder to me of what types of folders are expected to be where.
"""

INF = float('inf')


def sanitize_name(name):
    sanitized_name = name.lower().strip(' /\\:*?"<>|')
    return sanitized_name


def get_tag_id(tag_ref):
    main_id = tag_ref.id[0]
    if main_id == 0xFFFF and tag_ref.id[1] == 0xFFFF:
        return None
    return main_id


root_dir = ""

# directories inside the root_dir
camera_dir     = "camera\\"
characters_dir = "characters\\"
cinematics_dir = "cinematics\\"
dialog_dir     = "dialog\\"
effects_dir    = "effects\\"
globals_dir    = "globals\\"
item_coll_dir  = "item collections\\"
levels_dir     = "levels\\"
powerups_dir   = "powerups\\"
rasterizer_dir = "rasterizer\\"
scenery_dir    = "scenery\\"
sky_dir        = "sky\\"
sound_dir      = "sound\\"
ui_dir         = "ui\\"
vehicles_dir   = "vehicles\\"
weapons_dir    = "weapons\\"


# general purpose directories used in MANY things
shaders_dir = "shaders\\"
effects_dir = "effects\\"
bitmaps_dir = "bitmaps\\"
shared_dir  = "shared\\"  # for anything shared between tags


# directories inside "object" directories(weapon, vehicle, biped, scenery, etc)
obje_shaders_dir = shaders_dir
obje_effects_dir = effects_dir
obje_bitmaps_dir = bitmaps_dir
obje_actor_dir   = "%s\\"  # directory for actors and their variants.
#                            insert the actors name as the directory name.


# directories inside the cinematics directory
cinematic_anims_dir   = "animations\\"
cinematic_effects_dir = effects_dir
cinematic_scenery_dir = "scenery\\"


# directories inside the effects directory
effect_decals_dir    = "decals\\"
effect_d_objects_dir = "detail_objects\\"
effect_lights_dir    = "lights\\"  # general lights used for special effects
effect_p_systems_dir = "particle systems\\"
effect_particles_dir = "particles\\"
effect_physics_dir   = "point physics\\"
effect_vehicle_dir   = "vehicle effects\\"
effect_zmaps_dir     = "zmaps\\"


# directories inside the decals directory.
# each of these will have a "bitmaps" directory inside it
decal_blood_dir   = "blood splats\\"
decal_bullets_dir = "bullet holes\\"
decal_vehicle_dir = "vehicle marks\\"


# directories inside the item collections directory
itmc_powerups = "powerups\\"
itmc_weapons  = "weapons\\"


# directories inside the levels directory
level_bitmaps_dir = bitmaps_dir
level_decals_dir  = "decals\\"
level_devices_dir = "devices\\"
level_music_dir   = "music\\"
level_scenery_dir = "scenery\\"
level_shaders_dir = shaders_dir


# directories inside sky directory
sky_shaders_dir = shaders_dir
sky_bitmaps_dir = bitmaps_dir


# directories inside sound directory
snd_sfx_dir       = "sfx\\"
snd_dialog_dir    = "dialog\\"
snd_music_dir     = "music\\"
snd_sound_env_dir = "sound environments\\"


# directories inside sound\sfx directory
sfx_ambience_dir = "ambience\\"
sfx_impulse_dir  = "impulse\\"
sfx_ui_dir       = "ui\\"
sfx_vehicles_dir = vehicles_dir
sfx_weapons_dir  = weapons_dir


# directories inside sound\sfx\impluse directory
imp_animations_dir = "animations\\"
imp_bodyfalls_dir  = "bodyfalls\\"
imp_doors_dir      = "doors\\"
imp_footsteps_dir  = "footsteps\\"
imp_glass_dir      = "glass\\"
imp_materials_dir  = "material_effects\\"
imp_panel_dir      = "panel\\"
imp_casings_dir    = "shellcasings\\"
imp_weap_drops_dir = "weapon_drops\\"


# directories inside ui directory
ui_devc_def_dir = "device_defaults\\"
ui_hud_dir      = "hud\\"
ui_shell_dir    = "shell\\"


# directories inside ui/hud directory
hud_bitmaps_dir = bitmaps_dir
################################################
'''This will really need to be fleshed out a lot
more for it to actually be useful to anyone.'''
################################################


# directories inside ui/shell directory
shell_bitmaps_dir = bitmaps_dir


# directories inside the weapon directory
weap_fp_dir = "%s\\fp"
