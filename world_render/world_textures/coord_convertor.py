import pyproj
# 900913 pyproj
# pyproj.Transformer.
p_ll = pyproj.Proj('epsg:4326') #4326
p_mt = pyproj.Proj('epsg:3857') # espg:3857 metric; same as EPSG:900913
t1 = pyproj.Transformer.from_proj(p_ll, p_mt)
t2 = pyproj.Transformer.from_proj(p_mt, p_ll)
_ecef_to_lla = pyproj.Transformer.from_crs(
    {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'},
    {"proj":'latlong', "ellps":'WGS84', "datum":'WGS84'}
    )
_lla_to_ecef = pyproj.Transformer.from_crs(
   {"proj":'latlong', "ellps":'WGS84', "datum":'WGS84'},
   {"proj":'geocent', "ellps":'WGS84', "datum":'WGS84'}
      )

def ecef_to_lla(x,y,z):
    return _ecef_to_lla.transform(x,y,z,radians=False)

def lla_to_ecef(lon, lat, alt=0):
    return _lla_to_ecef.transform(lon, lat, alt,radians=False)