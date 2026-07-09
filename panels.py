import bpy

from .prefs import get_prefs


class _View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TechArt Kit"


class TAKIT_PT_exporter(_View3DPanel, bpy.types.Panel):
    bl_idname = "TAKIT_PT_exporter"
    bl_label = "FBX Exporter"

    def draw(self, context):
        s = context.scene.takit_export
        layout = self.layout
        layout.use_property_decorate = False

        # --- Destination ---
        col = layout.column(align=True)
        col.prop(s, 'export_path', text="", icon='FILE_FOLDER')
        row = col.row(align=True)
        row.prop(s, 'export_name', text="", icon='FILE_NEW')
        row.operator('export_scene.takit_open_folder', text="", icon='VIEWZOOM')

        # --- Big action ---
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator('export_scene.takit_export', text="Export Selected", icon='EXPORT')


class TAKIT_PT_exporter_transform(_View3DPanel, bpy.types.Panel):
    bl_parent_id = "TAKIT_PT_exporter"
    bl_label = "Transform"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        s = context.scene.takit_export
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(s, 'export_coord_up')
        col.prop(s, 'export_coord_forward')
        col.separator()
        col.prop(s, 'export_scale')
        col.prop(s, 'export_units')
        col.prop(s, 'export_smoothing')


class TAKIT_PT_exporter_process(_View3DPanel, bpy.types.Panel):
    bl_parent_id = "TAKIT_PT_exporter"
    bl_label = "Processing"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        s = context.scene.takit_export
        col = self.layout.column(align=True)
        col.prop(s, 'export_apply_modifiers', icon='MODIFIER')
        col.prop(s, 'join_objects', icon='SNAP_VERTEX')
        col.prop(s, 'move_to_origin', icon='OBJECT_ORIGIN')
        col.prop(s, 'strip_suffix', icon='SORTALPHA')


class TAKIT_PT_mesh_check(_View3DPanel, bpy.types.Panel):
    bl_label = "Mesh Check"

    def draw(self, context):
        mc = context.window_manager.mesh_check_props
        prefs = get_prefs()
        layout = self.layout

        row = layout.row(align=True)
        row.prop(mc, 'check_data', text="Live Check",
                 icon='CHECKMARK' if mc.check_data else 'MESH_DATA', toggle=True)
        row.prop(mc, 'show_overlay', text="Overlay",
                 icon='OVERLAY', toggle=True)

        active = mc.check_data or mc.show_overlay

        def check_row(parent, key, color_prop):
            r = parent.row(align=True)
            r.active = active
            r.prop(mc, key)
            r.prop(prefs, color_prop, text="")

        box = layout.box()
        box.label(text="Geometry", icon='MESH_ICOSPHERE')
        col = box.column(align=True)
        check_row(col, 'non_manifold', 'non_manifold_color')
        check_row(col, 'triangles', 'triangles_color')
        check_row(col, 'ngons', 'ngons_color')

        box = layout.box()
        box.label(text="Vertices", icon='DOT')
        col = box.column(align=True)
        check_row(col, 'n_poles', 'n_poles_color')
        check_row(col, 'e_poles', 'e_poles_color')
        check_row(col, 'more_poles', 'more_poles_color')
        check_row(col, 'isolated_verts', 'isolated_verts_color')


class TAKIT_PT_texel_density(_View3DPanel, bpy.types.Panel):
    bl_label = "Texel Density"

    def draw(self, context):
        td = context.scene.takit_td
        layout = self.layout

        obj = context.active_object
        if not obj or obj.type != 'MESH':
            layout.label(text="Select a mesh object", icon='INFO')
            return

        col = layout.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(td, 'units', text="Units")
        col.prop(td, 'texture_size', text="Texture")
        if td.texture_size == 'CUSTOM':
            row = col.row(align=True)
            row.prop(td, 'custom_width', text="W")
            row.prop(td, 'custom_height', text="H")
        col.prop(td, 'selected_faces')

        units_label = {'0': "px/cm", '1': "px/m", '2': "px/in", '3': "px/ft"}[td.units]
        box = layout.box()
        split = box.split(factor=0.4)
        left = split.column(align=True)
        right = split.column(align=True)
        left.label(text="UV Space:")
        left.label(text="Density:")
        right.label(text=td.uv_space)
        r = right.row()
        r.label(text=f"{td.density} {units_label}")

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("ign_texel_density.check", text="Calculate TD", icon='UV_DATA')


_classes = (
    TAKIT_PT_exporter,
    TAKIT_PT_exporter_transform,
    TAKIT_PT_exporter_process,
    TAKIT_PT_mesh_check,
    TAKIT_PT_texel_density,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
