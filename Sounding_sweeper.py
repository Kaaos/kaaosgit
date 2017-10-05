# -*- coding: utf-8 -*-

# Removes too shallow soundings from the point data
# Fairway areas must be mechanically swept to make sure not hard targets are removed from the data!
# Other restrictions for possible use cases exist, use good judgement!
# Experimental, use at your own risk

# Load packages (install first):
from shapely.geometry import Point
import geopandas as gpd
import Tkinter as Tk  # File IO-dialog
from tkFileDialog import askopenfilename  # File IO-dialog


# Function for fairway areas shapefile input:
def input_fairwayareas_path():
    Tk.Tk().withdraw()  # Keep the root window from appearing
    filetype = [('ESRI Shapefile', '.shp')]
    info = 'Select fairway areas shapefile:'
    try:
        filepath = askopenfilename(filetypes=filetype, initialdir='C:\Users', title=info)  # show an 'Open' dialog box and return the path to the selected file
    except Exception:
        filepath = None
    return filepath


# Function for points file input:
def input_points():
    Tk.Tk().withdraw()
    filetype = [('Ascii XYZ', '.xyz')]
    info = 'Select XYZ points file:'
    try:
        filepath = askopenfilename(filetypes=filetype, initialdir='C:\Users', title=info)  # show an 'Open' dialog box and return the path to the selected file
    except Exception:
        filepath = None
    return filepath


# Function for output (point-) file paths parsing:
def parse_outputfilepaths(input_path):
    corrected_points_path = input_path.split(".")[0] + "_corrected.xyz"
    tracking_list_path = input_path.split(".")[0] + "_tracking_list.xyz"
    return corrected_points_path, tracking_list_path


# Function for EPSG CRS code input:
def epsg_input():
    print 'Enter EPSG code for point data CRS:'
    while True:
        epsg = raw_input('')
        if (epsg == ''):
            print 'No EPSG code defined. Exiting.'
            exit()
        try:
            epsg = int(epsg)
            break
        except Exception:
            print "Illegal argument. Enter an (integer type) EPSG code."
    return epsg


# Function to read in fairwayareas:
def read_fairways(path):
    try:
        fairway = gpd.read_file(path)  # NOTICE: CRS must match ASCII points CRS for intersection to work properly!
        deepsweep = max(fairway["SDEPFWYARE"])  # Get deepest swept depth
        epsg = fairway.crs  # Get dataset CRS as EPSG code
    except Exception:
        print "Error reading fairway shapefile. Exiting."
        exit()

    return fairway, deepsweep, epsg


# Function to reproject vector data to given CRS:
def reproject_data(data, point_epsg):
    try:
        print "\nReprojecting data to: ", point_epsg
        data = data.to_crs(epsg=point_epsg)
        print "Reprojection OK."
    except Exception:
        print "Error: Reprojection failed."
        exit()


# Function to erase new files that include errors:
def deleteContent(cleanfile):
    cleanfile.seek(0)
    cleanfile.truncate()


# Function to check the correction outcome and erase files and exit if errors were found
def check_correction(loop, corrected, tracklist, points):
    if (loop is False):  # Was looping not clean, came up with errors?
        print "Something went wrong. Emptying new files and exiting."
        deleteContent(corrected)
        deleteContent(tracklist)
        exit()


# Point iterator function:
def iterate_points(points, fairwayareas, deepest_sweep, corrected_out, tracklist_out):
    try:
        print "\nIterating over points file.. (please be patient as this might take a while)"
        for p in points:
            point_coordinates = p.split(" ")
            if (abs(float(point_coordinates[2])) >= deepest_sweep):
                corrected_out.write(p)  # Point depth >= deepest sweep, can be written right away to make processing faster
            else:
                writerFunction(fairwayareas, p, point_coordinates, corrected_out, tracklist_out)  # Point directed to further processing
        return True

    except Exception:
        return False


# Function to check, correct and write points:
def writerFunction(fairway, p, point_coordinates, corrected_out, tracklist_out):
    try:
        var_point = Point(float(point_coordinates[0]), float(point_coordinates[1]))
        var_depth = abs(float(point_coordinates[2]))

        for i in range(len(fairway)):   # Loop trough fairway areas
            sweep_depth = fairway.loc[i]["SDEPFWYARE"]
            sweep_geometry = fairway.loc[i]["geometry"]

            if (sweep_geometry.intersects(var_point)):  # Point on fairway area?
                if (var_depth < sweep_depth):   # Depth shallower than swept depth?

                    tracklist_out.write(p)  # Original points are stored on a tracking list
                    point_coordinates[2] = str(0.0 - sweep_depth)  # Set point depth to swept depth
                    row = point_coordinates[0] + " " + point_coordinates[1] + " " + point_coordinates[2] + "\n"  # Define row (single point in XYZ)
                    corrected_out.write(row)    # Write corrected point
                    print("Conflicting point detected: Point Z = " + str(var_depth) + ", swept depth = " + str(sweep_depth))
                    return  # Point written, return

                else:
                    corrected_out.write(p)  # Point OK --> write
                    return  # Point written, return

        corrected_out.write(p)  # Point not on fairways --> OK --> write
        return  # Point written, return

    except Exception:  # Error protection
        print "Error: error writing points to a file. Exiting."
        exit()


# # # # # # # #
# Main method #
# # # # # # # #

# Get points file, parse output filepaths:
points_fp = input_points()  # Get original points filepath
corrected_fp, tracklist_fp = parse_outputfilepaths(points_fp)  # Parse output filepaths
point_crs = epsg_input()  # Get point data EPSG

# Read in fairways in ESRI shapefile format:
fairway_fp = input_fairwayareas_path()  # Get path
fairways, deepest_sweep, fairway_epsg = read_fairways(fairway_fp)  # Get file pointer, deepest swepth depth and EPSG code

# Reproject fairway areas to match points CRS:
reproject_data(fairways, point_crs)


# Open files (also takes care of closing the files in all cases):
with open(points_fp, "r") as points, \
        open(corrected_fp, "a") as corrected_out, \
        open(tracklist_fp, "a") as tracklist_out:

    # Correct the points, write output files and check if everything went ok:
    correction_successful = iterate_points(points, fairways, deepest_sweep, corrected_out, tracklist_out)
    check_correction(correction_successful, corrected_out, tracklist_out, points)  # If errors were found, output files will be empty

    # In case of success:
    print "\nSweeping successful! Check new files: "
    print corrected_fp
    print tracklist_fp, "\n"
