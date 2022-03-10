import dataclasses
from io import BytesIO
from typing import List, Tuple
from PIL import Image
import numpy as np
import requests
from shapely.geometry import Polygon

from .coord_convertor import lla_to_ecef, ecef_to_lla
from .utils import bbox_middle, bbox_width, bbox_height

import math
# def marcator_deg2num(lat_deg, lon_deg, zoom):
#   lat_rad = math.radians(lat_deg)
#   n = 2.0 ** zoom
#   xtile = int((lon_deg + 180.0) / 360.0 * n)
#   ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
#   return (xtile, ytile)

import math

from world_render.world_textures.raster_cache import RasterCache


def marcator_num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)


class WorldTextureManager:
	def __init__(self):
		# TODO fix
		self.tile_size = 256
		self.world_bbox = (-180,-90, 180, 90)
		self.is_mercator = True
		self.is_lla = True
		self.min_zoom=0
		self.max_zoom=20
		self.layer_name = 'QQQQ'
		self.url = "https://tile.openstreetmap.org/{zoom}/{xtile}/{ytile}.png"
		self.url = "https://gis.sinica.edu.tw/worldmap/file-exists.php?img=BingH-jpg-{zoom}-{xtile}-{ytile}.png"

	def grid_to_wgs84lla(self, zoom, xtile, ytile):
		#TODO fix
		if self.is_mercator:
			n = 2.0 ** zoom
			lon_deg = xtile / n * 360.0 - 180.0
			lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
			lat_deg = math.degrees(lat_rad)
			return (lon_deg, lat_deg)
		else:
			devisions = 2 ** zoom
			world_bbox = self.world_bbox
			return (world_bbox[0] + (world_bbox[2] - world_bbox[0]) * xtile / devisions,
					world_bbox[1] + (world_bbox[3] - world_bbox[1]) * ytile / devisions)

	def get_tile_url(self, tile: 'WorldTileIndex'):
		return tile._manager.url.format(zoom=tile.zoom, xtile=tile.x, ytile=tile.y)

	def load_tile(self, tile: 'WorldTileIndex'):
		cache = RasterCache.instance()
		with cache.lock(tile):
			raster = cache.get(tile)
			if raster is None:
				res = requests.get(self.get_tile_url(tile))
				if 200 <= res.status_code < 300:
					raster = np.array(Image.open(BytesIO(res.content)))
				else:
					#TODO fix
					pass
				cache.put(tile, raster)
		return raster



	@property
	def query(self):
		return WorldTextureQuerier(self)

@dataclasses.dataclass(frozen=True)
class WorldTileIndex:
	_manager: 'WorldTextureManager'
	zoom: int
	x: int
	y: int

	def __bool__(self):
		return self.zoom >= 0 # return False on invalid tile

	@property
	def index(self):
		# TODO check
		base = sum((2 ** i) ** 2 for i in range(0, self.zoom))
		x_range = (2 ** self.zoom)
		return base + x_range * y + x

	@property
	def world_bbox(self):
		"""Returns the bounding box of the tile in WGS-84 lla"""
		bl = self._manager.grid_to_wgs84lla(self.zoom, self.x, self.y)
		tr = self._manager.grid_to_wgs84lla(self.zoom, self.x + 1, self.y + 1)
		return (bl[0], min(bl[1],tr[1]), tr[0], max(bl[1],tr[1]))

	def get_children(self):
		"""Children given in order of bl, br, tl, tr"""
		return [WorldTileIndex(self._manager, self.zoom + 1, self.x * 2, 	 self.y * 2),
				WorldTileIndex(self._manager, self.zoom + 1, self.x * 2 + 1, self.y * 2),
				WorldTileIndex(self._manager, self.zoom + 1, self.x * 2, 	 self.y * 2 + 1),
				WorldTileIndex(self._manager, self.zoom + 1, self.x * 2 + 1, self.y * 2 + 1)]

	@property
	def parent(self):
		return WorldTileIndex(self._manager, self.zoom - 1, self.x // 2, self.y // 2)

	def top(self):
		return WorldTileIndex(self._manager, 0, 0, 0)

	@property
	def mpp(self):
		"""Returns the meter per pixel resolution"""
		bbox = self.world_bbox
		middle = bbox_middle(bbox)
		pixel_width = bbox_width(bbox) / self._manager.tile_size
		pixel_height = bbox_height(bbox) / self._manager.tile_size
		center = np.array(lla_to_ecef(middle[0], middle[1]))
		center_dx = np.array(lla_to_ecef(middle[0] + pixel_width, middle[1]))
		center_dy = np.array(lla_to_ecef(middle[0], middle[1] + pixel_height))
		return max(np.linalg.norm(center - center_dx), np.linalg.norm(center - center_dy))

	def __repr__(self):
		return f'<Tile: {self._manager.get_tile_url(self)}>'


class WorldTextureQuerier:
	def __init__(self, manager: WorldTextureManager):
		self._manager = manager

	def get_tile_list_for_area(self, roi: Polygon, meter_per_pixels: List[int]):
		if isinstance(meter_per_pixels, (int, float)):
			meter_per_pixels = [meter_per_pixels] * (len(roi.exterior.coords) - 1)

		return self._get_tile_list_for_area_rec(WorldTileIndex(self._manager, 0, 0, 0), roi, meter_per_pixels)

	def _get_tile_list_for_area_rec(self, tile: WorldTileIndex, roi: Polygon, meter_per_pixels: List[int]):
		# TODO improve this function, any part of a tile is not detailed enough all the tile is replaced instead of just that part
		tile_bounds = Polygon.from_bounds(*tile.world_bbox)
		if not tile_bounds.intersects(roi):
			return []
		if self._is_tile_detailed_enough(tile, roi, meter_per_pixels):
			return [tile]
		else:
			ret = []
			for child in tile.get_children():
				 self._get_tile_list_for_area_rec(child, roi, meter_per_pixels)
			return ret

	def _is_tile_detailed_enough(self, tile: WorldTileIndex, roi: Polygon, meter_per_pixels: List[int]):
		if tile.zoom < self._manager.min_zoom:
			return False
		if tile.zoom >= self._manager.max_zoom:
			return True

		tile_bounds = Polygon.from_bounds(*tile.world_bbox)
		tile_in_roi = tile_bounds.intersection(roi)
		for x,y in tile_in_roi.exterior.coords:
			required_mpp = self._interpolate_polygon_value(roi, meter_per_pixels, (x,y))
			if required_mpp < tile.mpp:
				return False
		return True

	def _interpolate_polygon_value(self, polygon: Polygon, vertex_values: List[float], pos: Tuple[float, float]):
		distances = [np.linalg.norm([pos[0] - vert[0], pos[1] - vert[1]]) for vert in polygon.exterior.coords[:-1]]
		sum_dist = sum(distances)
		return sum(distances[index] * value for index, value in enumerate(vertex_values)) / sum_dist

	@property
	def world_bbox(self):
		return self._world_bbox

	@property
	def tile_size(self):
		return self._tile_size

def _print_tile(tile):
	print(tile._manager.url.format(zoom=tile.zoom, xtile=tile.x, ytile=tile.y))

if __name__ == '__main__':
	tel_aviv_poly = Polygon([[-179, -88],
			[-179, -89],
			[-178, -88]])
	manager = WorldTextureManager()



	tel_aviv_poly = Polygon([[34.809299, 32.105306],
							 [34.816682, 32.027579],
							 [34.741740, 32.031382]])
	Polygon.from_bounds(*WorldTileIndex(manager, 3, 4, 3).world_bbox).intersection(tel_aviv_poly)
	manager = WorldTextureManager()
	tiles = manager.query.get_tile_list_for_area(tel_aviv_poly, 100)
	hash(tiles[0])
	image = manager.load_tile(tiles[0])
	image = image

	# print("sdf**************")
	# for tile in tiles:
	# 	_print_tile(tile)
	# print()
	# _print_tile(tiles[0].parent)
	# _print_tile(tiles[0].parent.parent)
	# _print_tile(tiles[0].parent.parent.parent)
	# _print_tile(tiles[0].parent.parent.parent.parent)
	# _print_tile(tiles[0].parent.parent.parent.parent.parent)
	# _print_tile(tiles[0].parent.parent.parent.parent.parent.parent)
