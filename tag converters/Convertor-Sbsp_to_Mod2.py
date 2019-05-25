#!/usr/bin/env python3

try: import mek_lib  # setup sys.path properly is portably installed
except ImportError: pass

import os

from copy import deepcopy
from os.path import abspath, join, isfile, splitext
from time import time
from tkinter import *
from tkinter.filedialog import askdirectory, askopenfilename
from traceback import format_exc

from reclaimer.model.jms import JmsNode, JmsMaterial, JmsMarker, JmsVertex,\
     JmsModel, MergedJmsModel, edge_loop_to_tris
from reclaimer.model.model_compilation import compile_gbxmodel
from reclaimer.hek.defs.objs.matrices import euler_to_quaternion, \
     planes_to_verts_and_edge_loops
from reclaimer.hek.defs.sbsp import sbsp_def
from reclaimer.hek.defs.mod2 import mod2_def
from supyr_struct.defs.block_def import BlockDef

curr_dir = join(abspath(os.curdir), "")


def planes_to_verts_and_tris(planes, region=0, mat_id=0, make_fans=False):
    raw_verts, edge_loops = planes_to_verts_and_edge_loops(planes)

    verts = [JmsVertex(0, v[0]*100, v[1]*100, v[2]*100) for v in raw_verts]
    tris = []
    # Calculate verts and triangles from the raw vert positions and edge loops
    for edge_loop in edge_loops:
        tris.extend(edge_loop_to_tris(edge_loop, region, mat_id, 0, make_fans))

    return verts, tris


def get_bsp_surface_edge_loops(bsp, ignore_flags=False):
    surfaces = bsp.surfaces.STEPTREE
    edges = bsp.edges.STEPTREE

    edge_loops = {}
    # loop over each surface in the collision.
    # NOTE: These are polygonal, not just triangular
    for s_i in range(len(surfaces)):
        surface = surfaces[s_i]
        flags = surface.flags
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


def make_bsp_jms_verts(bsp, node_transform=None):
    verts = []
    if node_transform:
        dx, dy, dz, _, rotation = transform[0], transform[1], transform[2]
        for vert in bsp.vertices.STEPTREE:
            trans = rotation * Matrix(vert[:3])
            verts.append(JmsVertex(
                0, (x + trans[0])*100, (y + trans[1])*100, (z + trans[2])*100))
    else:
        for vert in bsp.vertices.STEPTREE:
            verts.append(JmsVertex(
                0, vert[0]*100, vert[1]*100, vert[2]*100))

    return verts


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


def make_mirror_jms_models(clusters, nodes, make_fans=True):
    jms_models = []
    mirrors = []

    for cluster in clusters:
        mirrors.extend(cluster.mirrors.STEPTREE)

    mirror_index = 0
    for mirror in mirrors:
        tris = edge_loop_to_tris(
            len(mirror.vertices.STEPTREE), make_fan=make_fans)
        verts = [
            JmsVertex(0, vert[0] * 100, vert[1] * 100, vert[2] * 100)
            for vert in mirror.vertices.STEPTREE
            ]

        jms_models.append(
            JmsModel("bsp", 0, nodes,
                     [JmsMaterial(mirror.shader.filepath.split("\\")[-1])],
                     (), ("mirror_%s" % mirror_index, ), verts, tris))

        mirror_index += 1

    return jms_models


def make_fog_plane_jms_models(fog_planes, nodes, make_fans=True, optimize=False):
    jms_models = []
    materials = [JmsMaterial("fog_plane", "<none>", "$fog_plane")]

    plane_index = 0
    for fog_plane in fog_planes:
        tris = edge_loop_to_tris(
            len(fog_plane.vertices.STEPTREE), make_fan=make_fans)
        verts = [
            JmsVertex(0, vert[0] * 100, vert[1] * 100, vert[2] * 100)
            for vert in fog_plane.vertices.STEPTREE
            ]

        
        jms_model = JmsModel(
            "bsp", 0, nodes, materials, (),
            ("fog_plane_%s" % plane_index, ), verts, tris)

        if optimize:
            jms_model.optimize_geometry(True)

        jms_models.append(jms_model)
        plane_index += 1

    return jms_models


def make_cluster_portal_jms_models(planes, clusters, cluster_portals, nodes,
                                   make_fans=True, optimize=False):
    jms_models = []
    materials = [
        JmsMaterial("+portal", "<none>", "+portal"),
        JmsMaterial("+&ai_deaf_portal", "<none>", "+&ai_deaf_portal")
        ]

    cluster_index = 0
    portals_seen = set()
    for cluster in clusters:
        verts = []
        tris = []
        for portal_index in cluster.portals.STEPTREE:
            if portal_index[0] in portals_seen:
                continue

            portals_seen.add(portal_index[0])
            portal = cluster_portals[portal_index[0]]
            shader = 1 if portal.flags.ai_cant_hear_through_this else 0
            portal_plane = planes[portal.plane_index]

            tris.extend(edge_loop_to_tris(
                len(portal.vertices.STEPTREE), mat_id=shader,
                base=len(verts), make_fan=make_fans)
                                )
            verts.extend(
                JmsVertex(0, vert[0] * 100, vert[1] * 100, vert[2] * 100)
                for vert in portal.vertices.STEPTREE
                )
        
        jms_model = JmsModel(
            "bsp", 0, nodes, materials, (),
            ("cluster_%s_portals" % cluster_index, ), verts, tris)

        if optimize:
            jms_model.optimize_geometry(True)

        jms_models.append(jms_model)
        cluster_index += 1

    return jms_models


def make_weather_polyhedra_jms_models(polyhedras, nodes, make_fans=True):
    jms_models = []
    materials = [JmsMaterial("+weatherpoly", "<none>", "+weatherpoly")]

    polyhedra_index = 0
    for polyhedra in polyhedras:
        verts, tris = planes_to_verts_and_tris(
            polyhedra.planes.STEPTREE, make_fans=make_fans)
        
        jms_models.append(JmsModel(
            "bsp", 0, nodes, materials, (),
            ("weather_polyhedra_%s" % polyhedra_index, ), verts, tris))

        polyhedra_index += 1

    return jms_models


def make_bsp_coll_jms_models(bsps, materials, nodes, node_transforms=(),
                             ignore_flags=False, make_fans=True):
    jms_models = []
    bsp_index = 0
    for bsp in bsps:
        coll_edge_loops = get_bsp_surface_edge_loops(bsp, ignore_flags)
        node_transform = node_transforms[bsp_index] if node_transforms else None

        coll_materials = []
        mat_info_to_mat_id = {}
        # create materials from the provided materials and the
        # info on the collision properties of each surface.
        for mat_info in coll_edge_loops:
            src_material = materials[mat_info[0]]
            material = JmsMaterial(src_material.name)
            if not ignore_flags:
                if len(mat_info) > 1: material.double_sided = mat_info[1]
                if len(mat_info) > 2: material.large_collideable = mat_info[2]
                if len(mat_info) > 3: material.ladder = mat_info[3]
                if len(mat_info) > 4: material.breakable = mat_info[4]
                material.collision_only = not material.large_collideable
                material.double_sided &= not material.large_collideable
                material.name = material.properties + material.name
                material.shader_path = material.properties + material.shader_path
                material.properties = ""

            mat_info_to_mat_id[mat_info] = len(coll_materials)
            coll_materials.append(material)

        verts = make_bsp_jms_verts(bsp, node_transform)

        tri_count = 0
        # figure out how many triangles we'll be creating
        for mat_info in coll_edge_loops:
            for edge_loop in coll_edge_loops[mat_info]:
                tri_count += len(edge_loop) - 2

        tri_index = 0
        tris = [None] * tri_count
        # create triangles from the edge loops
        for mat_info in coll_edge_loops:
            mat_id = mat_info_to_mat_id[mat_info]
            for edge_loop in coll_edge_loops[mat_info]:
                loop_tris = edge_loop_to_tris(
                    edge_loop, mat_id=mat_id, make_fan=make_fans)
                tris[tri_index: tri_index + len(loop_tris)] = loop_tris
                tri_index += len(loop_tris)

        jms_models.append(
            JmsModel("bsp", 0, nodes, coll_materials, [],
                     ("collision_%s" % bsp_index, ), verts, tris))
        bsp_index += 1

    return jms_models


def sbsp_to_mod2(
        sbsp_path, include_lens_flares=True, include_markers=True,
        include_weather_polyhedra=True, include_fog_planes=True,
        include_portals=True, include_collision=True, include_renderable=True,
        include_mirrors=True, include_lightmaps=True, fan_weather_polyhedra=True,
        fan_fog_planes=True,  fan_portals=True, fan_collision=True,
        fan_mirrors=True, optimize_fog_planes=False, optimize_portals=False,):

    print("    Loading...")
    sbsp_tag = sbsp_def.build(filepath=sbsp_path)
    mod2_tag = mod2_def.build()

    sbsp_body = sbsp_tag.data.tagdata
    coll_mats = [JmsMaterial(mat.shader.filepath.split("\\")[-1])
                 for mat in sbsp_body.collision_materials.STEPTREE]

    base_nodes = [JmsNode("frame")]
    jms_models = []

    if include_markers:
        print("    Converting markers...")
        try:
            jms_models.append(make_marker_jms_model(
                sbsp_body.markers.STEPTREE, base_nodes))
        except Exception:
            print(format_exc())
            print("    Could not convert markers")

    if include_lens_flares:
        print("    Converting lens flares...")
        try:
            jms_models.append(make_lens_flare_jms_model(
                sbsp_body.lens_flare_markers.STEPTREE,
                sbsp_body.lens_flares.STEPTREE, base_nodes))
        except Exception:
            print(format_exc())
            print("    Could not convert lens flares")

    if include_fog_planes:
        print("    Converting fog planes...")
        try:
            jms_models.extend(make_fog_plane_jms_models(
                sbsp_body.fog_planes.STEPTREE, base_nodes,
                fan_fog_planes, optimize_fog_planes))
        except Exception:
            print(format_exc())
            print("    Could not convert fog planes")

    if include_mirrors:
        print("    Converting mirrors...")
        try:
            jms_models.extend(make_mirror_jms_models(
                sbsp_body.clusters.STEPTREE, base_nodes, fan_mirrors))
        except Exception:
            print(format_exc())
            print("    Could not convert mirrors")

    if include_portals:
        print("    Converting portals...")
        try:
            jms_models.extend(make_cluster_portal_jms_models(
                sbsp_body.collision_bsp.STEPTREE[0].planes.STEPTREE,
                sbsp_body.clusters.STEPTREE, sbsp_body.cluster_portals.STEPTREE,
                base_nodes, fan_portals, optimize_portals))
        except Exception:
            print(format_exc())
            print("    Could not convert portals")

    if include_weather_polyhedra:
        print("    Converting weather polyhedra...")
        try:
            jms_models.extend(make_weather_polyhedra_jms_models(
                sbsp_body.weather_polyhedras.STEPTREE, base_nodes,
                fan_weather_polyhedra))
        except Exception:
            print(format_exc())
            print("    Could not convert weather polyhedra")

    if include_collision:
        print("    Converting collision...")
        try:
            jms_models.extend(make_bsp_coll_jms_models(
                sbsp_body.collision_bsp.STEPTREE, coll_mats, base_nodes,
                None, False, fan_collision))
        except Exception:
            print(format_exc())
            print("    Could not convert collision")

    if include_renderable:
        print("    Converting renderable...")
        try:
            pass
        except Exception:
            print(format_exc())
            print("    Could not convert renderable")

    if include_lightmaps:
        print("    Converting lightmaps...")
        try:
            pass
        except Exception:
            print(format_exc())
            print("    Could not convert lightmaps")

    print("    Compiling gbxmodel...")
    mod2_tag.filepath = splitext(sbsp_path)[0] + "_SBSP.gbxmodel"
    compile_gbxmodel(mod2_tag, MergedJmsModel(*jms_models), True)
    return mod2_tag


class SbspToMod2Convertor(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.title("Structure bsp to gbxmodel convertor v1.0")
        self.resizable(0, 0)

        self.tags_dir = StringVar(self)
        self.tag_path = StringVar(self)

        self.include_weather_polyhedra = IntVar(self, 1)
        self.include_fog_planes = IntVar(self, 1)
        self.include_portals = IntVar(self, 1)
        self.include_collision = IntVar(self, 1)
        self.include_renderable = IntVar(self, 1)
        self.include_mirrors = IntVar(self, 0)
        self.include_lightmaps = IntVar(self, 0)

        self.include_markers = IntVar(self, 1)
        self.include_lens_flares = IntVar(self, 0)

        self.fan_portals = IntVar(self, 1)
        self.fan_weather_polyhedra = IntVar(self, 1)
        self.fan_fog_planes = IntVar(self, 1)
        self.fan_mirrors = IntVar(self, 1)
        self.fan_collision = IntVar(self, 1)

        self.optimize_portals = IntVar(self, 0)
        self.optimize_fog_planes = IntVar(self, 0)

        # make the frames
        self.tags_dir_frame = LabelFrame(self, text="Directory of tags")
        self.tag_path_frame = LabelFrame(self, text="Single tag")
        self.important_frame = LabelFrame(self, text="Important geometry/markers to include")
        self.additional_frame = LabelFrame(self, text="Additional geometry/markers to include")
        self.topology_frame = LabelFrame(self, text="Topology generation")


        # Generate the important frame and its contents
        include_vars = {
            "Weather polyhedra": self.include_weather_polyhedra,
            "Fog planes": self.include_fog_planes, "Portals": self.include_portals,
            "Collidable": self.include_collision, "Renderable": self.include_renderable,
            "Mirrors": self.include_mirrors, "Lightmaps": self.include_lightmaps,
            "Markers": self.include_markers, "Lens flares": self.include_lens_flares}
        important_buttons = []

        for text in ("Collidable", "Portals",# "Renderable",
                     "Weather polyhedra", "Fog planes", "Markers"):
            important_buttons.append(Checkbutton(
                self.important_frame, variable=include_vars[text], text=text))


        # Generate the additional frame and its contents
        additional_buttons = []
        for text in ("Lens flares", "Mirrors", ):#"Lightmaps"):
            additional_buttons.append(Checkbutton(
                self.additional_frame, variable=include_vars[text], text=text))


        # Generate the topology frame and its contents
        topology_vars = {
            "Weather polyhedra": self.fan_weather_polyhedra,
            "Fog planes": self.fan_fog_planes, "Mirrors": self.fan_mirrors,
            "Portals": self.fan_portals, "Collision": self.fan_collision}
        topology_frames = []
        topology_labels = []
        topology_buttons = []
        for text in ("Portals", "Fog planes", "Weather polyhedra", "Mirrors", "Collision"):
            var = topology_vars[text]
            f = Frame(self.topology_frame)
            name_lbl = Label(f, text=text, width=15, anchor="w")
            fan_cbtn = Checkbutton(
                f, variable=var, text="Tri-fan")
            strip_cbtn = Checkbutton(
                f, variable=var, text="Tri-strip", onvalue=0, offvalue=1)
            topology_frames.append(f)
            topology_labels.append(name_lbl)
            topology_buttons.extend((fan_cbtn, strip_cbtn))
            if text == "Portals":
                topology_buttons.append(Checkbutton(
                    f, variable=self.optimize_portals, text="Optimize"))
            elif text == "Fog planes":
                topology_buttons.append(Checkbutton(
                    f, variable=self.optimize_fog_planes, text="Optimize"))


        # add the filepath boxes
        self.tags_dir_entry = Entry(
            self.tags_dir_frame, textvariable=self.tags_dir)
        self.tags_dir_entry.config(width=55, state=DISABLED)
        self.tag_path_entry = Entry(
            self.tag_path_frame, textvariable=self.tag_path)
        self.tag_path_entry.config(width=55, state=DISABLED)

        # add the buttons
        self.convert_dir_btn = Button(
            self, text="Convert directory",
            width=15, command=self.convert_dir)
        self.convert_file_btn = Button(
            self, text="Convert tag", width=15,
            command=self.convert_bsp)
        self.tags_dir_browse_btn = Button(
            self.tags_dir_frame, text="Browse",
            width=6, command=self.tags_dir_browse)
        self.tag_path_browse_btn = Button(
            self.tag_path_frame, text="Browse",
            width=6, command=self.tag_path_browse)

        # pack everything
        self.tags_dir_entry.pack(expand=True, fill='x', side='left')
        self.tags_dir_browse_btn.pack(fill='x', side='left')

        self.tag_path_entry.pack(expand=True, fill='x', side='left')
        self.tag_path_browse_btn.pack(fill='x', side='left')

        for frame in topology_frames:
            frame.pack(expand=True, fill='both')

        for label in topology_labels:
            label.pack(anchor='w', padx=10, side='left')

        for button_list in (important_buttons, additional_buttons):
            x = y = 0
            for button in button_list:
                button.grid(row=y, column=x, padx=5, pady=5, sticky="w")
                x += 1
                if x == 3:
                    x = 0
                    y += 1

        for button in topology_buttons:
            button.pack(anchor='w', padx=5, side='left')

        self.tags_dir_frame.pack(expand=True, fill='both')
        self.convert_dir_btn.pack(fill='both', padx=5, pady=5)
        self.tag_path_frame.pack(expand=True, fill='both')
        self.convert_file_btn.pack(fill='both', padx=5, pady=5)

        self.important_frame.pack(expand=True, fill='both')
        self.additional_frame.pack(expand=True, fill='both')
        self.topology_frame.pack(expand=True, fill='both')

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

    def tag_path_browse(self):
        initialdir = self.tag_path.get()
        if not initialdir:
            initialdir = self.tags_dir.get()

        tag_path = askopenfilename(initialdir=initialdir)
        if tag_path:
            self.tag_path.set(tag_path)

    def convert_bsp(self, bsp_path=None):
        start = time()
        if bsp_path is None:
            bsp_path = self.tag_path.get()

        if not isfile(bsp_path):
            return

        print(bsp_path)

        try:
            mod2_tag = sbsp_to_mod2(
                bsp_path, self.include_lens_flares.get(),
                self.include_markers.get(), self.include_weather_polyhedra.get(),
                self.include_fog_planes.get(), self.include_portals.get(),
                self.include_collision.get(), self.include_renderable.get(),
                self.include_mirrors.get(), self.include_lightmaps.get(),
                self.fan_weather_polyhedra.get(), self.fan_fog_planes.get(),
                self.fan_portals.get(), self.fan_collision.get(), self.fan_mirrors.get(),
                self.optimize_fog_planes.get(), self.optimize_portals.get())
            if mod2_tag:
                print("    Saving to %s" % mod2_tag.filepath)
                mod2_tag.serialize(
                    temp=False, backup=False, int_test=False)
        except Exception:
            print(format_exc())

        print('    Finished. Took %s seconds.\n' % round(time() - start, 1))

    def convert_dir(self):
        start = time()
        tags_dir = join(self.tags_dir.get(), "")
        for root, dirs, files in os.walk(tags_dir):
            root = join(root, "")

            for filename in files:
                filepath = root + filename
                if os.path.splitext(filename)[-1].lower() != (
                    '.scenario_structure_bsp'):
                    continue

                self.convert_bsp(filepath)

        print('Finished. Took %s seconds.\n' % round(time() - start, 1))

try:
    converter = SbspToMod2Convertor()
    converter.mainloop()
except Exception:
    print(format_exc())
    input()
