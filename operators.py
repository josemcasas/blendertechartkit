import os
import sys
import subprocess
from datetime import datetime

import bpy
import bmesh
import numpy as np

from . import export_core
from .prefs import get_prefs
from .texel_density import utils as td_utils
from .texel_density.cpp_interface import TDCoreWrapper


def show_message(message="", title="TechArt Kit", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


class TAKIT_OT_export_selection(bpy.types.Operator):
    bl_idname = 'export_scene.takit_export'
    bl_label = 'Export Selected (FBX)'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def execute(self, context):
        filepath = export_core.export_selection(context, operator=self)
        if not filepath:
            return {'CANCELLED'}
        self.report({'INFO'}, f"Exported: {filepath}")
        return {'FINISHED'}


class TAKIT_OT_open_export_folder(bpy.types.Operator):
    """Open the export folder in the OS file browser"""
    bl_idname = "export_scene.takit_open_folder"
    bl_label = "Open Export Folder"

    def execute(self, context):
        folder = bpy.path.abspath(context.scene.takit_export.export_path)
        os.makedirs(folder, exist_ok=True)
        try:
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except Exception as e:
            self.report({'ERROR'}, f"Could not open folder: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class TAKIT_OT_texel_density_check(bpy.types.Operator):
    """Calculate texel density for selected objects/faces"""
    bl_idname = "ign_texel_density.check"
    bl_label = "Calculate TD"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        td = context.scene.takit_td
        start_mode = context.object.mode
        start_active_obj = context.active_object
        need_select_again = list(context.selected_objects)
        start_selected = (context.objects_in_mode if start_mode == 'EDIT'
                          else context.selected_objects)

        tdcore_lib = TDCoreWrapper() if get_prefs().calculation_backend == 'CPP' else None

        bpy.ops.object.mode_set(mode='OBJECT')

        area = 0.0
        local_area_list, local_td_list = [], []
        bm = bmesh.new()

        for obj in start_selected:
            if obj.type != 'MESH' or len(obj.data.uv_layers) == 0 or len(obj.data.polygons) == 0:
                continue

            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = obj
            obj.select_set(True)

            mesh_data = obj.data
            face_count = len(mesh_data.polygons)

            if start_mode == 'OBJECT' or not td.selected_faces:
                selected_faces = np.arange(face_count, dtype=np.int32)
            elif context.area.spaces.active.type == "IMAGE_EDITOR" and not context.scene.tool_settings.use_uv_select_sync:
                bm.clear()
                bm.from_mesh(obj.data)
                bm.faces.ensure_lookup_table()
                uv_layer = bm.loops.layers.uv.active
                selected_faces = np.array(
                    [f.index for f in bm.faces
                     if f.select and all(loop[uv_layer].select for loop in f.loops)],
                    dtype=np.int32)
            else:
                selected_faces = np.array(
                    [p.index for p in mesh_data.polygons if p.select], dtype=np.int32)

            if selected_faces.size == 0:
                continue

            face_td_area = np.array(td_utils.calculate_td_area_to_list(tdcore_lib), dtype=np.float32)
            selected_areas = face_td_area[selected_faces, 1]
            selected_densities = face_td_area[selected_faces, 0]
            local_area = selected_areas.sum()

            if local_area == 0:
                local_texel_density = 0.0001
            else:
                weights = selected_areas / local_area
                local_texel_density = np.dot(selected_densities, weights)

            local_area_list.append(local_area)
            local_td_list.append(local_texel_density)
            area += local_area

        bm.free()

        if area > 0:
            local_area_np = np.array(local_area_list, dtype=np.float32)
            local_td_np = np.array(local_td_list, dtype=np.float32)
            texel_density = np.dot(local_td_np, local_area_np / area)
            td.uv_space = '%.4f' % round(area * 100, 4)
            td.density = '%.3f' % round(texel_density, 3)
        else:
            self.report({'INFO'}, "No faces selected or UV area is very small")
            td.uv_space = '0'
            td.density = '0'

        bpy.ops.object.select_all(action='DESELECT')
        for obj in need_select_again:
            obj.select_set(True)
        context.view_layer.objects.active = start_active_obj
        if start_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


_classes = (
    TAKIT_OT_export_selection,
    TAKIT_OT_open_export_folder,
    TAKIT_OT_texel_density_check,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
