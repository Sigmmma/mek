
#<!--
#
#                                                    ___
#                                           ___  \   \
#                                           \   \  \  \
#                                            \ \___________------___
#LOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOLOL(/  /_______loljet________/
#                                            /__/   |   /
#                                          n          /  /
#                                                      /  /
#                                                     /___ /
#
#
#-->

#The loljet can stay. -Fulsy

# 2019/11/06
#   Modified by Moses to properly export vertex normals and marker radii.
#   Modified to also be significantly faster(the linear searches through
#   arrays for each vert/tri were pissing me off and slowing shit down.)



#INFORMATION!
bl_info = {
    "name": "HBT Threshold .JMS Exporter",
    "author": "Original WaltzStreet script by Cyboryxmen, Modified by Fulsy & Moses",
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Export .JMS files for compilation by Tool.exe",
    "warning": "",
    "category": "Import-Export"}



import time
import os
import bpy
import mathutils
import math
import re

from decimal import *

from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

getcontext().prec = 13


#DECLARING ALL GLOBAL FUNCTIONS!
def throw_exception(failmessage, info, opinstance):
    print("Threshold Error!")
    print("Error message:%s" % failmessage)
    if failmessage == 0:
        opinstance.report({'ERROR'}, "Please link all nodes to one object!")
        print("please link all nodes to one object!")

    elif failmessage == 1:
        opinstance.report({'ERROR'}, "Frame node is missing.")

    elif failmessage == 2:
        opinstance.report({'ERROR'}, "There were no geometry to be exported. Please link all geometry to a single node!")

    elif failmessage == 3:
        print("You forgot to assign a material to geometry object:" + info)

    elif failmessage == 4:
        print("You linked object {} to more than 1 region".format(obj))


    print("")


def find_region(obj):
    found = None
    for collection in obj.users_collection:
        if found is not None:
            throw_exception(4, obj, opinstance)
        elif re.match("~", collection.name):
            found = collection.name

    return found


def find_last_parent(obj):
    testparent = obj.parent
    while testparent != None:
        obj = testparent
        testparent = obj.parent

    return obj


def find_last_node(obj):
    print(obj)
    testparent = obj.parent
    while (not re.match("frame", testparent.name, re.IGNORECASE) or
           re.match("bip01", testparent.name, re.IGNORECASE)):
        testparent = testparent.parent
    return testparent


def find_child(node):
    while child!="found":
        child = node.child


def find_root_node(node, mainframe, nodeslist):
    testframe = find_last_parent(node)
    if testframe not in nodeslist:
        nodeslist.append(testframe)

    if mainframe is None:
        return testframe
    elif testframe != mainframe:
        return None

    return mainframe


def deselect():
    if not bpy.ops.object.select_all.poll():
        bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.primitive_cube_add(align='WORLD', enter_editmode=False, location=(0, 0, 506.061), rotation=(0, 0, 0))
    bpy.ops.object.delete(use_global = False)


def select():
    if not bpy.ops.object.select_all.poll():
        bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='SELECT')


def select_all_layers():
    x = 0
    y = []
    y.append(bpy.context.view_layer.layer_collection.children)
    x+=1
    return y


def deselect_layers(y):
    x = 0
    for bool in y:
        bpy.context.view_layer.layer_collection.children
        x+=1



#MAKING IMPORT-EXPORT OPERATOR!
#This operator is the main flow control setup. It's also responsible for the file browser.
class ExportJMS(Operator, ExportHelper):
    bl_idname = "export_jms.export"
    bl_label = "Export JMS"

    filename_ext = ".jms"

    filter_glob = StringProperty(
            default="*.jms",
            options={'HIDDEN'},
            )

    def execute(self, context):
        return export_jms(self, self.filepath)


#This allows the operator to appear in the import/export menu
def menu_func_export(self, context):
    self.layout.operator(ExportJMS.bl_idname, text="Halo CE JMS file (.jms)")


def register():
    bpy.utils.register_class(ExportJMS)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportJMS)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()


class JmsVertex:
    node0 = -1
    node1 = -1
    node1_weight = 0
    pos = None
    norm = None
    uv = None


class JmsTriangle:
    v0 = 0
    v1 = 0
    v2 = 0
    region = 0
    material = 0


#Beginning of the export function
def export_jms(opinstance, filepath):
    layersSelected = []
    scene = bpy.context.scene

    blenderscale = bpy.context.scene.unit_settings.scale_length
    scale = Decimal(1/blenderscale)
    objectslist = list(bpy.context.scene.objects)


    #Lists of data for JMS file
    version_number = 8200
    node_checksum = 3251

    scene_modified = False
    mainframe = None
    directory = ""

    nodeslist = []
    materialslist = []
    texturedirectory = "<none>"

    markerslist = []
    geometrylist = []
    mesheslist = []
    regionslist = ["unnamed"]


    vertices = []
    triangles = []
    polymaterials = []
    getcontext().prec = 13


    #THE SORTING OF STUFF!
    #Picks out all markers, nodes, and mesh objects in the scene, and puts them into appropriate lists.
    print("------------Script start------------")

    layersSelected = select_all_layers()

    uses_armature = False
    for obj in objectslist:
        if (obj.name[0:5].lower() == 'frame' or obj.name[0:5].lower() == "bip01"):
            #A catch-all solution is employed here for if people want to use a simple object for a frame
            #or if they want to use an armature
            if uses_armature:
                pass
            elif obj.type == 'ARMATURE':
                nodeslist = list(obj.data.bones)
                uses_armature = True
            else:
                nodeslist.append(obj)

        elif re.match("#", obj.name):
            markerslist.append(obj)

        elif obj.type== 'MESH':
            geometrylist.append(obj)

    #Check to see if nodes exist
    print(list(nodeslist))
    if len(nodeslist)==0:
        throw_exception(1, "lol", opinstance)
        return {'CANCELLED'}

    print("geometrylist =", len(geometrylist))


    for node in nodeslist:
        print("checking node:" + node.name + "...")
        node_root = find_root_node(node, mainframe, nodeslist)

        if mainframe is None:
            mainframe = node_root

        if mainframe != node_root:
            mainframe = None
            break

    if mainframe is None:
        throw_exception(0, "lol", opinstance)
        return {'CANCELLED'}


    print("current mainframe:" + mainframe.name)
    del nodeslist[nodeslist.index(mainframe)]
    nodeslist.insert(0, mainframe)

    print("deleting unnnessary items...")
    if mainframe in geometrylist:
        del geometrylist[geometrylist.index(mainframe)]
    elif mainframe in markerslist:
        del markerslist[markerslist.index(mainframe)]

    # Comb through geometry list, remove objects not linked to frame from list
    for obj in geometrylist:
#        print(obj)
        testparent = find_last_parent(obj)
        print("testparent:", testparent)
        if testparent != mainframe:
            del geometrylist[geometrylist.index(obj)]

#    print(geometrylist)

#    for obj in markerslist:
#        testparent = find_last_parent(obj)
#        if testparent!=mainframe:
#            del markerslist[markerslist.index(obj)]

    if len(geometrylist) == 0:
        throw_exception(2, "lol", opinstance)
        return {'CANCELLED'}


    print("gathering materials...")
    for obj in geometrylist:
        if len(obj.material_slots)!=0:
            for slot in obj.material_slots:
                if slot.material not in materialslist:
                    materialslist.append(slot.material)
        else:
            throw_exception(3, obj.name, opinstance)
            return {'CANCELLED'}

    print("gathering regions...")
    for collections in bpy.data.collections:
        regionslist.append(collections.name)

    try:
        regionslist[0]
    except:
        bpy.ops.group.create(name="unnamed")
        regionslist.append(bpy.data.groups["unnamed"])



    #THE REAL FUN BEGINS!
    #Prepare mesh object for exporting.
#    print("converting geometry object to mesh...")
    deselect()
    for obj in geometrylist:
        obj.select_set(state = True)
#        bpy.ops.object.duplicate(linked = False)
        mesheslist.append(bpy.context.selected_objects[0])
        deselect()

#    print("applying modifiers...")
#    for mesh in mesheslist:
#        deselect()
#        mesh.select = True
#        bpy.context.scene.objects.active = mesh
#        bpy.ops.object.convert(target='MESH', keep_original = False)
#        scene_modified = True

#    print("UV unwrapping wrapped objects...")
#    for mesh in mesheslist:
#        deselect()
#        mesh.select = True
#        bpy.context.scene.objects.active = mesh
#        try:
#            mesh.data.uv_layers.active.data
#        except:
#            bpy.ops.uv.smart_project(angle_limit = 66, island_margin = 0, user_area_weight = 0)
#            scene_modified = True

#    print("triangulating faces...")
#    for mesh in mesheslist:
#        deselect()
#        mesh.select = True
#        bpy.context.scene.objects.active = mesh
#        if not bpy.ops.mesh.quads_convert_to_tris.poll():
#            bpy.ops.object.editmode_toggle()
#        bpy.ops.mesh.select_all(action='SELECT')
#        bpy.ops.mesh.quads_convert_to_tris()
#        bpy.ops.object.editmode_toggle()
#        scene_modified = True

    print("gathering faces and vertices...")
    print(mesheslist)
    for mesh in mesheslist:
        region_name = find_region(mesh)
        if region_name is None:
            region_name = regionslist[0]

        region = regionslist.index(region_name)

        node_index = nodeslist.index(find_last_node(mesh))
        matrix = mesh.matrix_world
        deselect()
        mesh.select_set(state = True)

        bpy.context.view_layer.objects.active = mesh

        uv_layer = mesh.data.uv_layers.active.data
        mesh_loops = mesh.data.loops
        mesh_verts = mesh.data.vertices

        for face in mesh.data.polygons:
            jms_triangle = JmsTriangle()
            triangles.append(jms_triangle)

            jms_triangle.v0 = len(vertices)
            jms_triangle.v1 = len(vertices) + 1
            jms_triangle.v2 = len(vertices) + 2
            jms_triangle.region = region
            jms_triangle.material = materialslist.index(mesh.data.materials[face.material_index])
            for loop_index in face.loop_indices:
                vert = mesh_verts[mesh_loops[loop_index].vertex_index]
                uv = uv_layer[loop_index].uv

                jms_vertex = JmsVertex()
                vertices.append(jms_vertex)

                pos  = matrix@vert.co
                norm = matrix@(vert.co + vert.normal) - pos
                jms_vertex.node0 = node_index
                jms_vertex.pos = pos
                jms_vertex.norm = norm
                jms_vertex.uv = uv

    print("preparation complete!")
    print("Here are the meshes to be exported:")
    for mesh in mesheslist:
        print(mesh.name)

    print("")
    print("cleaning up...")

    deselect()
    # Delete all the meshes if we modified them
    if scene_modified:
        for mesh in mesheslist:
            mesh.select_set(state = True)
        bpy.ops.object.delete(use_global = False)

    deselect_layers(layersSelected)

    print("\n\n")
    print("beginning JMS data export!")
    print("\n\n")

#Actual writing to file begins here.

    with open(filepath, 'w') as f:
        f.write("%s\n" % version_number)
        f.write("%s\n" % node_checksum)

        f.write("%s\n" % len(nodeslist))
        for node in nodeslist:
            print("writing node data:{}...".format(node.name))
            child0 = -1
            child1 = -1
            matrix = node.matrix_world
            pos  = matrix@node.location
            quat = node.rotation_quaternion

            quat_i = Decimal(quat[1]).quantize(Decimal('1.000000'))
            quat_j = Decimal(quat[2]).quantize(Decimal('1.000000'))
            quat_k = Decimal(quat[3]).quantize(Decimal('1.000000'))
            quat_w = Decimal(quat[0]).quantize(Decimal('1.000000'))
            pos_x = Decimal(pos[0]).quantize(Decimal('1.000000'))*scale
            pos_y = Decimal(pos[1]).quantize(Decimal('1.000000'))*scale
            pos_z = Decimal(pos[2]).quantize(Decimal('1.000000'))*scale

            f.write("%s\n" % node.name)
            f.write("%s\n%s\n" % (child0, child1))
            f.write("%s\t%s\t%s\t%s\n" % (quat_i, quat_j, quat_k, quat_w))
            f.write("%s\t%s\t%s\n" % (pos_x, pos_y, pos_z))

        f.write("%s\n" % len(materialslist))
        for material in materialslist:
            print("writing material:{}...".format(material.name))
            f.write("%s\n" % material.name)
            f.write("%s\n" % texturedirectory)

        f.write("%s\n" % len(markerslist))
        for marker in markerslist:
            name = marker.name.replace(' ', '')[+1:]
            print("writing marker data:{}...".format(name))
            region = 0
            node = nodeslist.index(find_last_node(marker))
            matrix = marker.matrix_world

            radius = abs(marker.scale[0])
            pos  = matrix@marker.location
            quat = marker.rotation_quaternion

            quat_i = Decimal(quat[1]).quantize(Decimal('1.000000'))
            quat_j = Decimal(quat[2]).quantize(Decimal('1.000000'))
            quat_k = Decimal(quat[3]).quantize(Decimal('1.000000'))
            quat_w = Decimal(quat[0]).quantize(Decimal('1.000000'))
            pos_x = Decimal(pos[0]).quantize(Decimal('1.000000'))*scale
            pos_y = Decimal(pos[1]).quantize(Decimal('1.000000'))*scale
            pos_z = Decimal(pos[2]).quantize(Decimal('1.000000'))*scale

            f.write("%s\n" % name)
            f.write("%s\n" % region)
            f.write("%s\n" % node)
            f.write("%s\t%s\t%s\t%s\n" % (quat_i, quat_j, quat_k, quat_w))
            f.write("%s\t%s\t%s\n" % (pos_x, pos_y, pos_z))
            f.write("%s\n" % radius)

        f.write("%s\n" % len(regionslist))
        for region in regionslist:
            print("writing region data:{}...".format(region))
            f.write("%s\n" % region)

        f.write("%s\n" % len(vertices))
        print("here comes the big one!")
        for jms_vertex in vertices:
            pos  = jms_vertex.pos
            norm = jms_vertex.norm
            uv   = jms_vertex.uv

            pos_x = Decimal(pos[0]).quantize(Decimal('1.000000'))*scale
            pos_y = Decimal(pos[1]).quantize(Decimal('1.000000'))*scale
            pos_z = Decimal(pos[2]).quantize(Decimal('1.000000'))*scale

            norm_i = Decimal(norm[0]).quantize(Decimal('1.000000'))
            norm_j = Decimal(norm[1]).quantize(Decimal('1.000000'))
            norm_k = Decimal(norm[2]).quantize(Decimal('1.000000'))

            tex_u = Decimal(uv[0]).quantize(Decimal('1.000000'))
            tex_v = Decimal(uv[1]).quantize(Decimal('1.000000'))

            vert_string =  "%s\n" % jms_vertex.node0
            vert_string += "%s\t%s\t%s\n" % (pos_x, pos_y, pos_z)
            vert_string += "%s\t%s\t%s\n" % (norm_i, norm_j, norm_k)
            vert_string += "%s\n%s\n" % (jms_vertex.node1, jms_vertex.node1_weight)
            vert_string += "%s\n%s\n0\n" % (tex_u, tex_v)
            f.write(vert_string)

        f.write("%s\n" % len(triangles))
        x = 0
        for tri in triangles:
            tri_string = "%s\n%s\n%s\t%s\t%s\n" % (
                tri.region, tri.material, tri.v0, tri.v1, tri.v2)
            f.write(tri_string)
            x += 3

    print("\n\n")
    print("Export complete!")
    print("\n\n")


    return {'FINISHED'}

#memo
#   support for bones not yet implemented
#   export regions not yet implemented


