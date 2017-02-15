## geoidutm.py
##
## Need to install utm: pip install utm
##
## Input argument: None
## Test run: python geoidutm.py
##
## Fuctions:
## getGeoIDFromLL(longi, lati, binSizeMeter, binType, zoneNumIn = -1)
##   Input: Longitude, Latitude, Bin size in meters, binType
##     Note: Bin size should be positive integer in meters (1 ~ 9999).
##     Note: binType 0: square (center location as geoID),
##                   1: Hexagon (center location as geoID)
##   Output: GeoID[40], centerLongi, centerLati, zoneNum
##     Note: GeoID: [Reserved][BinType][BinSize][ZoneNum][LatitudeBand]
##       [Easting][Northing]
##           #Bytes: 10,1,4,3,11,11 = 40 characters
##   Return: negative bit 0: invalid longitude
##           negative bit 1: invalid latitude
##           negative bit 2: invalid bin size
##           negative bit 3: invalid bin type
##           0 (successful)
## getLLFromGeoID(geoID)
##   Input: geoID
##   Output: numValInBound, llBound, centerLongitude, centerLatitude,
##     binSizeMeter, binType
##   Return: negative bit 0: invalid geoID length
##           negative bit 1: invalid geoID binType
##           negative bit 2: invalid geoID binSize
##           negative bit 3: invalid geoID zoneNum
##           negative bit 4: invalid geoID latitudeBand
##           0 (successful)
##

import utm, math, sys

minLenGeoID = 25

## Function
##-------------------- For bin in in general -----
def getLLBoundFromUTMBound(numVal, eastingClock, northingClock, zoneNum, latiBand):
  lonClock = [0] * numVal
  latClock = [0] * numVal
  for p in xrange(0, numVal):
    latClock[p], lonClock[p] = utm.to_latlon(eastingClock[p], northingClock[p], zoneNum, latiBand)
  return lonClock, latClock

def getLLBoundFromUTMBound2(numVal, eastingClock, northingClock, zoneNum, latiBand):
  inxBound = 0
  numValInBound = numVal * 2
  for i in xrange(0, numVal):
    llBound[inxBound+1], llBound[inxBound] = utm.to_latlon(eastingClock[i], northingClock[i], zoneNum, latiBand)
    inxBound += 2
  return numValInBound, llBound

##-------------------- Square bin -----
def getBoundFromCenterSquare(xOffset, yOffset, easting, northing):
  eastingClock = [0] * 4
  northingClock = [0] * 4
  eastingClock[0] = easting - xOffset
  eastingClock[1] = easting - xOffset
  eastingClock[2] = easting + xOffset
  eastingClock[3] = easting + xOffset
  northingClock[0] = northing - yOffset
  northingClock[1] = northing + yOffset
  northingClock[2] = northing + yOffset
  northingClock[3] = northing - yOffset
  return eastingClock, northingClock

def getGeoIDXYCenterSquare(easting, northing, binSizeMeter, zoneNum, latiBand):
  halfBinSize = binSizeMeter / 2.0
  xSeg = binSizeMeter
  xOffset = halfBinSize
  ySeg = binSizeMeter
  yOffset = halfBinSize
  x = int(easting / xSeg)
  y = int(northing / ySeg)
  centerEasting = x * xSeg + xOffset
  centerNorthing = y * ySeg + yOffset
  centerLati, centerLongi = utm.to_latlon(centerEasting, centerNorthing, zoneNum, latiBand)
  return x, y, centerLongi, centerLati

def getGeoIDCenterBoundLLSquare(binSizeMeter, x, y):
  eastingClock = [0,1,2,3]
  northingClock = [0,1,2,3]
  halfBinSize = binSizeMeter / 2.0
  xSeg = binSizeMeter
  xOffset = halfBinSize
  ySeg = binSizeMeter
  yOffset = halfBinSize
  easting = x * xSeg + xOffset
  northing = y * ySeg + yOffset
  centerLati, centerLongi = utm.to_latlon(easting, northing, zoneNum, latiBand)
  eastingClock, northingClock = getBoundFromCenterSquare(xOffset, yOffset, easting, northing)
  numValInBound, llBound = getLLBoundFromUTMBound2(4, eastingClock, northingClock, zoneNum, latiBand)
  return numValInBound, llBound, centerLongi, centerLati

##-------------------- Hexagon bin -----
def isLeft(x, y, aX, aY, bX, bY):
  ## http://stackoverflow.com/questions/1560492/
  ##   how-to-tell-whether-a-point-is-to-the-right-or-left-side-of-a-line
  ## (x, y): poiny to check; (aX, aY): line point 1; (bX, bY): line point 2
  ## val: 0: colinear; > 0: left; < 0: right
  ##   line horizontal -> > 0: above the line
  leftFlag = 0
  val = (bX - aX) * (y - aY) - (bY - aY) * (x - aX)
  if (val > 0):
    leftFlag = 1
  elif (val < 0):
    leftFlag = 0
  return leftFlag

def getBoundFromCenterHexagon(xSeg, ySeg, centerEasting, centerNorthing):
  eastingClock = [0,1,2,3,4,5]
  northingClock = [0,1,2,3,4,5]
  eastingClock[0] = centerEasting - 2.0 * xSeg
  eastingClock[1] = centerEasting - xSeg
  eastingClock[2] = centerEasting + xSeg
  eastingClock[3] = centerEasting + 2.0 * xSeg
  eastingClock[4] = centerEasting + xSeg
  eastingClock[5] = centerEasting - xSeg
  northingClock[0] = centerNorthing
  northingClock[1] = centerNorthing + ySeg
  northingClock[2] = centerNorthing + ySeg
  northingClock[3] = centerNorthing
  northingClock[4] = centerNorthing - ySeg
  northingClock[5] = centerNorthing - ySeg
  return eastingClock, northingClock

def getGeoIDXYCenterHexagon(easting, northing, binSizeMeter, zoneNum, latiBand):
  eastingClock = [0,1,2,3,4,5]
  northingClock = [0,1,2,3,4,5]
  xSeg = binSizeMeter / 4.0
  xSegNum = math.floor(easting / xSeg)
  xRegionNum = math.floor(xSegNum / 6)
  xRegionRem = xSegNum % 6               ## 0 ~ 5

  ySeg = binSizeMeter / 2.0 * math.sin(math.pi / 3.0)
  ySegNum = math.floor(northing / ySeg)
  yRegionRem = ySegNum % 2

  x = math.floor(xSegNum/3)
  y = ySegNum

  ## Init. center and hexagon bound
  if ((xRegionRem >= 0) and (xRegionRem < 3)):
    centerEasting = xRegionNum * 1.5 * binSizeMeter + 0.5 * binSizeMeter
  else:
    centerEasting = xRegionNum * 1.5 * binSizeMeter + binSizeMeter + xSeg
  centerNorthing = ySegNum * ySeg
  eastingClock, northingClock = getBoundFromCenterHexagon(xSeg, ySeg, centerEasting, centerNorthing)

  #print 'A', xSeg, xSegNum, xRegionNum, xRegionRem, ySeg, ySegNum, yRegionRem, x, y, centerEasting, centerNorthing  ## Echo print

  ## Revise x, y
  if ((xRegionRem == 0) and (yRegionRem == 0)):
    leftFlag = isLeft(easting, northing, eastingClock[0], northingClock[0], eastingClock[1], northingClock[1])
    if (leftFlag != 1):
      x += 1  ## (x, y) = (odd, even)
    else:
      y += 1  ## (even, odd)
  elif (((xRegionRem == 1) or (xRegionRem == 2)) and (yRegionRem == 0)):
    x += 1  ## (odd, even)
  elif ((xRegionRem == 3) and (yRegionRem == 0)):
    leftFlag = isLeft(easting, northing, eastingClock[5], northingClock[5], eastingClock[0], northingClock[0])
    if (leftFlag == 0):
      x += 1  ## (even, odd)
      y += 1
  elif (((xRegionRem == 4) or (xRegionRem == 5)) and (yRegionRem == 0)):
    x += 1  ## (even, odd)
    y += 1
  elif ((xRegionRem == 0) and (yRegionRem == 1)):
    leftFlag = isLeft(easting, northing, eastingClock[5], northingClock[5], eastingClock[0], northingClock[0])
    if (leftFlag != 1):
      x += 1  ## (odd, even)
      y += 1
  elif (((xRegionRem == 1) or (xRegionRem == 2)) and (yRegionRem == 1)):
    x += 1  ## (odd, even)
    y += 1
  elif ((xRegionRem == 3) and (yRegionRem == 1)):
    leftFlag = isLeft(easting, northing, eastingClock[0], northingClock[0], eastingClock[1], northingClock[1])
    if (leftFlag == 0):
      x += 1  ## (even, odd)
    else:
      y += 1  ## (odd, even)
  elif (((xRegionRem == 4) or (xRegionRem == 5)) and (yRegionRem == 1)):
    x += 1  ## (even, odd)

  #print 'B', xSeg, xSegNum, xRegionNum, xRegionRem, ySeg, ySegNum, yRegionRem, x, y, centerEasting, centerNorthing  ## Echo print

  ## Update center and Hexagon bound
  centerEasting = x * 3.0 * xSeg - xSeg 
  centerNorthing = y * ySeg

  #print 'C', centerEasting, centerNorthing, zoneNum, latiBand  ## Echo print

  #eastingClock, northingClock = getBoundFromCenterHexagon(xSeg, ySeg, centerEasting, centerNorthing)
  centerLati, centerLongi = utm.to_latlon(centerEasting, centerNorthing, zoneNum, latiBand)
  return x, y, centerLongi, centerLati

def getGeoIDCenterBoundLLHexagon(binSizeMeter, zoneNum, latiBand, x, y):
  eastingClock = [0,1,2,3,4,5]
  northingClock = [0,1,2,3,4,5]
  llBound = [0,1,2,3,4,5,6,7,8,9,10,11]
  xSeg = binSizeMeter / 4.0
  ySeg = binSizeMeter / 2.0 * math.sin(math.pi / 3.0)
  easting = x * 3.0 * xSeg - xSeg
  northing = y * ySeg
  centerLati, centerLongi = utm.to_latlon(easting, northing, zoneNum, latiBand)
  eastingClock, northingClock = getBoundFromCenterHexagon(xSeg, ySeg, easting, northing)
  numValInBound, llBound = getLLBoundFromUTMBound2(6, eastingClock, northingClock, zoneNum, latiBand)
  return numValInBound, llBound, centerLongi, centerLati 

##-------------------- GeoID -----
def assembleGeoID(binType, binSizeMeter, zoneNum, latiBand, x, y):
  sReserved = '0000000000'
  sBinSize = '%04d' % (binSizeMeter)
  sZoneNum = '%02d' % (zoneNum)
  sX = '%011d' % (x)
  sY = '%011d' % (y)
  geoID = sReserved + str(binType) + sBinSize + sZoneNum + latiBand + sX + sY  ## 10, 1, 4, 2, 1, 11, 11 = 40
  return geoID

def disassembleGeoID(geoID):
  binType = int(geoID[10:11])
  binSizeMeter = int(geoID[11:15])
  zoneNum = int(geoID[15:17])
  latiBand = geoID[17:18]
  latiBand = latiBand.upper()
  x = int(geoID[18:29])
  y = int(geoID[29:40])
  return zoneNum, latiBand, x, y, binType, binSizeMeter

##-------------------- Export functions -----
def getGeoIDFromUTM(easting, northing, binSizeMeter, binType, zoneNum, latiBand):
  centerLongi = 0.0
  centerLati = 0.0
  x = 0
  y = 0
  if (binType == 0):  ## Square
    x, y, centerLongi, centerLati = getGeoIDXYCenterSquare(easting, northing, binSizeMeter, zoneNum, latiBand)
  elif (binType == 1):  ## Hexagon
    x, y, centerLongi, centerLati = getGeoIDXYCenterHexagon(easting, northing, binSizeMeter, zoneNum, latiBand)
    if (x == 0):  ## Jan. 19, 2017; Need to get GeoID from previous zone to make sure GeoID used to check same bin
      eastingMove = easting - binSizeMeter / 2.0
      latMove, lonMov = utm.to_latlon(eastingMove, northing, zoneNum, latiBand)  ## Move LL
      eastingUse, northingUse, zoneNum, latiBand = utm.from_latlon(latMove, lonMov)  ## Compute moved UTM
      x, y, centerLongi, centerLati = getGeoIDXYCenterHexagon(eastingUse, northingUse, binSizeMeter, zoneNum, latiBand)
  geoID = assembleGeoID(binType, binSizeMeter, zoneNum, latiBand, x, y)
  #print "getGeoIDFromUTM()", easting, northing, geoID, binType, binSizeMeter, ';' , x, y, centerLongi, centerLati  ## Echo print
  return geoID, centerLongi, centerLati

def getGeoIDFromLL(longi, lati, binSizeMeter, binType, zoneNumIn = -1):
  retVal = 0  ## Init.
  geoID = ""
  centerLongi = 0.0
  centerLati = 0.0
  zoneNum = 0
  ## Check input parameters
  if ((longi < -180.0) or (longi > 180.0)):
    retVal |= 1
  if ((lati < -80.0) or (lati > 84.0)):
    retVal |= 2
  if ((binSizeMeter < 1) or (binSizeMeter > 9999)):
    retVal |= 4
  if ((binType != 0) and (binType != 1)):
    retVal |= 8
  if (retVal != 0):
    retVal *= -1
  else:
    zoneNumUse = zoneNumIn
    if ((zoneNumUse <= 0) or (zoneNumUse > 60)):  ## Invalide zoneNum
      #if (zoneNumUse == -1):
      #  zoneNumUse = 10  ## US west boundary; Use this way to make plotting binning region smooth; causing to_latlon issue out of range in easting
      #  easting, northing, zoneNum, latiBand = utm.from_latlon(lati, longi, zoneNumUse)  ## LL -> UTM
      #else:
        easting, northing, zoneNum, latiBand = utm.from_latlon(lati, longi)  ## LL -> UTM
    else:
      easting, northing, zoneNum, latiBand = utm.from_latlon(lati, longi, zoneNumUse)  ## LL -> UTM; Force zone
    #print easting, northing, zoneNum, latiBand  ## Echo print
    geoID, centerLongi, centerLati = getGeoIDFromUTM(easting, northing, binSizeMeter, binType, zoneNum, latiBand)
  return retVal, geoID, centerLongi, centerLati, zoneNum

def getLLFromGeoID(geoID):
  retVal = 0  ## Init.
  numValInBound = 0
  llBound = [0,1,2,3,4,5,6,7,8,9,10,11]
  centerLongi = 0.0
  centerLati = 0.0
  binSizeMeter = 0
  binType = 0
  zoneNum = 0
  latiBand = ''
  x = 0.0
  y = 0.0

  ## Check input parameters
  if ((len(geoID) > 40) or (len(geoID) <= minLenGeoID)):
    retVal |= 1
  if (retVal != 0):
    retVal *= -1
  else:
    zoneNum, latiBand, x, y, binType, binSizeMeter = disassembleGeoID(geoID)
    #print geoID, ':', binType, binSizeMeter, zoneNum, latiBand, x, y         ## Echo print

    ## Check input parameters
    if ((binType != 0) and (binType != 1)):
      retVal |= 2
    if ((binSizeMeter <= 0) or (binSizeMeter > 9999)):
      retVal |= 4
    if ((zoneNum <= 0) or (zoneNum > 60)):
      retVal |= 8
    latiBandValid = 0
    sLatiBandValid = 'CDEFGHJKLMNPQRSTUVWX'
    if (sLatiBandValid.find(latiBand)!=-1):  ## Found
      latiBandValid = 1
    if (latiBandValid == 0):
      retVal |= 16
    if (retVal != 0):
      retVal *= -1

    if (retVal == 0):
      if (binType == 0):
        numValInBound, llBound, centerLongi, centerLati = getGeoIDCenterBoundLLSquare(binSizeMeter, x, y)
      elif (binType == 1):
        numValInBound, llBound, centerLongi, centerLati = getGeoIDCenterBoundLLHexagon(binSizeMeter, zoneNum, latiBand, x, y)
  return retVal, numValInBound, llBound, centerLongi, centerLati, binSizeMeter, binType

##-------------------- Test -----
## Function test
retVal = 0
centerLongi = 0.0
centerLati = 0.0
zoneNum = 0
numValInBound = 0
llBound = [0,1,2,3,4,5,6,7,8,9,10,11]

## Setup arguments
## (longi, lati) = (51.2, 7.5) -> (easting, northing) = (395201.310381, 5673135.24118); 32U
#longi = 51.2
#lati = 7.5
longi = -122.51593
lati = 37.752214
binSizeMeter = 100
binType = 1
geoID = '00000000001010032U0000000526900000131015'

## Calling function
retVal, geoID, centerLongi, centerLati, zoneNum = getGeoIDFromLL(longi, lati, binSizeMeter, binType)
#print 'getGeoIDFromLL():', longi, lati, binSizeMeter, binType, ':', retVal, geoID, centerLongi, centerLati, zoneNum  ## Echo print

retVal, numValInBound, llBound, centerLongi, centerLati, binSizeMeter, binType = getLLFromGeoID(geoID)
#print 'getLLFromGeoID():', geoID, ':', retVal, numValInBound, llBound, centerLongi, centerLati, binSizeMeter, binType  ## Echo print
