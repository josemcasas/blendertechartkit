import os
import bpy

from bpy.props import (
    BoolProperty, EnumProperty, StringProperty, FloatProperty,
)
from bpy.types import PropertyGroup

from .mesh_check.overlay import MeshCheck, MeshCheckGPU


def _default_export_path():
    path = os.path.join(os.path.expanduser('~'), 'Documents', 'FBX_Exports')
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------
class TAKitExportSettings(PropertyGroup):
    export_path: StringProperty(
        name="Export folder", subtype='DIR_PATH', default=_default_export_path())
    export_name: StringProperty(
        name="Name", default="",
        description="File name (without extension). Empty = use the object name")

    export_scale: FloatProperty(
        name="Scale", default=1.0, min=0.001, max=1000.0,
        soft_min=0.01, soft_max=100.0)
    export_units: EnumProperty(
        name="Units",
        items=[("METERS", "m", ""), ("CENTIMETERS", "cm", "")],
        default="METERS")

    export_coord_up: EnumProperty(
        name="Up",
        items=[(a, a, "") for a in ("X", "Y", "Z", "-X", "-Y", "-Z")],
        default="Z")
    export_coord_forward: EnumProperty(
        name="Forward",
        items=[(a, a, "") for a in ("X", "Y", "Z", "-X", "-Y", "-Z")],
        default="-Y")

    export_smoothing: EnumProperty(
        name="Smoothing",
        items=[("OFF", "Normals only", ""), ("FACE", "Face", ""), ("EDGE", "Edge", "")],
        default="FACE")

    export_apply_modifiers: BoolProperty(name="Apply modifiers", default=True)
    join_objects: BoolProperty(
        name="Join selection", default=False,
        description="Combine the selected meshes into one before exporting")
    move_to_origin: BoolProperty(
        name="Move to origin", default=False,
        description="Recenter (origin to bounds) and move to world origin")
    strip_suffix: BoolProperty(
        name="Strip .001 suffix", default=True,
        description="Remove Blender's numeric duplicate suffix from exported names")


# ---------------------------------------------------------------------------
# Mesh Check (overlay lives on the WindowManager, matching overlay.py)
# ---------------------------------------------------------------------------
def _enable_depsgraph_handler(self, context):
    if self.check_data:
        if context.object is None:
            self.check_data = False
        else:
            MeshCheck.set_mode(context.object.mode)
            MeshCheck.add_callback()
    else:
        MeshCheck.remove_callback()


def _update_overlay(self, context):
    if self.show_overlay:
        MeshCheckGPU.setup_handler()
    else:
        MeshCheckGPU.remove_handler()


def _mc_updater(attr):
    def updater(self, context):
        if getattr(self, attr):
            MeshCheck.update_mc_object_datas(attr)
    return updater


class TAKitMeshCheckProps(PropertyGroup):
    check_data: BoolProperty(
        name="Check Data", default=False, update=_enable_depsgraph_handler)
    show_overlay: BoolProperty(
        name="Show Overlay", default=False, update=_update_overlay)

    non_manifold: BoolProperty(name="Non manifold", default=False,
                               update=_mc_updater("non_manifold"))
    triangles: BoolProperty(name="Triangles", default=True,
                            update=_mc_updater("triangles"))
    ngons: BoolProperty(name="Ngons", default=False, update=_mc_updater("ngons"))
    e_poles: BoolProperty(name="E poles", default=False, update=_mc_updater("e_poles"))
    n_poles: BoolProperty(name="N poles", default=False, update=_mc_updater("n_poles"))
    more_poles: BoolProperty(name="Poles > 5", default=False,
                             update=_mc_updater("more_poles"))
    isolated_verts: BoolProperty(name="Isolated verts", default=False,
                                 update=_mc_updater("isolated_verts"))

    checker_options = ("non_manifold", "triangles", "ngons",
                       "n_poles", "e_poles", "more_poles", "isolated_verts")


# ---------------------------------------------------------------------------
# Texel Density
# ---------------------------------------------------------------------------
TD_TEXTURE_SIZE_ITEMS = (('512', '512px', ''), ('1024', '1024px', ''),
                         ('2048', '2048px', ''), ('4096', '4096px', ''),
                         ('CUSTOM', 'Custom', ''))
TD_UNITS_ITEMS = (('0', 'px/cm', ''), ('1', 'px/m', ''),
                  ('2', 'px/in', ''), ('3', 'px/ft', ''))


def _td_recheck(self, context):
    if context.active_object and context.active_object.type == 'MESH':
        bpy.ops.ign_texel_density.check()


class TAKitTexelDensityProps(PropertyGroup):
    texture_size: EnumProperty(name="", items=TD_TEXTURE_SIZE_ITEMS,
                               default='1024', update=_td_recheck)
    custom_width: StringProperty(name="Width", default="1024")
    custom_height: StringProperty(name="Height", default="1024")
    units: EnumProperty(name="", items=TD_UNITS_ITEMS, default='0', update=_td_recheck)
    selected_faces: BoolProperty(name="Selected faces only", default=False)
    uv_space: StringProperty(name="", default="0 %")
    density: StringProperty(name="", default="0")


_classes = (
    TAKitExportSettings,
    TAKitMeshCheckProps,
    TAKitTexelDensityProps,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.takit_export = bpy.props.PointerProperty(type=TAKitExportSettings)
    bpy.types.WindowManager.mesh_check_props = bpy.props.PointerProperty(type=TAKitMeshCheckProps)
    bpy.types.Scene.takit_td = bpy.props.PointerProperty(type=TAKitTexelDensityProps)


def unregister():
    del bpy.types.Scene.takit_td
    del bpy.types.WindowManager.mesh_check_props
    del bpy.types.Scene.takit_export
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
