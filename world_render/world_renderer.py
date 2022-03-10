from typing import Iterable

from world_render import assets
from world_render.geometrizer import TileGeometryBuilder, TileBuffers
from world_render.world_textures.texture_manager import WorldTextureManager, WorldTileIndex

import numpy as np
from ported._example import Example

class WorldRenderer(Example):

    gl_version = (3, 3)
    aspect_ratio = 16 / 9
    title = "Map Geometry painter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._texture_manager = WorldTextureManager()
        self._tile_builder = TileGeometryBuilder()

        self.render_sample()


    def render_sample(self):
        tiles = [WorldTileIndex(self._texture_manager, 1, 2, 2),
                 WorldTileIndex(self._texture_manager, 3, 8, 9),
                 WorldTileIndex(self._texture_manager, 4, 18, 18)]
        buffers = self._tile_builder.tesselate_tiles(tiles)
        self._render_buffers(buffers)

    def _render_buffers(self, buffers: Iterable[TileBuffers]):
        self.prog = self.ctx.program(
            vertex_shader=assets.VERTEX_SHADER,
            fragment_shader=assets.FRAGMENT_SHADER,
        )

        for buffer in buffers:
            buffer.vertices
        # Point coordinates are put followed by the vec3 color values
        vertices = np.array([
            # x, y, red, green, blue
            0.0, 0.8, 1.0, 0.0, 0.0,
            -0.6, -0.8, 0.0, 1.0, 0.0,
            0.6, -0.8, 0.0, 0.0, 1.0,
        ], dtype='f4')

        self.vbo = self.ctx.buffer(vertices)

        # We control the 'in_vert' and `in_color' variables
        self.vao = self.ctx.vertex_array(
            self.prog,
            [
                # Map in_vert to the first 2 floats
                # Map in_color to the next 3 floats
                (self.vbo, '2f 3f', 'in_vert', 'in_color')
            ],
        )

    def render(self, time: float, frame_time: float):
        self.ctx.clear(1.0, 1.0, 1.0)
        self.vao.render()

if __name__ == '__main__':
    wr = WorldRenderer()
    wr.render_sample()





import numpy as np

from ported._example import Example


class SimpleColorTriangle(Example):
    gl_version = (3, 3)
    aspect_ratio = 16 / 9
    title = "Simple Color Triangle"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prog = self.ctx.program(
            vertex_shader=assets.VERTEX_SHADER,
            fragment_shader=assets.FRAGMENT_SHADER,
        )

        # Point coordinates are put followed by the vec3 color values
        vertices = np.array([
            # x, y, red, green, blue
            0.0, 0.8, 1.0, 0.0, 0.0,
            -0.6, -0.8, 0.0, 1.0, 0.0,
            0.6, -0.8, 0.0, 0.0, 1.0,
        ], dtype='f4')

        self.vbo = self.ctx.buffer(vertices)

        # We control the 'in_vert' and `in_color' variables
        self.vao = self.ctx.vertex_array(
            self.prog,
            [
                # Map in_vert to the first 2 floats
                # Map in_color to the next 3 floats
                (self.vbo, '2f 3f', 'in_vert', 'in_color')
            ],
        )

    def render(self, time: float, frame_time: float):
        self.ctx.clear(1.0, 1.0, 1.0)
        self.vao.render()


# if __name__ == '__main__':
#     SimpleColorTriangle.run()
