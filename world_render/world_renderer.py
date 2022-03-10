from typing import Iterable
import numpy as np

from world_render import assets
from world_render.geometrizer import TileGeometryBuilder, TileBuffers
from world_render.world_textures.texture_manager import WorldTextureManager, WorldTileIndex


class WorldRenderer(assets.Example):

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

        self.vaos = []
        self.textures = []
        self.images = []
        for index, buffer in enumerate(buffers):
            assert buffer.vertices.dtype == np.float64
            assert buffer.texcoords.dtype == np.float64
            assert buffer.indices.dtype == np.uint16

            verts = self.ctx.buffer(buffer.vertices)
            texcos = self.ctx.buffer(buffer.texcoords)
            inds = self.ctx.buffer(buffer.indices)

            image = self._texture_manager.load_tile(buffer.tile)
            assert image.dtype == np.uint8
            self.images.append(image)
            self.textures.append(self.ctx.texture(list(image.shape)[:2], image.shape[2], image.data, dtype='f1'))

            # We control the 'in_vert' and `in_color' variables
            self.vaos.append(self.ctx.vertex_array(
                    self.prog,
                    [
                        # Map in_vert to the first 2 floats
                        # Map in_color to the next 3 floats
                        (verts, '2f8', 'in_vert'),
                        (texcos, '2f8', 'in_tex')
                    ],
                    index_buffer=inds,
                    index_element_size=2,  # 16 bit / 'u2' index buffer
                ))

    def render(self, time: float, frame_time: float):
        self.ctx.clear(1.0, 1.0, 1.0)
        for index in range(len(self.vaos)):
            self.textures[index].use()
            self.vaos[index].render()

if __name__ == '__main__':
    WorldRenderer.run()
    #wr.run()





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
