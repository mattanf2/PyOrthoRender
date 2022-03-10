import enum
from collections import defaultdict
from typing import List, Iterable, Tuple, Dict
from itertools import chain

import numpy as np

from world_render.world_textures.texture_manager import WorldTextureManager, WorldTileIndex
from world_render.world_textures.utils import Corner

HAS_TEXTURE = 32
TileCondition = Dict[WorldTileIndex, int]


class TileBuffers:  # tile graphic buffers

    def __init__(self, tile: WorldTileIndex, aoi: np.ndarray):
        self.tile = tile
        self._vertices_lists = []
        self._vertices = None
        self._texcoords_lists = []
        self._texcoords = None
        self._indices_lists = []
        self._indices = None
        self._total_vertices = 0
        self._aoi = aoi

    def append_vertex_buffers(self, vertices, texcoords, indices):
        vertices = (vertices - self._aoi[0]) / (self._aoi[1] - self._aoi[0])
        indices += self._total_vertices
        self._total_vertices += len(vertices)
        self._vertices_lists.append(vertices)
        self._texcoords_lists.append(texcoords)
        self._indices_lists.append(indices)

    @property
    def vertices(self):
        if self._vertices_lists:
            if self._vertices:
                self._vertices_lists = [self._vertices] + self._vertices_lists
            self._vertices = np.concatenate(self._vertices_lists)
            self._vertices_lists = []
        return self._vertices

    @property
    def texcoords(self):
        if self._texcoords_lists:
            if self._texcoords:
                self._texcoords_lists = [self._texcoords] + self._texcoords_lists
            self._texcoords = np.concatenate(self._texcoords_lists)
            self._texcoords_lists = []
        return self._texcoords

    @property
    def indices(self):
        if self._indices_lists:
            if self._indices:
                self._indices_lists = [self._indices] + self._indices_lists
            self._indices = np.concatenate(self._indices_lists)
            self._indices_lists = []
        return self._indices

    def get_matplotlib_triangles(self, index):
        inds = self.indices
        verts = self.vertices
        from matplotlib.patches import Polygon
        colors = ['#ef000020', '#00ef0020',  '#0000ef20', '#00909000', '#90009000', '#90900000', '#44444420']
        for i in range(0, len(inds), 3):
            yield Polygon([verts[inds[i]], verts[inds[i + 1]], verts[inds[i + 2]], verts[inds[i]]], edgecolor='black', color=colors[index % len(colors)])


class TileGeometryBuilder:
    manager = WorldTextureManager()
    WorldTileIndex(manager, 3, 4, 3)

    def __init__(self):
        self._aoi_zoom_level: int = 0
        self._aoi_bounds: np.ndarray = None #np.array([[0,0],[0,0]])

    @property
    def aoi_zoom_level(self):
        if self._aoi_zoom_level == 0:
            raise ValueError("zoom level not initialized")
        return self._aoi_zoom_level

    @property
    def aoi_bounds(self):
        if self._aoi_bounds is None:
            raise ValueError("aoi bounds not initialized")
        return self._aoi_bounds

    @property
    def aoi_world_bounds(self):
        return self.aoi_bounds / self.aoi_zoom_level**2

    def tesselate_tiles(self, tiles: Iterable[WorldTileIndex]) -> Iterable[TileBuffers]:
        self._max_zoom_level = max((tile.zoom for tile in tiles)) + 1
        rendered_tiles_condition: TileCondition = defaultdict(lambda: 0)
        for tile in tiles:
            rendered_tiles_condition[tile] |= HAS_TEXTURE

            child_tile, tile = tile, tile.parent
            ancestor_updated = False
            while tile and not ancestor_updated:
                ancestor_updated = tile in rendered_tiles_condition
                rendered_tiles_condition[tile] |= self._get_relation_to_parent(child_tile)
                child_tile, tile = tile, tile.parent

        return self._generate_tile_buffers(tiles, rendered_tiles_condition)

    def _get_relation_to_parent(self, tile: WorldTileIndex):
        return (Corner.TR if tile.y % 2 else Corner.BR) \
            if tile.x % 2 else \
            (Corner.TL if tile.y % 2 else Corner.BL)

    def _generate_tile_buffers(self, textured_tiles: Iterable[WorldTileIndex], tiles_condition: TileCondition):
        textured_tiles = sorted(textured_tiles, key=lambda t: t.zoom)
        corner_vertices = self._get_tiles_corner_vertices(textured_tiles)
        np_verts = np.array(list(corner_vertices))
        self._aoi_bounds = np.vstack([np_verts.min(axis=0), np_verts.max(axis=0)])

        buffers = []
        for tile in textured_tiles:
            buffers.append(TileBuffers(tile, self.aoi_bounds))
            self._append_buffer_for_tile(buffers[-1], tile, tiles_condition, corner_vertices, 0)
        return buffers

    def _get_tiles_corner_vertices(self, tiles: Iterable[WorldTileIndex]):
        vertices = set()
        for tile in tiles:
            factor = 2 ** (self._max_zoom_level - tile.zoom)
            vertices.add(((tile.x + 0) * factor, (tile.y + 0) * factor))
            vertices.add(((tile.x + 1) * factor, (tile.y + 0) * factor))
            vertices.add(((tile.x + 0) * factor, (tile.y + 1) * factor))
            vertices.add(((tile.x + 1) * factor, (tile.y + 1) * factor))
        return vertices

    def _append_buffer_for_tile(self, buffer: TileBuffers, tile: WorldTileIndex,
                                tiles_condition: TileCondition, corner_vertices: List[Tuple[int, int]],
                                iteration: int):
        # Check if current tile as assgined to another textured tile
        if tile in tiles_condition and tiles_condition[tile] & HAS_TEXTURE and iteration != 0:
            return

        if tile in tiles_condition and tiles_condition[tile] & (Corner.TR | Corner.BR | Corner.TL | Corner.BL):
            for child_tile in tile.get_children():
                self._append_buffer_for_tile(buffer, child_tile, tiles_condition, corner_vertices, iteration + 1)
        else:
            self._add_vertexes_around_tile(buffer, tile, corner_vertices)

    def _add_vertexes_around_tile(self, buffer: TileBuffers, tile: WorldTileIndex,
                                  corners: List[Tuple[int, int]]):

        factor = 2 ** (self._max_zoom_level - tile.zoom)
        vertices = chain(
            [((2 * tile.x + 1) * factor / 2, (2 * tile.y + 1) * factor / 2)], # center position
            self._filter_vertices_x_aligned(corners, (tile.x + 0) * factor, (tile.y) * factor, (tile.y + 1) * factor),
            self._filter_vertices_y_aligned(corners, (tile.y + 1) * factor, (tile.x) * factor, (tile.x + 1) * factor),
            self._filter_vertices_x_aligned(corners, (tile.x + 1) * factor, (tile.y + 1) * factor, (tile.y) * factor),
            self._filter_vertices_y_aligned(corners, (tile.y + 0) * factor, (tile.x + 1) * factor, (tile.x) * factor))
        vertices = np.array(list(vertices), dtype=np.float32)
        texcoords = (vertices - (tile.x * factor, tile.y * factor)) / factor

        num_vertices = len(vertices)
        indices = np.arange(3, (num_vertices) * 3)
        indices[0::3] = 0
        indices[1::3] = indices[1::3] // 3
        indices[2::3] = indices[2::3] // 3 + 1
        indices[-1] = 1

        buffer.append_vertex_buffers(vertices, texcoords, indices)

    @staticmethod
    def _filter_vertices_x_aligned(vertices, x_value, from_y, to_y):
        min_y, max_y = min(from_y, to_y), max(from_y, to_y)
        arr = [(x_value, from_y)] + [vert for vert in vertices if vert[0] == x_value and min_y < vert[1] < max_y]
        return sorted(arr, key=lambda v: abs(v[1] - from_y))

    @staticmethod
    def _filter_vertices_y_aligned(vertices, y_value, from_x, to_x):
        min_x, max_x = min(from_x, to_x), max(from_x, to_x)
        arr = [(from_x, y_value)] + [vert for vert in vertices if vert[1] == y_value and min_x < vert[0] < max_x]
        return sorted(arr, key=lambda v: abs(v[0] - from_x))


def _example_tiles():
    global manager
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots()
    ax.autoscale(True)
    manager = WorldTextureManager()
    tiles = [WorldTileIndex(manager, 1, 2, 2), WorldTileIndex(manager, 3, 8, 9), WorldTileIndex(manager, 4, 18, 18)]
    builder = TileGeometryBuilder()
    buffers = builder.tesselate_tiles(tiles)
    for index, buffer in enumerate(buffers):
        for tri in buffer.get_matplotlib_triangles(index):
            ax.add_patch(tri)
    # display plot
    plt.show()


if __name__ == '__main__':
    _example_tiles()
    #_example_np_bezeir()

    #_example_tiles()

#https://nurbs-python.readthedocs.io/en/latest/module_fitting.html