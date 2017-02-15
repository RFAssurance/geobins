# geobins
Geographic binning algorithm to allow universal utilization of bins across any method.

## getBinsOneLLBound(): [getBinsInRegions.py]
  Input a longitude and latitude polygon region with optional (key, value) properties. A GeoJSON file and couple of mid/mif (input boundary, bin boundary, bin center) files will be generated.

## getBinGeoJSONFromGeoID(): [getBinsInRegions.py]
  Input a GeoID with optional (key, value) properties. A JSON string object will be returned.

## getGeoIDFromLL(longi, lati, binSizeMeter, binType, zoneNumIn = -1)
Input: Longitude, Latitude, Bin size in meters, binType
Note: Bin size should be positive integer in meters (1 ~ 9999).
Note: binType 0: square (center location as geoID),
              1: Hexagon (center location as geoID)
Output: GeoID[40], centerLongi, centerLati, zoneNum
Note: GeoID: [Reserved][BinType][BinSize][ZoneNum][LatitudeBand]
 [Easting][Northing]
Bytes: 10,1,4,3,11,11 = 40 characters
Return: negative bit 0: invalid longitude
      negative bit 1: invalid latitude
      negative bit 2: invalid bin size
      negative bit 3: invalid bin type
      0 (successful)

## getLLFromGeoID(geoID)
Input: geoID
Output: numValInBound, llBound, centerLongitude, centerLatitude,
    binSizeMeter, binType
Return: negative bit 0: invalid geoID length
      negative bit 1: invalid geoID binType
      negative bit 2: invalid geoID binSize
      negative bit 3: invalid geoID zoneNum
      negative bit 4: invalid geoID latitudeBand
      0 (successful)

## llPtInRegion(longi, lati, numValInBound, llBound)
Input: longitude, latitude, numValInBound, llBound
Output: inRegionFlag
Return: negative bit 0: invalid longitude
      negative bit 1: invalid latitude
      negative bit 2: invalid numValInBound
      negative bit 3: invalid llBound
      0: successful
Note: Point on boundary is inside.

## geoIDInRegion(geoID, numValInBound, llBound)
Input: geoID, numValInBound, llBound
Output: inRegionFlag
Return: negative bit 0: invalid geoID length
      negative bit 1: invalid geoID binType
      negative bit 2: invalid geoID binSize
      negative bit 3: invalid geoID zoneNum
      negative bit 4: invalid geoID zoneLetter
      negative bit 5: invalid numValInBound
      negative bit 6: invalid llBound
      0: successful
Note: Point on boundary is inside.

## -----------------------------------
When use, you would need to install utm package (using “pip install utm” in advance before running):
You can run “python geoidutm.py”

When calling the functions in your python code, you would need:
import utm, math, sys
from geoidutm import getGeoIDFromLL, getGeoIDFromUTM, getBoundFromCenterSquare, getBoundFromCenterHexagon
from ptinregion import utmPtInRegion

---------------------------------------
At the end of each Python code files, there is a “Test” section which contains sample calling examples.
You can remove the “#” in front of print to show some results when you run.

For example of the function getGeoIDFromLL():
retVal = 0
centerLongi = 0.0
centerLati = 0.0
zoneNum = 0

## Setup arguments
(longi, lati) = (51.2, 7.5) -> (easting, northing) = (395201.310381, 5673135.24118); 32U
longi = 51.2
lati = 7.5
binSizeMeter = 100
binType = 1
geoID = '00000000001010032U0000000526900000131015'

## Calling function
retVal, geoID, centerLongi, centerLati, zoneNum = getGeoIDFromLL(longi, lati, binSizeMeter, binType)
print 'getGeoIDFromLL():', longi, lati, binSizeMeter, binType, ':', retVal, geoID, centerLongi, centerLati, zoneNum  ## Echo print

----------------------------------------------
I verify the code using getBinsOneLLBound() (under development; still in progress) with the following:
numValInBound = 8
llBound = [-122.51593,37.75312,-122.4993,37.78031,-122.432803,37.795259,-122.44142,37.752214]  ## in region
binSizeMeter = 100
binType = 1  ## Hexagon
binType = 0  ## Square
