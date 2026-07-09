# Blender TechArt Kit

Standalone Blender 4.2+ extension extracted from the (cancelled) Ignite project's
Maya/Blender pipeline. **No Perforce, no credentials, no project structure.**

## Features
- **FBX Exporter** — export the current mesh selection to a folder you choose,
  UE-ready preset (axis, scale, smoothing), optional apply-modifiers / join /
  recenter, and automatic stripping of Blender's `.001` duplicate suffix.
  Works on temporary copies — your scene is never mutated.
- **Mesh Check** — real-time GPU overlay for non-manifold, triangles, ngons,
  N/E/>5 poles and isolated verts. (GPL, orig. Legigan Jeremy / Pistiwique.)
- **Texel Density** — px/cm·m·in·ft readout with a native C++ backend
  (`tdcore.dll` / `libtdcore.so`) and a pure-Python fallback.

## Install
Blender → Edit → Preferences → Get Extensions → Install from Disk → pick the
zipped folder (or point it at this directory). Panels appear in the 3D Viewport
sidebar (`N`) under the **TechArt Kit** tab. Colors/offsets for Mesh Check and
the TD backend live in the add-on preferences.

## Dev
`python tests/test_logic.py` runs the (Blender-free) name-suffix self-check.

## What was removed from the original Ignite addon
- Perforce integration (`import P4`, workspace gating, auto-update) — the whole
  UI used to be hidden unless a live P4 server validated.
- The Qt/PySide6 validation window (hundreds of MB of vendored PySide6) —
  the native Mesh Check overlay replaces it.
- The `export_fbx_bin.py` core-overwrite hack (2×189 KB, needed admin, broke on
  every Blender update). Its only real effect — dropping the `.001` suffix — is
  now done in `export_core.strip_dup_suffix`.
- Ignite asset taxonomy (Environment/category/subcategory) driven by the P4
  workspace path.
