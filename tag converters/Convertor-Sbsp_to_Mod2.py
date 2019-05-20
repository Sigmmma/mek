#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

import os

from copy import deepcopy
from os.path import abspath, dirname, exists, splitext
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory
from traceback import format_exc

from reclaimer.model.jms import JmsNode, JmsMaterial, JmsMarker, JmsVertex,\
     JmsTriangle, JmsModel, GeometryMesh, PermutationMesh,\
     MergedJmsRegion, MergedJmsModel
from reclaimer.model.model_compilation import compile_gbxmodel
from reclaimer.hek.defs.objs.matrices import euler_to_quaternion
from reclaimer.hek.defs.sbsp import sbsp_def
from reclaimer.hek.defs.mod2 import mod2_def
from supyr_struct.defs.block_def import BlockDef
from supyr_struct.defs.constants import PATHDIV

PATHDIV = PATHDIV
curr_dir = abspath(os.curdir) + PATHDIV


def plane_verts_to_tris(plane, verts, base=0):
    ct = len(verts)
    reverse = False
    # use the cross product of the rays to the first 2 vertices to
    # get a vector we can cross with the plane vector to determine
    # if the triangles need to be facing the opposite direction.
    ray_a = [verts[1][0] - verts[0][0],
             verts[1][1] - verts[0][1],
             verts[1][2] - verts[0][2]
             ]
    ray_b = [verts[2][0] - verts[0][0],
             verts[2][1] - verts[0][1],
             verts[2][2] - verts[0][2]
             ]
    ray_c = [ray_a[1]*ray_b[2] - ray_a[2]*ray_b[1],
             ray_a[2]*ray_b[0] - ray_a[0]*ray_b[2],
             ray_a[0]*ray_b[1] - ray_a[1]*ray_b[0]
             ]
    reverse = (plane[0]*ray_c[0] +
               plane[1]*ray_c[1] +
               plane[2]*ray_c[2]) < 0

    # making a triangle fan, so first vert is always zero
    if reverse:
        return [(base, base + (i + 2) % ct, base + (i + 1) % ct)
                for i in range(ct - 2)]
    else:
        return [(base, base + (i + 1) % ct, base + (i + 2) % ct)
                for i in range(ct - 2)]


def planes_to_verts_and_tris(planes):
    # There are a few steps to calculating verts and faces from a
    # set of intersecting planes that create a closed convex form.
    #
    # 1: Get the edge lines for each plane by crossing the plane with
    #    each other plane. If they are parallel, their cross product
    #    will be the zero vector and should be ignored.
    # 2: Calculate the points of intersection for each planes edges
    #    to determine their vertices, skipping any vertices that are
    #    on the forward-facing side of any of the planes.
    # 3: Once 2 valid vertices have been determined for an edge, remove
    #    that edge from being used to calculate vertices(optimization).
    #    Also, create a line from the vertices and cross it with the
    #    edge to determine what order the vertices need to be traversed
    #    to make that edge. Use the one whose cross-product is positive.
    # 4: Sort the edges by picking a starting edge and going to the
    #    edge that starts with the vert the first edge ends with.
    #    Repeat this until all edges are seen.
    # 5: Loop over the sorted edges and create a list of vertices and
    #    a triangle strip list from them.
    #
    # There are some other optimizations that can be made, but this
    # is the basic method I have come up for doing this.
    verts = []
    tristrip = []
    return verts, tristrip


def get_bsp_surface_edge_loops(bsp, ignore_flags=False):
    surfaces = bsp.surfaces.STEPTREE
    edges = bsp.edges.STEPTREE

    edge_loops = {}
    # loop over each surface in the collision.
    # NOTE: These are polygonal, not just triangular
    for s_i in range(len(surfaces)):
        surface = surfaces[s_i]
        flags = flags.material
        e_i = surface.first_edge
        if ignore_flags:
            key = (surface.material, )
        else:
            key = (surface.material, flags.two_sided, flags.invisible,
                   flags.climbable, flags.breakable)

        surface_edges = set()
        vert_indices = []
        # loop over each edge in the surface and concatenate
        # the verts that make up the outline until we run out
        while e_i not in surface_edges:
            surface_edges.add(e_i)
            edge = edges[e_i]
            if edge[4] == s_i:
                e_i = edge[2]
                vert_indices.append(edge[0])
            else:
                e_i = edge[3]
                vert_indices.append(edge[1])

        edge_loops.setdefault(key, []).append(vert_indices)

    return edge_loops


'''
sbsp_body.collision_materials.STEPTREE
sbsp_body.collision_bsp.STEPTREE

sbsp_body.weather_polyhedras.STEPTREE
'''


def make_bsp_coll_jms_models(bsps, materials, nodes, ignore_flags=False):
    coll_jms_models = []
    for bsp in bsps:
        coll_edge_loops = get_bsp_surface_edge_loops(bsps[i], ignore_flags)

    return coll_jms_models


def make_marker_jms_model(sbsp_markers, nodes):
    markers = []
    for m in sbsp_markers:
        markers.append(
            JmsMarker(m.name, "bsp", 0, 0, m.rotation.i,
                      m.rotation.j, m.rotation.k, m.rotation.w,
                      m.position.x*100, m.position.y*100, m.position.z*100)
            )

    return JmsModel("bsp", 0, nodes, [], markers, ("markers", ))


def make_lens_flare_jms_model(lens_flare_markers, lens_flares, nodes):
    markers = []
    for m in lens_flare_markers:
        i, j, k, w = euler_to_quaternion(
            m.direction.i/128, m.direction.j/128, m.direction.k/128)
        lens_flare_name = lens_flares[m.lens_flare_index].shader.filepath

        markers.append(
            JmsMarker(lens_flare_name.split("\\")[-1], "bsp", 0, 0, i, j, k, w,
                      m.position.x*100, m.position.y*100, m.position.z*100)
            )

    return JmsModel("bsp", 0, nodes, [], markers, ("lens_flares", ))


def make_fog_plane_jms_models(fog_planes, nodes):
    fog_plane_jms_models = []
    materials = [JmsMaterial("fog_plane", "<none>", "$fog_plane")]

    plane_index = 0
    for fog_plane in fog_planes:
        tris = [
            JmsTriangle(0, 0, *raw_tri) for raw_tri in
            plane_verts_to_tris(fog_plane.plane, fog_plane.vertices.STEPTREE)
            ]
        verts = [
            JmsVertex(0, vert[0] * 100, vert[1] * 100, vert[2] * 100)
            for vert in fog_plane.vertices.STEPTREE
            ]

        fog_plane_jms_models.append(
            JmsModel("bsp", 0, nodes, materials, (),
                     ("fog_plane_%s" % plane_index, ), verts, tris))

        plane_index += 1

    return fog_plane_jms_models


def make_mirror_jms_models(clusters, nodes):
    mirror_jms_models = []
    mirrors = []

    for cluster in clusters:
        mirrors.extend(cluster.mirrors.STEPTREE)

    mirror_index = 0
    for mirror in mirrors:
        tris = [
            JmsTriangle(0, 0, *raw_tri) for raw_tri in
            plane_verts_to_tris(mirror.plane, mirror.vertices.STEPTREE)
            ]
        verts = [
            JmsVertex(0, vert[0] * 100, vert[1] * 100, vert[2] * 100)
            for vert in mirror.vertices.STEPTREE
            ]

        mirror_jms_models.append(
            JmsModel("bsp", 0, nodes,
                     [JmsMaterial(mirror.shader.filepath.split("\\")[-1])],
                     (), ("mirror_%s" % mirror_index, ), verts, tris))

        mirror_index += 1

    return mirror_jms_models


def make_cluster_portal_jms_models(planes, clusters, cluster_portals, nodes):
    cluster_portal_jms_models = []
    materials = [
        JmsMaterial("portal", "<none>", "+portal"),   # normal
        JmsMaterial("ai_deaf_portal", "<none>", "+&ai_deaf_portal")
        ]

    cluster_index = 0
    for cluster in clusters:
        cluster_verts = []
        cluster_tris = []
        for portal_index in cluster.portals.STEPTREE:
            portal = cluster_portals[portal_index[0]]
            shader = 1 if portal.flags.ai_cant_hear_through_this else 0
            portal_plane = planes[portal.plane_index]

            cluster_tris.extend([
                JmsTriangle(0, shader, *raw_tri) for raw_tri in
                plane_verts_to_tris(
                    portal_plane, portal.vertices.STEPTREE,
                    len(cluster_verts))
                ])
            cluster_verts.extend([
                JmsVertex(0, vert[0] * 100, vert[1] * 100, vert[2] * 100)
                for vert in portal.vertices.STEPTREE
                ])

        cluster_portal_jms_models.append(
            JmsModel("bsp", 0, nodes, materials, (),
                     ("cluster_%s_portals" % cluster_index, ),
                     cluster_verts, cluster_tris))
        # cluster_portal_jms_models[-1].optimize_geometry(True)

        cluster_index += 1

    return cluster_portal_jms_models


def sbsp_to_mod2(
        sbsp_path, include_lens_flares=True, include_markers=True,
        include_weather_polyhedra=True, include_fog_planes=True,
        include_mirrors=True, include_portals=True, include_collision=True,
        include_renderable=True, include_lightmaps=True):

    print("   Loading tags...")
    sbsp_tag = sbsp_def.build(filepath=sbsp_path)
    mod2_tag = mod2_def.build()

    print("   Converting...")
    sbsp_body = sbsp_tag.data.tagdata
    coll_mats = [JmsMaterial(mat.shader.filepath.split("\\")[-1])
                 for mat in sbsp_body.collision_materials.STEPTREE]

    base_nodes = [JmsNode("frame")]
    jms_models = []

    if include_markers:
        try:
            jms_models.append(make_marker_jms_model(
                sbsp_body.markers.STEPTREE, base_nodes))
        except Exception:
            print(format_exc())
            print("Could not convert markers")

    if include_lens_flares:
        try:
            jms_models.append(make_lens_flare_jms_model(
                sbsp_body.lens_flare_markers.STEPTREE,
                sbsp_body.lens_flares.STEPTREE, base_nodes))
        except Exception:
            print(format_exc())
            print("Could not convert lens flares")

    if include_fog_planes:
        try:
            jms_models.extend(make_fog_plane_jms_models(
                sbsp_body.fog_planes.STEPTREE, base_nodes))
        except Exception:
            print(format_exc())
            print("Could not convert fog planes")

    if include_mirrors:
        try:
            jms_models.extend(make_mirror_jms_models(
                sbsp_body.clusters.STEPTREE, base_nodes))
        except Exception:
            print(format_exc())
            print("Could not convert mirrors")

    if include_portals:
        try:
            jms_models.extend(make_cluster_portal_jms_models(
                sbsp_body.collision_bsp.STEPTREE[0].planes.STEPTREE,
                sbsp_body.clusters.STEPTREE, sbsp_body.cluster_portals.STEPTREE,
                base_nodes))
        except Exception:
            print(format_exc())
            print("Could not convert portals")

    if include_weather_polyhedra:
        try:
            pass
        except Exception:
            print(format_exc())
            print("Could not convert weather polyhedra")

    if False and include_collision:
        try:
            jms_models.extend(make_bsp_coll_jms_models(
                sbsp_body.collision_bsp.STEPTREE, coll_mats, base_nodes))
        except Exception:
            print(format_exc())
            print("Could not convert collision")

    if include_renderable:
        try:
            pass
        except Exception:
            print(format_exc())
            print("Could not convert renderable")

    if include_lightmaps:
        try:
            pass
        except Exception:
            print(format_exc())
            print("Could not convert lightmaps")

    mod2_tag.filepath = splitext(sbsp_path)[0] + "_SBSP.gbxmodel"
    compile_gbxmodel(mod2_tag, MergedJmsModel(*jms_models), True)
    return mod2_tag


class SbspToMod2Convertor(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Structure bsp to gbxmodel convertor v1.6")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.tags_dir.set(curr_dir + 'tags' + PATHDIV)

        # make the frames
        self.tags_dir_frame = LabelFrame(self, text="Tags directory")
        self.checkbox_frame = LabelFrame(self, text="Conversion settings")

        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.convert_btn = Button(
            self, text="Convert models", width=15, command=self.convert_models)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='x', side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.convert_btn.pack(fill='both', padx=5, pady=5)

        self.update()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry("%sx%s" % (w, h))
        self.minsize(width=w, height=h)

    def destroy(self):
        Tk.destroy(self)
        raise SystemExit(0)

    def tags_dir_browse(self):
        dirpath = askdirectory(initialdir=self.tags_dir.get())
        if dirpath:
            self.tags_dir.set(dirpath)

    def convert_models(self):
        print('Converting scenario_structure_bsps\n')
        start = time()
        tags_dir = self.tags_dir.get()

        if not tags_dir.endswith(PATHDIV):
            tags_dir += PATHDIV

        for root, dirs, files in os.walk(tags_dir):
            if not root.endswith(PATHDIV):
                root += PATHDIV

            for filename in files:
                filepath = root + filename
                if os.path.splitext(filename)[-1].lower() != (
                    '.scenario_structure_bsp'):
                    continue

                print('Converting: %s' % filepath.split(tags_dir)[-1])

                try:
                    mod2_tag = sbsp_to_mod2(filepath)
                    if mod2_tag:
                        mod2_tag.serialize(
                            temp=False, backup=False, int_test=False)
                except Exception:
                    print(format_exc())
                print()
        print('\nFinished. Took %s seconds' % (time() - start))

try:
    converter = SbspToMod2Convertor()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()