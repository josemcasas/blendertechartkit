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


import bmesh

__all__ = ['Triangles', 'Ngons', 'NonManifold', 'Poles']


def _triangulate_polygon(bm, polygons_idx):
    bm_copy = bm.copy()

    bm_copy.faces.ensure_lookup_table()
    polygons = [bm_copy.faces[idx] for idx in polygons_idx]

    new_faces = bmesh.ops.triangulate(bm_copy, faces=polygons,
                                      quad_method="BEAUTY",
                                      ngon_method="BEAUTY")
    verts_idx = [vert.index for face in new_faces['faces'] for vert in
                 face.verts]
    bm_copy.free()
    del bm_copy
    bm.verts.ensure_lookup_table()
    verts = [bm.verts[idx] for idx in verts_idx]
    return verts


def _get_offset(offset, obj):
    scale = sum(obj.scale[:]) / 3
    return max(0.000001, offset) / 100 * scale


class MainGeo:
    def __init__(self, parent):
        self._parent = parent
        self._count = 0
        self._verts = []
        self._indices = []
        self._edges = []

    @property
    def count(self):
        return self._count

    def get_faces(self, offset):
        obj = self._parent._object
        wm = obj.matrix_world
        _offset = _get_offset(offset, obj)
        coords = tuple([
            ((wm @ vert.co)[0] + vert.normal.x * _offset,
             (wm @ vert.co)[1] + vert.normal.y * _offset,
             (wm @ vert.co)[2] + vert.normal.z * _offset)
            for vert in self._verts]
                )
        return coords, self._indices

    def get_edges(self, offset):
        obj = self._parent._object
        wm = obj.matrix_world
        _offset = _get_offset(offset, obj)
        coords = tuple([
            ((wm @ vert.co)[0] + vert.normal.x * _offset,
             (wm @ vert.co)[1] + vert.normal.y * _offset,
             (wm @ vert.co)[2] + vert.normal.z * _offset) for edge in
            self._edges for vert in edge.verts])
        return coords


class Triangles(MainGeo):
    def __init__(self, parent):
        MainGeo.__init__(self, parent)

    def set_datas(self):
        bm = self._parent.bm_object
        self._verts.clear()
        self._indices.clear()
        self._edges.clear()

        faces = [face for face in bm.faces if len(face.edges) == 3]
        self._count = len(faces)

        self._verts = [vert for face in faces for vert in face.verts]
        vert_count = len(self._verts)
        index = list(range(vert_count))
        self._indices = [index[i:i+3] for i in range(0, vert_count, 3)]
        self._edges = [edge for face in faces for edge in face.edges]


class Ngons(MainGeo):
    def __init__(self, parent):
        MainGeo.__init__(self, parent)

    def set_datas(self):
        bm = self._parent.bm_object
        self._verts.clear()
        self._indices.clear()
        self._edges.clear()

        faces = [face for face in bm.faces if len(face.edges) > 4]
        self._count = len(faces)

        self._verts = _triangulate_polygon(bm, list(map(lambda face:
                                                        face.index, faces)))
        vert_count = len(self._verts)
        index = list(range(vert_count))
        self._indices = [index[i:i + 3] for i in range(0, vert_count, 3)]
        self._edges = [edge for face in faces for edge in face.edges]


class NonManifold:
    def __init__(self, parent):
        self._parent = parent
        self._edges = []

    @property
    def count(self):
        return len(self._edges)
    def set_datas(self):
        bm = self._parent.bm_object
        self._edges.clear()
        self._edges = [edge for edge in bm.edges if not edge.is_manifold]

    def get_edges(self, offset):
        obj = self._parent._object
        wm = obj.matrix_world
        coords = [wm @ vert.co for edge in self._edges for vert in edge.verts]
        return coords


class Poles:
    def __init__(self, parent):
        self._parent = parent
        self._e_poles = set()
        self._n_poles = set()
        self._more_poles = set()
        self._isolated_verts = set()

    def count(self, pole_type):
        return len(getattr(self, f"_{pole_type}"))

    def set_datas(self):
        bm = self._parent.bm_object
        checkers = ('n_poles', 'e_poles', 'more_poles', 'isolated_verts')
        for check in checkers:
            exec(f"self._{check}.clear()")

        for vert in bm.verts:
            pole_type = len(vert.link_edges)
            if pole_type == 0:
                self._isolated_verts.add(vert)
            if pole_type == 3:
                self._n_poles.add(vert)
            if pole_type == 5:
                self._e_poles.add(vert)
            if pole_type > 5:
                self._more_poles.add(vert)

    def get_poles(self, offset, pole_type):
        obj = self._parent._object
        wm = obj.matrix_world
        verts = getattr(self, f"_{pole_type}")
        _offset = _get_offset(offset, obj)
        coords = tuple([
            ((wm @ vert.co)[0] + vert.normal.x * _offset,
             (wm @ vert.co)[1] + vert.normal.y * _offset,
             (wm @ vert.co)[2] + vert.normal.z * _offset)
            for vert in verts]
                )

        return coords
