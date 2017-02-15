## getBinsInRegions.py
##
## Need to install utm: pip install utm
##
## Input argument: None
## Test run: python getBinsInRegions.py
##
## Fuctions:
## getBinsInARegion(numValInBound, llBound, binSizeMeter, binType, pathName, zoneNum = -1, **kwargs)
##   Input: numValInBound, llBound, binSizeMeter, binType, pathName, optional
##          zoneNum, optional key value pairs for properties
##   Return: negative bit 0: invalid numValInBound
##           negative bit 1: invalid llBound
##           negative bit 2: invalid bin size
##           negative bit 3: invalid bin type
##           negative bit 4: invalid pathName
##           negative bit 5: path cannot be created
##           negative bit 6: file cannot be created
##           0: successful
##   Note: Generate a geoJSON file: GeoBin.json.
##   Note: Typically, zoneNum should be set to -1 in order to detect zone
##         number automatically from latitude and longitude.
##   Note: If kwargs is not provided, default GeoJSON properties will be used.
## getBinGeoJSONFromGeoID(geoID, **kwargs)
##   Input: geoID, optional key value pairs for properties
##   Output: data (GeoJSON in plain string format)
##   Return: negative bit 0: invalid geoID length
##           negative bit 1: invalid geoID binType
##           negative bit 2: invalid geoID binSize
##           negative bit 3: invalid geoID zoneNum
##           negative bit 4: invalid geoID zoneLetter
##           0: successful
##   Note: If kwargs is not provided, default GeoJSON properties will be used.
##

import utm, math, sys, os, errno
from geoidutm import getGeoIDFromLL, getGeoIDFromUTM, getLLFromGeoID, getBoundFromCenterSquare, getBoundFromCenterHexagon, getLLBoundFromUTMBound
from ptinregion import utmPtInRegion, llPtInRegion
#import json

## Global variables (default values)
strokeColorDef = "#000000"
strokeWeightDef = 1
strokeOpacityDef = 1
fillColorDef = "#FFFFFF"
fillOpacityDef = 0.3

## Function
def dist2LL(lon1, lat1, lon2, lat2):
    ## Haversine formula for distance between 2 LLs
    radius = 6371 # km
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist = radius * c
    return dist

def getRecFromBound(numValInBound, bound):
  ## Get rectangular boundary from a polygon; X0, Y0, X1, Y1, ...
  recBound = [0,1,2,3,4,5,6,7]
  minX = minY = maxX = maxY = 0.0
  for i in xrange(0, numValInBound, 2):
    if (i == 0):
      minX = maxX = bound[i]
      minY = maxY = bound[i+1]
    else:
      if (minX > bound[i]):
        minX = bound[i]
      if (minY > bound[i+1]):
        minY = bound[i+1]
      if (maxX < bound[i]):
        maxX = bound[i]
      if (maxY < bound[i+1]):
        maxY = bound[i+1]
  recBound[0] = recBound[2] = minX
  recBound[1] = recBound[7] = minY
  recBound[3] = recBound[5] = maxY
  recBound[4] = recBound[6] = maxX
  return recBound

def convertLLToUTMOneBound(numValInBound, llBound, zoneNumForce = -1):
  utmBound = [0] * numValInBound
  zoneNum = 0
  zoneNumUse = zoneNumForce
  for i in xrange(0, numValInBound, 2):
    if ((zoneNumUse <= 0) or (zoneNumUse > 60)):
      utmBound[i], utmBound[i+1], zoneNum, latiBand = utm.from_latlon(llBound[i+1], llBound[i])
    else:
      utmBound[i], utmBound[i+1], zoneNum, latiBand = utm.from_latlon(llBound[i+1], llBound[i], zoneNumUse)
    zoneNumUse = zoneNum
  return utmBound

def convertUTMToLLOneBound(numValInBound, utmBound, zoneNum, latiBand):
  llBoundFromUTM = [0] * numValInBound
  for i in xrange(0, numValInBound, 2):
    llBoundFromUTM[i+1], llBoundFromUTM[i] = utm.to_latlon(utmBound[i], utmBound[i+1], zoneNum, latiBand)
  return llBoundFromUTM

def getDistLLRecBound(llRecBound):
  distH1 = dist2LL(llRecBound[0], llRecBound[1], llRecBound[6], llRecBound[7])
  distH2 = dist2LL(llRecBound[2], llRecBound[3], llRecBound[4], llRecBound[5])
  distH = distH1
  if (distH < distH2):
    distH = distH2
  distH *= 1000.0;  ## Meters
  distV1 = dist2LL(llRecBound[0], llRecBound[1], llRecBound[2], llRecBound[3])
  distV2 = dist2LL(llRecBound[4], llRecBound[5], llRecBound[6], llRecBound[7])
  distV = distV1
  if (distV < distV2):
    distV = distV2
  distV *= 1000.0;  ## Meters
  return distH, distV

def getDistUTMRecBound(utmRecBound):
  distH = utmRecBound[6] - utmRecBound[0]
  distV = utmRecBound[3] - utmRecBound[1]
  return distH, distV

def writeDataJsonGeo(geojson_file, firstFlag, geoID, centerLongi, centerLati, numBinBound, lonClock, latClock):
  binCenterFlag = 0
  if (firstFlag == 1):
    geojson_file.write("  },\n  \"features\": [\n")  ## Data for the previous one
    #geojson_file.write("  \"features\": [\n")  ## Data for the previous one; uncomment if no default properties
  else:
    geojson_file.write("    },\n")  ## Data for the previous one

  ## Center; do not output; Jan. 23, 2017
  if (binCenterFlag == 1):
    geojson_file.write("    {\n      \"type\": \"Feature\",\n")
    geojson_file.write("      \"geometry\": {\n")
    geojson_file.write("        \"type\": \"Point\",\n        \"coordinates\": [{0}, {1}]\n".format(centerLongi, centerLati))
    geojson_file.write("      },\n")
    geojson_file.write("      \"properties\": {\n")
    geojson_file.write("        \"geoid\": \"{0}\"\n".format(geoID))
    geojson_file.write("      }\n")
    geojson_file.write("    },\n")  ## Comment out if only output center or boundary

  ## Boundary
  geojson_file.write("    {\n      \"type\": \"Feature\",\n")
  geojson_file.write("      \"geometry\": {\n")
  geojson_file.write("        \"type\": \"Polygon\",\n")
  geojson_file.write("        \"coordinates\": [[\n")
  for i in xrange(0, numBinBound):
    if (i != 0):
      geojson_file.write(",\n")  ## Jan. 23, 2017
    geojson_file.write("          [{0}, {1}]".format(lonClock[i], latClock[i]))
  geojson_file.write("\n        ]]\n      },\n")
  geojson_file.write("      \"properties\": {\n")
  geojson_file.write("        \"geoid\": \"{0}\"\n".format(geoID))
  geojson_file.write("      }\n")
  return

def writeFooterJsonGeo(geojson_file, recCnt):
  if (recCnt == 0):
    geojson_file.write("  }\n")
  else:
    geojson_file.write("    }\n")  ## Data for the previous one
    geojson_file.write("  ]\n")
  geojson_file.write("}\n")
  return

def writeHeaderJsonGeo(geojson_file, **kwargs):
  firstFlag = 1
  gotStColor = 0
  gotStWeight = 0
  gotStOpa = 0
  gotFiColor = 0
  gotFiOpa = 0
  geojson_file.write("{\n  \"type\":\"FeatureCollection\",\n")
  geojson_file.write("  \"defaultProperties\": {\n")
  for key, value in kwargs.iteritems():
    if (firstFlag != 1):
      geojson_file.write(",\n")
    if (type(kwargs[key]) == str):  ## Check value type of a key
      geojson_file.write("    \"{0}\": \"{1}\"".format(key, value))
    else:
      geojson_file.write("    \"{0}\": {1}".format(key, value))
    firstFlag = 0
    if (key.lower() == "strokeColor".lower()):
      gotStColor = 1
    elif (key.lower() == "strokeWeight".lower()):
      gotStWeight = 1
    elif (key.lower() == "strokeOpacity".lower()):
      gotStOpa = 1
    elif (key.lower() == "fillColor".lower()):
      gotFiColor = 1
    elif (key.lower() == "fillOpacity".lower()):
      gotFiOpa = 1
  ## Output default properties if keys are not input
  if (gotStColor == 0):    ## JS style
    if (firstFlag != 1):
      geojson_file.write(",\n")
    geojson_file.write("    \"strokeColor\": \"{0}\"".format(strokeColorDef))
    firstFlag = 0
  if (gotStWeight == 0):
    if (firstFlag != 1):
      geojson_file.write(",\n")
    geojson_file.write("    \"strokeWeight\": {0}".format(strokeWeightDef))
    firstFlag = 0
  if (gotStOpa == 0):
    if (firstFlag != 1):
      geojson_file.write(",\n")
    geojson_file.write("    \"strokeOpacity\": {0}".format(strokeOpacityDef))
    firstFlag = 0
  if (gotFiColor == 0):
    if (firstFlag != 1):
      geojson_file.write(",\n")
    geojson_file.write("    \"fillColor\": \"{0}\"".format(fillColorDef))
    firstFlag = 0
  if (gotFiOpa == 0):
    if (firstFlag != 1):
      geojson_file.write(",\n")
    geojson_file.write("    \"fillOpacity\": {0}".format(fillOpacityDef))
    firstFlag = 0
  geojson_file.write("\n")
  return

def mkdirWChk(pathName):
  retVal = 0
  try:  ## Try to create folder first to prevent a common race condition
    os.makedirs(pathName)
  except OSError:
    if not os.path.isdir(pathName):  ## os.path.exists() does not distinguish file and path
      print "Cannot create path:" + pathName
      retVal |= 32
  return retVal

def openFileWChk(pathName, fnameIn):
  retVal = 0
  fname = os.path.join(pathName, fnameIn)  ## os.sep
  try:
    out_file = open(fname, "w")
  except IOError:
    print "Cannot open file for write:" + fname
    retVal |= 64
  return retVal, out_file

def openFileWMkdir(pathName, fnameIn):
  retVal = 0
  retVal = mkdirWChk(pathName)
  if (retVal == 0):
    retVal, out_file = openFileWChk(pathName, fnameIn)
  return retVal, out_file

def mifHeaderID(mif_file):
  mif_file.write("Version 450\nCharset \"WindowsLatin1\"\nDelimiter \",\"\nCoordSys Earth Projection 1, 0\n")
  mif_file.write("Columns 1\n  ID Char(60)\nData\n\n")
  return

def createBoundFile(pathName, bounFnamePre, numValInBound, llBound):
  retVal = mkdirWChk(pathName)
  midFname = bounFnamePre + ".mid"
  mifFname = bounFnamePre + ".mif"
  if (retVal == 0):
    retVal, boundMid_file = openFileWChk(pathName, midFname)
  if (retVal == 0):
    retVal, boundMif_file = openFileWChk(pathName, mifFname)
  if (retVal == 0):
    boundMid_file.write("0\n")
    mifHeaderID(boundMif_file)
    numPt = int(math.floor(numValInBound / 2.0) + 1)
    boundMif_file.write("Region 1\n  {0}\n".format(numPt))
    for i in xrange(0, numValInBound, 2):
      boundMif_file.write("{0} {1}\n".format(llBound[i], llBound[i+1]))
    boundMif_file.write("{0} {1}\n".format(llBound[0], llBound[1]))
    boundMif_file.write("  Pen (3,2,255)\n    Brush (1,0,255)\n")  ## Blue color outline
    #boundMif_file.write("  Pen (3,2,65280)\n    Brush (1,0,16777215)\n")  ## Green color outline
  boundMid_file.close()
  boundMif_file.close()
  return retVal

def writeDataBinCenterGeo(outMid_file, outMif_file, geoID, centerLongi, centerLati):
  outMid_file.write("{0}\n".format(geoID))
  outMif_file.write("Point {0} {1}\n    Symbol(32,0,4)\n".format(centerLongi, centerLati))  ## SYMBOL (shape, color, size)
  return

def writeDataBinBoundGeo(outMid_file, outMif_file, geoID, numBinBound, lonClock, latClock):
  outMid_file.write("{0}\n".format(geoID))
  outMif_file.write("Region 1\n  {0}\n".format(numBinBound+1))
  for i in xrange(0, numBinBound):
    outMif_file.write("{0} {1}\n".format(lonClock[i], latClock[i]))
  outMif_file.write("{0} {1}\n".format(lonClock[0], latClock[0]))
  outMif_file.write("  Pen (3,2,16711680)\n    Brush (1,0,16777215)\n")  ## Red color outline
  return

def openMidMifFileWMkdirGeo(pathName):
  retVal = mkdirWChk(pathName)
  if (retVal == 0):
    retVal, geoBinCenterMid_file = openFileWChk(pathName, "GeoBinCenter.mid")
  if (retVal == 0):
    retVal, geoBinCenterMif_file = openFileWChk(pathName, "GeoBinCenter.mif")
  if (retVal == 0):
    retVal, geoBinBoundMid_file = openFileWChk(pathName, "GeoBinBound.mid")
  if (retVal == 0):
    retVal, geoBinBoundMif_file = openFileWChk(pathName, "GeoBinBound.mif")
  if (retVal == 0):
    mifHeaderID(geoBinCenterMif_file) 
    mifHeaderID(geoBinBoundMif_file)
  return retVal, geoBinCenterMid_file, geoBinCenterMif_file, geoBinBoundMid_file, geoBinBoundMif_file

def getBinsOneLLBoundChkPara(numValInBound, llBound, binSizeMeter, binType, pathName):
  retVal = 0  ## Init.
  if (numValInBound < 6):
      retVal |= 1
  if (len(llBound) < numValInBound):
      retVal |= 2
  if ((retVal & 2) != 2):
    numValInBoundUse = numValInBound
    if (len(llBound) < numValInBoundUse):
      numValInBoundUse = len(llBound)
    if ((numValInBoundUse % 2) == 1):  ## Odd
      numValInBoundUse -= 1
    for i in xrange(0, numValInBoundUse, 2):
      if ((llBound[i] < -180.0) or (llBound[i] > 180.0)):  ## Longitude range
        retVal |= 2
      if ((llBound[i+1] < -90.0) or (llBound[i+1] > 90.0)):  ## Latitude range
        retVal |= 2
  if ((binSizeMeter < 1) or (binSizeMeter > 9999)):
    retVal |= 4
  if ((binType != 0) and (binType != 1)):
    retVal |= 8
  if (len(pathName) <= 0):
    retVal |= 16
  return retVal

def writeDataJsonGeoObj(geoID, numValInBound, llBound, **kwargs):
  data = {}
  numBinInBound = int(numValInBound / 2)
  data["type"] = "Feature"
  data["geometry"] = {}  ## List
  data["geometry"]["type"] = "Polygon"
  #data["geometry"]["coordinates"] = [[[0] * 2] * numBinInBound]  ## Array; If used, end up same data
  data["geometry"]["coordinates"] = [[[0 for x in xrange(2)] for y in xrange(numBinInBound)]]  ## Array
  cnt = 0
  for i in xrange(0, numValInBound, 2):
    data["geometry"]["coordinates"][0][cnt][0] = llBound[i]
    data["geometry"]["coordinates"][0][cnt][1] = llBound[i+1]
    cnt += 1
  data["properties"] = {}
  data["properties"]["geoid"] = geoID

  for key, value in kwargs.iteritems():
    recordFlag = 1  ## Do not record if value of a key is same as default
    if ((key.lower() == "strokeColor".lower()) and (value.lower() == strokeColorDef.lower())):
      recordFlag = 0
    elif ((key.lower() == "strokeWeight".lower()) and (value == strokeWeightDef)):
      recordFlag = 0
    elif ((key.lower() == "strokeOpacity".lower()) and (value == strokeOpacityDef)):
      recordFlag = 0
    elif ((key.lower() == "fillColorDef".lower()) and (value.lower() == fillColorDef.lower())):
      recordFlag = 0
    elif ((key.lower() == "fillOpacity".lower()) and (value == fillOpacityDef)):
      recordFlag = 0
    if (recordFlag == 1):
      data["properties"][key] = value
  return data

def writeDataJsonGeoStr(geoID, numValInBound, llBound, **kwargs):
  firstFlag = 1
  data = "{\"type\":\"Feature\",\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[["
  for i in xrange(0, numValInBound, 2):
    if (firstFlag != 1):
      data = data + ","
    data = data + "[{0},{1}]".format(llBound[i], llBound[i+1])
    firstFlag = 0
  data = data + "]]},\"properties\":{"
  for key, value in kwargs.iteritems():
    recordFlag = 1  ## Do not record if value of a key is same as default
    if ((key.lower() == "strokeColor".lower()) and (value.lower() == strokeColorDef.lower())):
      recordFlag = 0
    elif ((key.lower() == "strokeWeight".lower()) and (value == strokeWeightDef)):
      recordFlag = 0
    elif ((key.lower() == "strokeOpacity".lower()) and (value == strokeOpacityDef)):
      recordFlag = 0
    elif ((key.lower() == "fillColorDef".lower()) and (value.lower() == fillColorDef.lower())):
      recordFlag = 0
    elif ((key.lower() == "fillOpacity".lower()) and (value == fillOpacityDef)):
      recordFlag = 0
    if (recordFlag == 1):
      if (type(kwargs[key]) == str):
        data = data + "\"{0}\":\"{1}\",".format(key, value)
      else:
        data = data + "\"{0}\":{1},".format(key, value)
  data = data + "\"geoid\":\"{0}\"".format(geoID)
  data = data + "}}"
  return data

def crossUTMZoneDetect(longiMin, longiMax):
  crossZoneFlag = 0
  zoneNumMin = int(math.floor((longiMin + 180.0) / 6) + 1)
  zoneNumMax = int(math.floor((longiMax + 180.0) / 6) + 1)
  if (zoneNumMin != zoneNumMax):
    crossZoneFlag = 1
  #print longiMin, longiMax, zoneNumMin, zoneNumMax, crossZoneFlag  ## Echo print
  return crossZoneFlag, zoneNumMin, zoneNumMax

def getDistHVFromBound(numValInRecBound, llRecBound, zoneNumForce):
  utmBound = convertLLToUTMOneBound(numValInRecBound, llRecBound, zoneNumForce)  ## Convert llRecBound to UTM using the force UTM zone. ## Assume one UTM zone
  utmRecBound = getRecFromBound(numValInRecBound, utmBound)  ## Jan. 25, 2017
  distH, distV = getDistLLRecBound(llRecBound)  ## Get H and V distance from LL rectangular bound
  distHFromUTM, distVFromUTM = getDistUTMRecBound(utmRecBound)  ## Jan. 25, 2017
  #print "dist:", distH, distV, distHFromUTM, distVFromUTM  ## Echo print
  if (distHFromUTM > distH):
    distH = distHFromUTM
  if (distVFromUTM > distV):
    distV = distVFromUTM
  return distH, distV

def getBinsOneLLBoundSameZone(forceZoneFlag, crossZoneFlag, minNorthIn, distVIn, numValInBound, llBound, numValInRecBound, llRecBound, binSizeMeter, binType, zoneNumForce, geojson_file, geoBinBoundMid_file, geoBinBoundMif_file, geoBinCenterMid_file, geoBinCenterMif_file):
  ## Input minNorthIn, distVIn to use lower northing and bigger distance when not force zone and crossZone
  retValTemp, geoID, centerLongi, centerLati, zoneNumTemp = getGeoIDFromLL(llRecBound[0], llRecBound[1], binSizeMeter, binType)
  minEast, minNorth, zoneNumTemp, latiBand = utm.from_latlon(centerLati, centerLongi, zoneNumForce)  ## Get minUTM bin center and get latiBand
  #print minEast, minNorth, zoneNumTemp, latiBand, centerLati, centerLongi, zoneNumForce, geoID, zoneNumTemp  ## Echo print

  firstFlag = 1  ## Init.
  recCnt = 0

  ## Setup stepSizeH, stepSizeV, numStepH, numStepV, offsetH, offsetV, xSeg, ySeg
  distH, distV = getDistHVFromBound(numValInRecBound, llRecBound, zoneNumForce)
  #print minNorthIn, distVIn, minNorth, distV  ## Echo print

  if ((forceZoneFlag == 0) and (crossZoneFlag == 1)):
    if ((minNorthIn >= 0.0) and (distVIn >= 0)):
      if (minNorthIn < minNorth):
        minNorth = minNorthIn
      if (distV < distVIn):
        distV = distVIn

  offsetV = 0.0
  if (binType == 0):
    stepSizeH = binSizeMeter
    stepSizeV = binSizeMeter
    offsetH = binSizeMeter / 2.0
    offsetV = binSizeMeter / 2.0
  else:
    stepSizeH = binSizeMeter / 4.0 * 3.0 * 2.0  ## Avoid duplicate geoID
    stepSizeV = binSizeMeter / 2.0 * math.sin(math.pi / 3.0)
    ySeg = stepSizeV
    xSeg = binSizeMeter / 4.0
    offsetH = xSeg * 3.0
  numStepH = int(math.floor(distH / stepSizeH)) + 2  ## Jan. 25, 2017; 1->2; cross zone should not duplicate
  numStepV = int(math.floor(distV / stepSizeV)) + 6  ## Jan. 25, 2017; 1->6

  if (binType == 1):
    xSegNum = int(math.floor(minEast/offsetH))  ## Move north location if even even or odd odd
    ySegNum = int(math.floor(minNorth / ySeg))
    xSegNumMod2 = xSegNum % 2
    ySegNumMod2 = ySegNum % 2
    if (ySegNumMod2 == 1):
      minNorth -= stepSizeV  ## North always starts with even y
    if (xSegNumMod2 == 1):
      minEast -= offsetH   ## East always starts with odd x
    #print minEast, minNorth, offsetH, ySeg, xSegNum, ySegNum  ## Echo print

  startChkH = 0
  endChkH = numStepH
  if ((forceZoneFlag == 0) and (crossZoneFlag == 1)):  ## Jan. 25, 2017; Need to check some bin boundary to reduce overlapping bin plot when bins in different zones
    startChkH = 10
    endChkH = numStepH - 10  ## Start and end Horizontal 
    if (endChkH < 0):
      endChkH = 0

  #print llRecBound, binType, distH, distV, stepSizeH, stepSizeV, numStepH, numStepV, offsetH, offsetV, xSeg, ySeg  ## Echo print

  ## Step H bin by bin (avoid duplicate geoID), then V
  ##   Check whether a boundary point inside polygon; If inside polygon, record result
  curNorth = minNorth - stepSizeV  ## Init. northing
  for j in xrange(0, numStepV):
    curNorth += stepSizeV          ## Current northing
    curEast = minEast - stepSizeH  ## Init. easting
    if (binType == 1):
      ySegNum = math.floor(curNorth / ySeg)
      if ((ySegNum % 2) == 1):     ## Adjust starting easting (horizontal shift)
        curEast += offsetH
    for i in xrange(0, numStepH):
      curEast += stepSizeH         ## Current easting
      if (binType == 0):           ## Bin boundary in UTM
        numBinBound = 4
        eastingClock, northingClock = getBoundFromCenterSquare(offsetH, offsetV, curEast, curNorth)
      else:
        numBinBound = 6
        eastingClock, northingClock = getBoundFromCenterHexagon(xSeg, ySeg, curEast, curNorth)
      lonClock, latClock = getLLBoundFromUTMBound(numBinBound, eastingClock, northingClock, zoneNumForce, latiBand)  ## Bin boundary in LL; Jan. 25, 2017

      inRegionFlag = 0
      for k in xrange(0, numBinBound):  ## Inside region check; Any bin vertex in region?
         #retValTemp, inRegionFlag = utmPtInRegion(eastingClock[k], northingClock[k], numValInBound, utmBound)  ## Region may distort
         retValTemp, inRegionFlag = llPtInRegion(lonClock[k], latClock[k], numValInBound, llBound)  ## Jan. 25, 2017; Should use LL to check bin inside
         if (inRegionFlag == 1):
           break
      #print j, i, inRegionFlag, numBinBound, eastingClock, northingClock  ## Echo print

      if (inRegionFlag == 1):      ## Record geoID, center, and boundary, and output

        if ((i > endChkH) or (i < startChkH)):  ## Check whether bin shall use next zone coordinates
          if (binType == 0):
            eastT, northT, zoneNumT, latiBandT = utm.from_latlon(latClock[2], lonClock[2])
          else:
            eastT, northT, zoneNumT, latiBandT = utm.from_latlon(latClock[3], lonClock[3])
          if (zoneNumT != zoneNumForce):  ## zoneNum changed
            continue

        if ((forceZoneFlag == 1) and (crossZoneFlag == 1)):  ## Use unique GeoID and center
          latiFromUTM, longiFromUTM = utm.to_latlon(curEast, curNorth, zoneNumForce, latiBand)
          retValTemp, geoID, centerLongi, centerLati, zoneNumTemp = getGeoIDFromLL(longiFromUTM, latiFromUTM, binSizeMeter, binType)
        else:
          curEastUse = curEast
          curNorthUse = curNorth
          if (minNorthIn > 0):  ## zone number changed; May not need since curEast = curEastUse and curNorth = curNorthUse; Test/Debug
            if (binType == 1):
              curEastUse = eastingClock[0] + 2.0 * xSeg
              curNorthUse = northingClock[0]

          geoID, centerLongi, centerLati = getGeoIDFromUTM(curEastUse, curNorthUse, binSizeMeter, binType, zoneNumForce, latiBand)
          #geoID, centerLongi, centerLati = getGeoIDFromUTM(curEast, curNorth, binSizeMeter, binType, zoneNumForce, latiBand)

        #print "getBinsOneLLBoundSameZone():", j, i, minEast, minNorth, curEast, curNorth, curEastUse, curNorthUse, xSeg, ySeg, numBinBound, eastingClock, northingClock, zoneNumForce, latiBand, geoID, centerLongi, centerLati  ## Echo print

        ## Output
        writeDataJsonGeo(geojson_file, firstFlag, geoID, centerLongi, centerLati, numBinBound, lonClock, latClock)
        writeDataBinCenterGeo(geoBinCenterMid_file, geoBinCenterMif_file, geoID, centerLongi, centerLati)
        writeDataBinBoundGeo(geoBinBoundMid_file, geoBinBoundMif_file, geoID, numBinBound, lonClock, latClock)
        firstFlag = 0
        recCnt += 1

        #print j, i, curEast, curNorth, geoID, centerLongi, centerLati  ## Echo print
        #print numBinBound, lonClock, latClock  ## Echo print
      #if (i >= 10):  ## Test/Debug
      #  break
    #if (j >= 2):  ## Test/Debug
    #  break

  return recCnt, minNorth, distV

##-------------------- Export functions -----
def getBinGeoJSONFromGeoID(geoID, **kwargs):
  retStrFlag = 1
  retVal = 0  ## Init.
  #data = {}  ## Uncomment this if retStrFlag == 0
  data = ""   ## Uncomment this if retStrFlag == 1
  centerLongi = 0.0
  centerLati = 0.0
  binSizeMeter = 0
  binType = 0
  numValInBound = 0
  llBound = [0,1,2,3,4,5,6,7,8,9,10,11]

  retVal, numValInBound, llBound, centerLongi, centerLati, binSizeMeter, binType = getLLFromGeoID(geoID)
  if (retVal == 0):
    if (retStrFlag == 1):
      data = writeDataJsonGeoStr(geoID, numValInBound, llBound, **kwargs)
    else:
      data = writeDataJsonGeoObj(geoID, numValInBound, llBound, **kwargs)
    #print llBound, data  ## Echo print
  return retVal, data

def getBinsOneLLBound(numValInBound, llBound, binSizeMeter, binType, pathName, zoneNum = -1, **kwargs):  ## kwargs is a dictionary: for k,v in kwargs.iteritems():
  ## Verify json format: $ python -m json.tool GeoBin.json
  ## http://www.saltycrane.com/blog/2008/01/how-to-use-args-and-kwargs-in-python/: for key in kwargs: print "another keyword arg: %s: %s" % (key, kwargs[key])
  retVal = getBinsOneLLBoundChkPara(numValInBound, llBound, binSizeMeter, binType, pathName)  ## Check input parameters
  if (retVal == 0):  ## May cross zone

    ## Prepare output files; Write file header
    retVal, geojson_file = openFileWMkdir(pathName, "GeoBin.json")
    if (retVal == 0):
      writeHeaderJsonGeo(geojson_file, **kwargs)
    if (retVal == 0):
      createBoundFile(pathName, "GeoBound", numValInBound, llBound)  ## Uncomment if need GeoBound mid/mif
    retValT, geoBinCenterMid_file, geoBinCenterMif_file, geoBinBoundMid_file, geoBinBoundMif_file = openMidMifFileWMkdirGeo(pathName)    ## Uncomment if need GeoBinBound mid/mif
    if ((retVal == 0) and (retValT != 0)):
      retVal = retValT

    if (retVal == 0):
      forceZoneFlag = 0  ## 1 for force zone if zoneNum < 1; 0 for auto-detect dynamically

      ## Get rectangular boundary from llBound; use minLL as force UTM zone and get minLL bin center.
      llRecBound = getRecFromBound(numValInBound, llBound)
      numValInRecBound = 8
      #print numValInRecBound, llRecBound  ## Echo print

      llRecBoundUse = [0] * 8
      for i in xrange(0, numValInRecBound):  ## Init.
        llRecBoundUse[i] = llRecBound[i]

      ## Write a function and call one zone by one zone
      crossZoneFlag, zoneNumMin, zoneNumMax = crossUTMZoneDetect(llRecBound[0], llRecBound[6])  ## Cross zone detection
      if ((zoneNum >= 1) and (zoneNum <= 60)):  ## Input zoneNum valid
        forceZoneFlag = 1
        zoneNumMin = zoneNum
        zoneNumMax = zoneNum
      if (forceZoneFlag == 1):
        zoneNumMax = zoneNumMin

      recCnt = 0
      minNorth = -1.0
      distV = -1.0
      for zoneNumUse in xrange(zoneNumMin, zoneNumMax + 1):
        if (zoneNumMin != zoneNumMax):  ## Need to replace some parts in llRecBoundUse
          if (zoneNumUse != zoneNumMax):
            llRecBoundUse[4] = llRecBoundUse[6] = -180.0 + zoneNumUse * 6.0
          else:
            llRecBoundUse[4] = llRecBoundUse[6] = llRecBound[4]
          if (zoneNumUse != zoneNumMin):
            llRecBoundUse[0] = llRecBoundUse[2] = -180.0 + (zoneNumUse - 1) * 6.0
          else:
            llRecBoundUse[0] = llRecBoundUse[2] = llRecBound[0]
        minNorthIn = minNorth
        distVIn = distV
        recCnt, minNorth, distV = getBinsOneLLBoundSameZone(forceZoneFlag, crossZoneFlag, minNorthIn, distVIn, numValInBound, llBound, numValInRecBound, llRecBoundUse, binSizeMeter, binType, zoneNumUse, geojson_file, geoBinBoundMid_file, geoBinBoundMif_file, geoBinCenterMid_file, geoBinCenterMif_file)
      
      writeFooterJsonGeo(geojson_file, recCnt)
      geoBinCenterMid_file.close()
      geoBinCenterMif_file.close()
      geoBinBoundMid_file.close()
      geoBinBoundMif_file.close()
      geojson_file.close()
  if (retVal > 0):
    retVal *= -1
  return retVal

##-------------------- Test -----
## Function test
retVal = 0
numValInBound = 8
llBound = [-122.51593,37.75312,-122.4993,37.78031,-122.432803,37.795259,-122.44142,37.752214]  ## in region; small region
#llBound = [-122.51593,37.75312,-122.4993,37.78031,-118.432803,37.795259,-118.44142,37.752214]  ## in region; for test cross zone region
binSizeMeter = 100
binType = 1  ## Hexagon
#binType = 0  ## Square
pathName = 'C:\\Users\\wyang.TTSWIRELESS\\Desktop\\MyProjects\\Python\\MyProjects\\GeoID'  ## Path to store GeoBin.json
geoID = '00000000001010010S0000000725200000096535'

## Calling function
args = {"strokeColor": "#FF0000", "binSize": 100}
#retVal = getBinsOneLLBound(numValInBound, llBound, binSizeMeter, binType, pathName, -1, **args)  ## Example for using **args
#retVal = getBinsOneLLBound(numValInBound, llBound, binSizeMeter, binType, pathName)
print 'getBinsOneLLBound():', retVal, ':', numValInBound, llBound, binSizeMeter, binType, pathName  ## Echo print

#data = {}  ## Return JSON object; Uncomment this if retStrFlag == 0 
data = ""   ## Return string; Uncomment this if retStrFlag == 1
retVal, data = getBinGeoJSONFromGeoID(geoID, **args)  ## Return string object by default; can return JSON object
print 'getBinGeoJSONFromGeoID():', retVal, data, ':', geoID  ## Echo print
#print  data["geometry"]["coordinates"][0][1][0], data["geometry"]["coordinates"][0][1][1]  ## Echo print for returning JSON Object

## Load JSON file test
#with open('..\\GeoBinSample.json') as infile:
  #jsonData = json.load(infile)
  #print jsonData
  #print jsonData['features'][0]['geometry']['coordinates']
