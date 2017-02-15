## ptinregion.py
##
## Need to install utm: pip install utm
##
## Input argument: None
## Test run: python ptinregion.py
##
## Fuctions:
## llPtInRegion(longi, lati, numValInBound, llBound)
##   Input: longitude, latitude, numValInBound, llBound
##   Output: inRegionFlag
##   Return: negative bit 0: invalid longitude
##           negative bit 1: invalid latitude
##           negative bit 2: invalid numValInBound
##           negative bit 3: invalid llBound
##           0: successful
##   Note: Point on boundary is inside.
## geoIDInRegion(geoID, numValInBound, llBound)
##   Input: geoID, numValInBound, llBound
##   Output: inRegionFlag
##   Return: negative bit 0: invalid geoID length
##           negative bit 1: invalid geoID binType
##           negative bit 2: invalid geoID binSize
##           negative bit 3: invalid geoID zoneNum
##           negative bit 4: invalid geoID zoneLetter
##           negative bit 5: invalid numValInBound
##           negative bit 6: invalid llBound
##           0: successful
##   Note: Point on boundary is inside.
##

import sys
from geoidutm import getLLFromGeoID

minLenGeoID = 25

## Function
##-------------------- Export functions -----
def utmPtInRegion(easting, northing, numValInBound, bound):
  ## Point on boundary is inside
  inRegionFlag = 0  ## Init.
  retVal = 0  ## Init.

  ## Check input parameters
  if (numValInBound < 6):
    retVal |= 4
  if (len(llBound) < numValInBound):
    retVal |= 8
  if (retVal != 0):
    retVal *= -1

  if (retVal == 0):
    oddNodes = False
    j = numValInBound - 2
    for i in xrange(0, numValInBound, 2):
      if ((bound[i] < easting and bound[j] >= easting) or (bound[j] < easting and bound[i] >= easting)):
        if ((bound[i+1] + (easting - bound[i]) / (bound[j] - bound[i]) * (bound[j+1] - bound[i+1])) < northing):
          oddNodes = not oddNodes
      #print j, i, easting, northing, bound[j], bound[j+1], bound[i], bound[i+1], oddNodes  ## Echo print
      j = i
    if (oddNodes):
      inRegionFlag = 1
  return retVal, inRegionFlag

def llPtInRegion(longi, lati, numValInBound, llBound):
  ## Point on boundary is inside
  inRegionFlag = 0  ## Init.
  retVal = 0  ## Init.

  ## Check input parameters
  if ((longi < -180.0) or (longi > 180.0)):
    retVal |= 1
  if ((lati < -90.0) or (lati > 90.0)):
    retVal |= 2
  if (numValInBound < 6):
    retVal |= 4
  if (len(llBound) < numValInBound):
    retVal |= 8
  if (retVal != 0):
    retVal *= -1

  if (retVal == 0):
    oddNodes = False
    j = numValInBound - 2
    for i in xrange(0, numValInBound, 2):
      if ((llBound[i] < longi and llBound[j] >= longi) or (llBound[j] < longi and llBound[i] >= longi)):
        if ((llBound[i+1] + (longi - llBound[i]) / (llBound[j] - llBound[i]) * (llBound[j+1] - llBound[i+1])) < lati):
          oddNodes = not oddNodes
      #print j, i, longi, lati, llBound[j], llBound[j+1], llBound[i], llBound[i+1], oddNodes  ## Echo print
      j = i
    if (oddNodes):
      inRegionFlag = 1
  return retVal, inRegionFlag

def geoIDInRegion(geoID, numValInBound, llBound):
  ## Point on boundary is inside
  inRegionFlag = 0  ## Init.
  retVal = 0  ## Init.
  centerLongi = 0.0
  centerLati = 0.0
  numValInBoundGeo = 0
  binSizeMeter = 0
  binType = 0
  llBoundGeo = [0,1,2,3,4,5,6,7,8,9,10,11]

  retVal, numValInBoundGeo, llBoundGeo, centerLongi, centerLati, binSizeMeter, binType = getLLFromGeoID(geoID)
  if (retVal == 0):
    if (numValInBound < 6):
      retVal |= 32
    if (len(llBound) < numValInBound):
      retVal |= 64
    if (retVal == 0):
      retVal, inRegionFlag = llPtInRegion(centerLongi, centerLati, numValInBound, llBound)
  if (retVal > 0):
    retVal *= -1
  return retVal, inRegionFlag

##-------------------- Test -----
## Function test
retVal = 0
inRegionFlag = 0
numValInBound = 8
llBound = [50.0,7.0,50.0,8.0,52.0,8.0,52.0,7.0]  ## in region
#llBound = [50.0,7.0,50.0,7.5,51.2,7.5,51.2,7.0]  ## on region
#llBound = [50.0,7.0,50.0,7.2,51.0,7.2,51.0,7.0]   ## out of region

## Setup arguments
## (longi, lati) = (51.2, 7.5) -> (easting, northing) = (395201.310381, 5673135.24118); 32U
longi = 51.2
lati = 7.5
geoID = '00000000001010032U0000000526900000131015'

## Calling function
retVal, inRegionFlag = llPtInRegion(longi, lati, numValInBound, llBound)
#print 'llPtInRegion():', longi, lati, numValInBound, llBound, ':', retVal, inRegionFlag  ## Echo print

retVal, inRegionFlag = geoIDInRegion(geoID, numValInBound, llBound)
#print 'geoIDInRegion():', geoID, numValInBound, llBound, ':', retVal, inRegionFlag  ## Echo print
