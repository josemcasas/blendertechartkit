import os
import bpy


def strip_dup_suffix(name):
    """SM_Wall.001 -> SM_Wall. Blender appends .NNN to duplicate names;
    UE would import that literally, so we drop it on export."""
    base = name.rsplit('.', 1)
    if len(base) == 2 and base[1].isdigit():
        return base[0]
    return name


def _resolve_filepath(settings, obj_name):
    name = settings.export_name.strip() or strip_dup_suffix(obj_name)
    if settings.strip_suffix:
        name = strip_dup_suffix(name)
    folder = bpy.path.abspath(settings.export_path)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, name + ".fbx")


def export_selection(context, operator=None):
    """Non-destructive FBX export of the current mesh selection.

    Works on temporary duplicates so the user's scene is never mutated.
    Returns the written filepath, or None on failure.
    """
    settings = context.scene.takit_export
    sources = [o for o in context.selected_objects if o.type == 'MESH']

    if not sources:
        if operator:
            operator.report({'ERROR'}, "No mesh objects selected")
        return None

    # 1. Duplicate sources (object + data) into the active collection.
    coll = context.collection
    dups = []
    for src in sources:
        dup = src.copy()
        dup.data = src.data.copy()
        coll.objects.link(dup)
        dups.append(dup)

    bpy.ops.object.select_all(action='DESELECT')
    for d in dups:
        d.select_set(True)
    context.view_layer.objects.active = dups[0]

    # 2. Apply modifiers on the copies.
    if settings.export_apply_modifiers:
        for d in dups:
            context.view_layer.objects.active = d
            for mod in list(d.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except RuntimeError as e:
                    print(f"[TechArtKit] modifier {mod.name} on {d.name}: {e}")

    # 3. Optionally join into a single mesh.
    if settings.join_objects and len(dups) > 1:
        bpy.ops.object.select_all(action='DESELECT')
        for d in dups:
            d.select_set(True)
        context.view_layer.objects.active = dups[0]
        bpy.ops.object.join()
        dups = [context.active_object]

    # 4. Recenter.
    if settings.move_to_origin:
        for d in dups:
            context.view_layer.objects.active = d
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
            d.location = (0.0, 0.0, 0.0)

    # 5. Name / path from the first (or only) object.
    if settings.strip_suffix:
        for d in dups:
            d.name = strip_dup_suffix(d.name)
    filepath = _resolve_filepath(settings, dups[0].name)

    # 6. Export.
    bpy.ops.object.select_all(action='DESELECT')
    for d in dups:
        d.select_set(True)
    context.view_layer.objects.active = dups[0]

    # ponytail: cm export = scale meters-scene by 100; good enough for UE import.
    global_scale = settings.export_scale * (100.0 if settings.export_units == 'CENTIMETERS' else 1.0)

    bpy.ops.export_scene.fbx(
        filepath=filepath,
        check_existing=False,
        use_selection=True,
        object_types={'MESH'},
        global_scale=global_scale,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE',
        axis_up=settings.export_coord_up,
        axis_forward=settings.export_coord_forward,
        mesh_smooth_type=settings.export_smoothing,
        use_mesh_modifiers=settings.export_apply_modifiers,
        add_leaf_bones=False,
        bake_anim=False,
    )

    # 7. Clean up the temporary duplicates.
    bpy.ops.object.select_all(action='DESELECT')
    for d in dups:
        d.select_set(True)
    bpy.ops.object.delete()

    # Restore original selection.
    for o in sources:
        o.select_set(True)

    return filepath
