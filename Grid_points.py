# Grids ASCII XYZ points to a raster file. Not final, missing inputs, checks and options.
# Assumes point data to be in projected CRS and coordinate (x,y) units to be meters.
# Valid data uses <space> as a delimiter and has an order of x y z:
"""
Valid data sample (WGS84 UTM 37S):
315352.45 9661052.71 5148.87
315432.85 9661052.64 5212.63
315253.44 9661053.20 5096.3
315487.97 9661082.98 5277.64
...
"""

import math
import numpy as np
from osgeo import gdal, osr

# Inputs missing (will maybe make them later, maybe not):
# Input filename/-path (checks needed), export filename/-path, projection information, cell size X&Y, method (affects also nodata value!)
# User can of course change all this manually even in this version.


# Read in the data (ascii xyz):
points = open(R"/Users/Topi/Desktop/koe/gridpisteet.xyz", "r")
data = points.read().splitlines()
points.close()


# Calculate and print bounding box:
#   Set initial values for borders:
min_x = float(data[0].split(' ')[0])
max_x = float(data[0].split(' ')[0])
min_y = float(data[0].split(' ')[1])
max_y = float(data[0].split(' ')[1])
n_points = 0  # Point count

# Loop trough all points:
for i in data:
    n_points += 1  # Get point count in the same go
    if(float(i.split(' ')[0]) < min_x):
        min_x = float(i.split(' ')[0])
    elif(float(i.split(' ')[0]) > max_x):
        max_x = float(i.split(' ')[0])
    elif(float(i.split(' ')[1]) < min_y):
        min_y = float(i.split(' ')[1])
    elif(float(i.split(' ')[1]) > max_y):
        max_y = float(i.split(' ')[1])

# Print information about the dataset:
print "\nBounding box (min x,min y - max x, max y): ", min_x, min_y, "-", max_x, max_y
print "\nPoint count: ", n_points
print "Area: ", round(((max_x - min_x) * (max_y - min_y) / 1000000), 3), "km^2"
print "Point density: ", round(n_points / ((max_x - min_x) * (max_y - min_y)), 5), "p/m^2"


# Define cell size in meters:
size_x = 50
size_y = 50


# Match origin to cellsize, even boundries:
origin_x = math.floor(min_x / size_x) * size_x
origin_y = math.floor(min_y / size_y) * size_y

# Top right corner coordinates:
topright_x = math.ceil(max_x / size_x) * size_x
topright_y = math.ceil(max_y / size_y) * size_y


print "\nMatched grid extent in", size_x, "*", size_y, "(m) grid cells:"
print "Bottom left corner coordinates (x,y):", origin_x, origin_y
print "Top right corner coordinates (x,y):", topright_x, topright_y

# Grid dimensions (cells):
cells_x = int((topright_x - origin_x) / size_x)
cells_y = int((topright_y - origin_y) / size_y)
print "\nGrid dimensions (x * y): ", cells_x, "*", cells_y
print "Total:", cells_x * cells_y, "cells"

delta_x = min_x - origin_x
delta_y = min_y - origin_y
print "Origin replacement (m): (x,y) ", delta_x, delta_y


# Create a new array, all cells filled with nodata (-9999):
array = np.full((cells_y, cells_x), -9999, dtype=np.float_)


# Loop trough points, calculate their indexes in the array and fill array cells:
for i in data:
    # Get point coordinates:
    x = float(i.split(" ")[0])
    y = float(i.split(" ")[1])
    z = float(i.split(" ")[2])

    # Calculate array indexes for the points:
    indeksi_x = int(math.floor((x + delta_x - min_x) / size_x))
    indeksi_y = int(math.floor(0 - ((y + delta_y - min_y) / size_y)))  # "Upside down" - starts at the topmost row

    # Fill array according to selection (for now just highest elevation):
    if(array[indeksi_y][indeksi_x] < z):
        array[indeksi_y][indeksi_x] = z

    # Another option, calculate points in each grid cell:
    # array[int(indeksi_y)][int(indeksi_x)] += 1


# Export array as a GeoTIFF raster file:
proj = osr.SpatialReference()
proj.ImportFromEPSG(32737)  # Projection from EPSG, must be asked

geotransform = ([origin_x, size_x, 0, topright_y, 0, -size_y])

driver = gdal.GetDriverByName("GTiff")
filename = R"/Users/Topi/Desktop/max_elevation_50m_grid.tif"

outdata = driver.Create(filename, array.shape[1], array.shape[0], 1, gdal.GDT_Float32)  # 1 band only
outband = outdata.GetRasterBand(1)
outband.SetNoDataValue(-9999)
outband.WriteArray(array)
outdata.SetGeoTransform(geotransform)
outdata.SetProjection(proj.ExportToWkt())
outdata = None  # Close dataset

print "\nRaster file created successfully. Exiting.\n"
