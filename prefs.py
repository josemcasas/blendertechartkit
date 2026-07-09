import bpy
import sys

from bpy.types import AddonPreferences
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, IntProperty

# In a Blender 4.2+ extension the add-on key equals this package's dotted id
# (e.g. "bl_ext.user_default.blendertechartkit"). __package__ resolves to it
# from any submodule that imports get_prefs(), so every lookup goes through here
# instead of the old, extension-incompatible __name__.split('.')[0] trick.
ADDON_ID = __package__


def get_prefs():
    return bpy.context.preferences.addons[ADDON_ID].preferences


BACKEND_ITEMS = (('CPP', 'C++ (Fast)', ''), ('PY', 'Python (Slow)', ''))


def _color(name, default):
    return FloatVectorProperty(name=name, subtype='COLOR', size=3,
                               min=0.0, max=1.0, default=default)


class TechArtKitPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    tabs: EnumProperty(
        name="Prefs Tabs",
        items=[('MESHCHECK', 'Mesh Check', ""),
               ('TEXELDENSITY', 'Texel Density', "")],
        default='MESHCHECK',
    )

    # --- Texel Density ---
    calculation_backend: EnumProperty(name="", items=BACKEND_ITEMS, default='CPP')

    # --- Mesh Check overlay (colors + draw offsets the overlay reads) ---
    non_manifold_color: _color("Non manifold", (1.0, 0.0, 0.0))
    triangles_color: _color("Triangles", (0.0, 1.0, 1.0))
    ngons_color: _color("Ngons", (1.0, 0.5, 0.0))
    e_poles_color: _color("E poles", (1.0, 1.0, 0.0))
    n_poles_color: _color("N poles", (0.0, 1.0, 0.0))
    more_poles_color: _color("Poles > 5", (1.0, 0.0, 1.0))
    isolated_verts_color: _color("Isolated verts", (1.0, 1.0, 1.0))

    edges_alpha: FloatProperty(name="Edges alpha", min=0.0, max=1.0, default=1.0)
    faces_alpha: FloatProperty(name="Faces alpha", min=0.0, max=1.0, default=0.4)

    faces_offset: FloatProperty(name="Faces offset", min=0.0, default=0.1)
    points_offset: FloatProperty(name="Points offset", min=0.0, default=0.1)

    edges_width: IntProperty(name="Edges width", min=1, max=10, default=2)
    point_size: IntProperty(name="Point size", min=1, max=20, default=6)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'tabs', expand=True)

        if self.tabs == 'TEXELDENSITY':
            box = layout.box()
            row = box.row(align=True)
            row.label(text='Calculation Backend:')
            if sys.platform.startswith("darwin"):
                self.calculation_backend = 'PY'
                row.label(text='Native backend not available on macOS.', icon='INFO')
            else:
                row.prop(self, 'calculation_backend', expand=False)

        elif self.tabs == 'MESHCHECK':
            box = layout.box()
            box.label(text="Overlay Colors", icon='COLOR')
            flow = box.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
            for name in ("non_manifold", "triangles", "ngons",
                         "n_poles", "e_poles", "more_poles", "isolated_verts"):
                flow.prop(self, f"{name}_color")

            box = layout.box()
            box.label(text="Draw Settings", icon='OPTIONS')
            col = box.column(align=True)
            col.use_property_split = True
            row = col.row(align=True)
            row.prop(self, "edges_alpha")
            row.prop(self, "faces_alpha")
            row = col.row(align=True)
            row.prop(self, "faces_offset")
            row.prop(self, "points_offset")
            row = col.row(align=True)
            row.prop(self, "edges_width")
            row.prop(self, "point_size")


def register():
    bpy.utils.register_class(TechArtKitPreferences)


def unregister():
    bpy.utils.unregister_class(TechArtKitPreferences)
