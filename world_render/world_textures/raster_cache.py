from typing import Hashable

import diskcache
# TODO fix
CACHE_DIR = "C:\Temp\GpuCache"
CACHE_SIZE = 2 ** 27  # 128meg
LOCK_EXPIRATION = 2 * 60 # 2 minutes
DATA_EXPIRATION = 10*24*60*60 # 10 days
class RasterCache:
    _instance: 'RasterCache' = None

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = RasterCache()
        return cls._instance

    def __init__(self):
        self._cache = diskcache.FanoutCache(CACHE_DIR, size_limit=int(CACHE_SIZE))

    def lock(self, key: Hashable):
        return diskcache.Lock(self._cache, LOCK_EXPIRATION)

    def get(self, key: Hashable):
        return self._cache.get(key)

    def put(self, key: Hashable, value):
        return self._cache.set(key, value, expire=DATA_EXPIRATION)


