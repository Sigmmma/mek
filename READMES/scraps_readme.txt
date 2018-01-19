
These you shouldnt even bother with for now. They're either unfinished or just
little tests that I decided to keep around:


Halo_Animation_Fps_Changer:
Can convert a directory of animation tags from 30 fps to 60 fps, or from 60 to 30. In order to
preserve the original animation, the new frame count is actually 1 less than double, so a 30
frame animation will be turned into a 59 frame one. Certain animations shouldn't have their
animations changed though, such as aiming, suspension, talking, etc. There is a new flag titled
"special overlay" in each animation to specify it as one of these special animations.
Check that flag for each animation you do NOT want converted.

Converting an animation tag from 30 to 60 then back to 30 should give you the exact same
animation, with some exceptions. There will be some miniscule floating point rounding errors
from multiplying/dividing the dx/dy/dz/dyaw, and the frame indices(left/right foot, sound, loop,
keyframe1, keyframe2) may be 1 less than they should be(they will never be negative though).

Currently compressed animations CAN be converted from 30 to 60, but not back to 30. This is
because I don't fully understand the compressed animation structure, and my current way of
converting to 60 invloves more or less doubling everything in the "frame numbers" list.
That list specifies which frames of the animation are stored, so by doubling all of them I
space apart when each frame is played, effectively doubling the animation length. Cool huh?


Halo_Meter_Extractor:
This is capable of extracting the bitmaps from all meter images in the tags folder to tga files.
This was a test, so dont even bother with it.


Halo_Animation_Decompressor:
Decompresses compressed animations found in model_animation tags.
This one isnt completely finished, as the decompression is screwy and I haven't figured
out exactly what else needs to be done. Honestly, dont even bother with it.