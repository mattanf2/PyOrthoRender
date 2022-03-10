import owslib.wmts


URL= "https://openlayers.org/en/latest/examples/data/WMTSCapabilities.xml"
URL = "https://osmlab.github.io/wmts-osm/WMTSCapabilities.xml"
URL = "http://ows.mundialis.de/services/service?REQUEST=GetCapabilities"
cap = owslib.wmts.WebMapTileService(URL)
print(data)