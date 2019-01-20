These are convertors that turn one type of tag into another type. The names of the
types are the four character codes that the engine refers to them by, so if you need
to know the full names of what converts what, just run the program and read its title.


Convertor-Coll_to_Mod2:
Converts a directory of model_collision_geometry tags into gbxmodel tags so they can be imported
into 3dsmax. The converter requires that you also provide the gbxmodel that the collision goes to,
otherwise it wont be able to rig anything or position the nodes. It will try to locate a gbxmodel
with the same name as the collision, but if it cant it'll ask you to select it.
The converted model will have the same name as the gbxmodel, but with "_COLLISION" on the end.

For importing the model into max, it's best to use the gbxmodel importer that comes with the
MEK(in the scripts folder) as it has some fixes and upgrades. Also, import the models with
"attach parts within region" as unchecked. This way you wont get all the pieces lumped into
one mesh. You'll need to weld together parts that use different materials in the same mesh,
but that's fine.


Convertor-Mode_to_Mod2:
Converts a directory of xbox models to gbxmodels.


Convertor-Stubbs_XXXX_to_Halo_XXXX:
Converts an extracted Stubbs the Zombie tag into an equivalent Halo Custom Edition one.