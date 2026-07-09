# -*- coding:utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# <pep8 compliant>

import bpy
import bmesh
import gpu

from gpu_extras.batch import batch_for_shader

from .core import *
from ..prefs import get_prefs

class MeshCheckObject:

    MESH_DATAS = ('verts', 'edges', 'faces')
    GEO_CHECKER = ('non_manifold', 'triangles', 'ngons')
    VERTS_CHECKER = ('n_poles', 'e_poles', 'more_poles', 'isolated_verts')

    def __init__(self, obj):

        self._object = obj
        self._bm_object = None

        self._verts = 0
        self._edges = 0
        self._faces = 0
        self._tris = 0

        self._triangles = Triangles(self)
        self._ngons = Ngons(self)
        self._non_manifold = NonManifold(self)

        self._poles = Poles(self)

        self._init_object()

    def _init_object(self):
        bm = self.set_bm_object()
        self.update_datas(bm)

    def set_bm_object(self):
        me = self._object.data
        if me.is_editmode:
            self._bm_object = bmesh.from_edit_mesh(me)
        else:
            bm = bmesh.new()
            bm.from_mesh(me)
            self._bm_object = bm
        return self._bm_object

    def update_datas(self, bm):
        for data in self.MESH_DATAS:
            setattr(self, f"_{data}", len(getattr(bm, data)))
            self._tris = len(bm.calc_loop_triangles())

        mesh_check = bpy.context.window_manager.mesh_check_props
        for check in self.GEO_CHECKER:
            if getattr(mesh_check, check):
                exec(f"self._{check}.set_datas()")

        if any(getattr(mesh_check, check) for check in self.VERTS_CHECKER):
            self._poles.set_datas()

    @property
    def bm_object(self):
        if self._bm_object is None or not self._bm_object.is_valid:
            self.update_bm_object()
        return self._bm_object

    def update_bm_object(self):
        bm = self.set_bm_object()
        self.update_datas(bm)
        return bm

    def is_updated_datas(self, bm):
        return any([getattr(self, f"_{data}") != len(getattr(bm, data))
                    for data in self.MESH_DATAS])


class MeshCheckGPU:

    _handler = None

    @staticmethod
    def shader():
        if bpy.app.version >= (4, 0, 0):
            return gpu.shader.from_builtin('UNIFORM_COLOR')

        return gpu.shader.from_builtin('3D_UNIFORM_COLOR')

    @classmethod
    def setup_handler(cls):
        cls._handler = bpy.types.SpaceView3D.draw_handler_add(
                cls.draw, (), 'WINDOW', 'POST_VIEW'
                )

    @classmethod
    def remove_handler(cls):
        bpy.types.SpaceView3D.draw_handler_remove(cls._handler, 'WINDOW')

    @classmethod
    def draw_edges(cls, coords, edges_width, color):
        shader = cls.shader()
        batch = batch_for_shader(shader, 'LINES', {"pos": coords})
        shader.bind()
        shader.uniform_float("color", color)
        gpu.state.blend_set("ALPHA")
        gpu.state.line_width_set(edges_width)
        batch.draw(shader)

    @classmethod
    def draw_faces(cls, coords, indices, color):
        shader = cls.shader()
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords},
                                 indices=indices)
        shader.bind()
        shader.uniform_float("color", color)
        gpu.state.blend_set("ALPHA")
        batch.draw(shader)
    @classmethod
    def draw_points(cls, coords, point_size, color):
        shader = cls.shader()
        batch = batch_for_shader(shader, 'POINTS', {"pos": coords})
        shader.bind()
        shader.uniform_float("color", color)
        gpu.state.point_size_set(point_size)
        batch.draw(shader)

    @staticmethod
    def remap_color(addon_prefs, check, type_):
        color = getattr(addon_prefs, f"{check}_color")
        alpha = getattr(addon_prefs, f"{type_}_alpha")
        return (*color, alpha)

    @classmethod
    def draw(cls):
        context = bpy.context
        if context.object is not None:
            if not bpy.context.space_data.shading.show_xray:
                gpu.state.depth_test_set('LESS')

            mesh_check = context.window_manager.mesh_check_props
            addon_prefs = get_prefs()

            for check in mesh_check.checker_options:
                if getattr(mesh_check, check):
                    for mc_object in MeshCheck.objects.values():
                        if check in ('non_manifold', 'triangles', 'ngons'):
                            faces_offset = getattr(addon_prefs, 'faces_offset')
                            coords = getattr(mc_object,
                                             f"_{check}").get_edges(faces_offset)

                            MeshCheckGPU.draw_edges(
                                    coords,
                                    addon_prefs.edges_width,
                                    cls.remap_color(addon_prefs, check,
                                                    'edges')
                                    )

                        if check in ('triangles', 'ngons'):
                            face_offset = getattr(addon_prefs, 'faces_offset')
                            coords, indices = getattr(mc_object,
                                             f"_{check}").get_faces(face_offset)
                            MeshCheckGPU.draw_faces(
                                    coords,
                                    indices,
                                    cls.remap_color(addon_prefs, check,
                                                    'faces')
                                    )

                        if check in ('n_poles', 'e_poles', 'more_poles',
                                     'isolated_verts'):
                            point_offset = getattr(addon_prefs,
                                                   'points_offset')
                            coords = mc_object._poles.get_poles(
                                    point_offset,
                                    check
                                    )

                            MeshCheckGPU.draw_points(
                                    coords,
                                    addon_prefs.point_size,
                                    getattr(addon_prefs, f"{check}_color")
                                    )

            gpu.state.depth_test_set('NONE')


class MeshCheck:

    _mode = ""
    objects = {}

    @staticmethod
    def poll():
        mesh_check = bpy.context.window_manager.mesh_check_props
        props = ("non_manifold", "triangles", "ngons",
                 "n_poles", "e_poles", "more_poles", "isolated_verts")
        return mesh_check.check_data and \
               any([getattr(mesh_check, prop) for prop in props])

    @classmethod
    def reset_mesh_check(cls):
        cls.set_mode("")
        for mc_object in cls.objects.values():
            del mc_object
        cls.objects.clear()

    @classmethod
    def mode(cls):
        return cls._mode

    @classmethod
    def set_mode(cls, states):
        cls._mode = states

    @classmethod
    def add_mesh_check_object(cls):
        for obj in bpy.context.selected_objects:
            if obj.type != "MESH" or cls.objects.get(obj):
                continue
            cls.objects[obj] = MeshCheckObject(obj)

    @classmethod
    def remove_mesh_check_object(cls, obj):
        mc_object = cls.objects.get(obj)
        if mc_object:
            del mc_object
            del cls.objects[obj]

    @classmethod
    def reset_mc_objects(cls):
        for mc_object in cls.objects.values():
            del mc_object
        cls.objects.clear()
        cls.add_mesh_check_object()

    @classmethod
    def add_callback(cls):
        if cls.callback not in bpy.app.handlers.depsgraph_update_post:
            cls.add_mesh_check_object()
            bpy.app.handlers.depsgraph_update_post.append(cls.callback)

    @classmethod
    def remove_callback(cls):
        if cls.callback in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(cls.callback)
            cls.reset_mesh_check()

    @classmethod
    def update_mc_object_datas(cls, checker_type):
        """
        :param checker_type: string,
        :return:
        """
        if checker_type in {'e_poles', 'n_poles', 'more_poles',
                            'isolated_verts'}:
            for mc_object in cls.objects.values():
                mc_object._poles.set_datas()

        else:
            for mc_object in cls.objects.values():
                getattr(mc_object, f"_{checker_type}").set_datas()

    @staticmethod
    def callback(scene):
        """
        Before doing anything, we check that the mode haven't changed.
        If this is the case and we are in EDIT mode, we check the validity
        of registered MeshCheckObject instances. For each instance,
        we update its bmesh representation.
        """
        if bpy.context.object is not None:
            object_mode = bpy.context.object.mode
            if object_mode != MeshCheck.mode():
                MeshCheck.set_mode(object_mode)
                MeshCheck.reset_mc_objects()

            if object_mode == "OBJECT":
                for obj in bpy.context.selected_objects:
                    if not MeshCheck.objects.get(obj):
                        MeshCheck.add_mesh_check_object()

                mc_objects = list(MeshCheck.objects.keys())
                for obj in mc_objects:
                    if obj not in list(bpy.data.objects) or not obj.select_get():
                        MeshCheck.remove_mesh_check_object(obj)

            if object_mode == "EDIT" and  MeshCheck.poll():
                depsgraph = bpy.context.evaluated_depsgraph_get()
                for obj, mc_object in MeshCheck.objects.items():
                    bm = mc_object.bm_object
                    for update in depsgraph.updates:
                        if update.id.original == obj and \
                                mc_object.is_updated_datas(bm):
                            mc_object.update_datas(bm)

        else:
            mesh_check = bpy.context.window_manager.mesh_check_props
            mesh_check.check_data = False
