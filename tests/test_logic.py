"""Standalone self-check (no Blender needed).

Stubs `bpy` so export_core imports, then asserts the name-suffix logic.
Run:  python tests/test_logic.py
"""
import sys
import types
import os

# Stub the bpy module so `import export_core` works outside Blender.
bpy = types.ModuleType("bpy")
bpy.path = types.SimpleNamespace(abspath=lambda p: p)
sys.modules["bpy"] = bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from export_core import strip_dup_suffix  # noqa: E402


def test_strip():
    assert strip_dup_suffix("SM_Wall.001") == "SM_Wall"
    assert strip_dup_suffix("SM_Wall.042") == "SM_Wall"
    assert strip_dup_suffix("SM_Wall") == "SM_Wall"
    # A dotted name that is NOT a numeric dup suffix must survive.
    assert strip_dup_suffix("Rock.LOD0") == "Rock.LOD0"
    assert strip_dup_suffix("v1.5_thing") == "v1.5_thing"
    print("OK strip_dup_suffix")


if __name__ == "__main__":
    test_strip()
    print("All checks passed.")
