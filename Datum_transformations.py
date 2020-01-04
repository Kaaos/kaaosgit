import math


# # # # # # # # # # # # # # # # # # # # # # # # # # #
#   Parameters:                                     #
#       Origin shifts (cX, cY, cZ):   Meters        #
#       Rotations (rX, rY, rZ):       Arc seconds   #
#       Scale (s):                    PPM           #
# # # # # # # # # # # # # # # # # # # # # # # # # # #

# Bursa-Wolf:
    # Finnish (old) KKJ datum - EUREF-FIN (parameters from JHS197 Appendix 6)
kkj_euref_fin = {"cX":-96.0617, "cY":-82.4278, "cZ":-121.7535, "rX":-4.80107, "rY":-0.34543, "rZ":1.37646,   "s":1.49640 }
euref_fin_kkj = {"cX":96.0610,  "cY":82.4298,  "cZ":121.7485,  "rX":4.80109,  "rY":0.34546,  "rZ": -1.37645, "s":-1.49651}

    # ITRF2014 to ETRS89 in different epochs, Baltic Sea area
    # See https://www.lantmateriet.se/contentassets/bbc47979dfef4f338e3c4f8b139da2fb/simplified-transformations-between-itrf2014-and-etrs89-for-maritime-applications.pdf
ITRF2014_etrs89_2015_5 = {"cX":0.73384, "cY":0.88328, "cZ":-0.62780, "rX":-0.029958, "rY":0.014279, "rZ":0.028179, "s":-0.00958}
ITRF2014_etrs89_2020_5 = {"cX":0.93597, "cY":1.12966, "cZ":-0.79088, "rX":-0.038216, "rY":0.019882, "rZ":0.034665, "s":-0.01310}
ITRF2014_etrs89_2021_5 = {"cX":0.97637, "cY":1.17886, "cZ":-0.82343, "rX":-0.039864, "rY":0.021001, "rZ":0.035961, "s":-0.01381}
ITRF2014_etrs89_2022_5 = {"cX":1.01673, "cY":1.22806, "cZ":-0.85601, "rX":-0.041514, "rY":0.022120, "rZ":0.037257, "s":-0.01452}


# # # # # # # # # # # # # # # # # #
#   Ellipsoids:                   #
#       a  = Semimajor axis (m)   #
#       b  = Semiminor axis (m)   #
#       e2 = First excentricity   #
# # # # # # # # # # # # # # # # # #
international_1924 = {"a":6378388, "b":6356911.9462, "e2":None}
grs80 = {"a":6378137, "b":6356752.3141, "e2":0.00669438002290}
wgs84 = {"a":6378137, "b":6356752.314245, "e2":None}


# # # # # # # # #
#   Functions:  #
# # # # # # # # #

# Converts geodetic coordinates to 3D cartesian coordinates:
def geodetic_to_cartesian(ellipsoid, lat, lon, height):
    # Ellipsoid parameters:
    a  = ellipsoid["a"]     # Semimajor axis
    b  = ellipsoid["b"]     # Semiminor axis

    cos_latitude  = math.cos(lat * (math.pi / 180))
    sin_latitude  = math.sin(lat * (math.pi / 180))
    cos_longitude = math.cos(lon * (math.pi / 180))
    sin_longitude = math.sin(lon * (math.pi / 180))

    n = a**2 / (math.sqrt((a**2 * cos_latitude**2) + (b**2 * sin_latitude**2)))

    xcoord = (n + height) * cos_latitude * cos_longitude
    ycoord = (n + height) * cos_latitude * sin_longitude
    zcoord = ((b**2 / a**2 * n) + height) * sin_latitude

    return(xcoord, ycoord, zcoord)


# Converts 3D cartesian coordinates to geodetic coordinates:
def cartesian_to_geodetic(ellipsoid, xcoord, ycoord, zcoord):
    # Ellipsoid parameters:
    a  = ellipsoid["a"]     # Semimajor axis
    b  = ellipsoid["b"]     # Semiminor axis

    # First excentricity, calculate if not given in papers:
    if ellipsoid["e2"] is None:
        e2 = (a**2 - b**2) / a**2
    else:
        e2 = ellipsoid["e2"]

    # Longitude:
    longitude = math.atan2(ycoord, xcoord) * 180 / math.pi

    # 1st approximation of latitude:
    tan_latitude = zcoord / ((1 - e2) * math.sqrt(xcoord**2 + ycoord**2))
    lat_radians  = math.atan(tan_latitude)
    latitude = lat_radians * 180 / math.pi

    # 1st approximation of N:
    cos_lat_radians = math.cos(lat_radians)
    sin_lat_radians = math.sin(lat_radians)
    n = a**2 / math.sqrt((a**2 * cos_lat_radians**2) + (b**2 * sin_lat_radians**2))

    # 1st approximation of h:
    height = (math.sqrt((xcoord**2 + ycoord**2) / cos_lat_radians)) - n

    guess_h = 0.0
    count = 0

    while (math.fabs(guess_h - height) > 0.0000000001):
        guess_h = height
        tan_latitude = zcoord / ((1 - (e2 * (n / (n + height)))) * math.sqrt(xcoord**2 + ycoord**2))
        lat_radians = math.atan(tan_latitude)
        latitude = lat_radians * 180 / math.pi
        n = a**2 / math.sqrt(a**2 * math.cos(lat_radians)**2 + b**2 * math.sin(lat_radians)**2)
        height = ((math.sqrt(xcoord**2 + ycoord**2)) / math.cos(lat_radians)) - n
        count += 1

    return (latitude, longitude, height, "Iterations: " + str(count))


# Converts arc seconds to radians:
def arcsec_to_rad(sec):
    return sec / (60 * 60 * 180 / math.pi)


# Bursa-Wolf 7-parameter transform
# Transforms 3D cartesian coordinates
# Input: (x, y, z) coordinates, parameter dictionary
    #   |Xb|             | 1     rZ   -rY|   |Xa|   |dx|
    #   |Yb| = (1 + m) * |-rZ    1     rX| . |Ya| + |dy|
    #   |Zb|             | rY   -rX    1 |   |Za|   |dz|
def bursawolf(xyz, params):
    Xa = xyz[0]
    Ya = xyz[1]
    Za = xyz[2]

    dx = params["cX"]
    dy = params["cY"]
    dz = params["cZ"]
    s = params["s"]

    rX = arcsec_to_rad(params["rX"])
    rY = arcsec_to_rad(params["rY"])
    rZ = arcsec_to_rad(params["rZ"])

    Xb = (1 + s * 10**-6) * (Xa + rZ * Ya - rY * Za)  + dx
    Yb = (1 + s * 10**-6) * (-rZ * Xa + Ya + rX * Za) + dy
    Zb = (1 + s * 10**-6) * (rY * Xa - rX * Ya + Za)  + dz

    return (Xb, Yb, Zb)


# Helmert 7-parameter transform
# Transforms 3D cartesian coordinates
# Input: (x, y, z) coordinates, parameter dictionary
    #   |Xb|             |1      -rZ   rY|   |Xa|   |dx|
    #   |Yb| = (1 + m) * |rZ      1   -rX| . |Ya| + |dy|
    #   |Zb|             |-rY    rX    1 |   |Za|   |dz|
def helmert(xyz, params):
    Xa = xyz[0]
    Ya = xyz[1]
    Za = xyz[2]

    dx = params["cX"]
    dy = params["cY"]
    dz = params["cZ"]
    s = params["s"]

    rX = arcsec_to_rad(params["rX"])
    rY = arcsec_to_rad(params["rY"])
    rZ = arcsec_to_rad(params["rZ"])

    Xb = (1 + s * 10**-6) * (Xa - rZ * Ya + rY * Za)   + dx
    Yb = (1 + s * 10**-6) * (rZ * Xa + Ya - rX * Za)   + dy
    Zb = (1 + s * 10**-6) * (-rY * Xa + rX * Ya + Za)  + dz

    return (Xb, Yb, Zb)


# # # # # # # # # # # # # # # # # #
#   Main (under construction)     #
# # # # # # # # # # # # # # # # # #

    # For example Geodetic (input) --> Cartesian 3D --> Bursa-wolf --> Geodetic (output)

# Random tests:
bursawolfresult = bursawolf((3565285.0000, 855949.0000, 5201383.0000), ITRF2014_etrs89_2022_5)

print("\nCartesian input: 65.432112345, 24.987654321, 987.456789")
result_cartesian = geodetic_to_cartesian(grs80, 65.432112345, 24.987654321, 987.456789)
result = cartesian_to_geodetic(grs80, result_cartesian[0], result_cartesian[1], result_cartesian[2])
print("Cartesian 3D:", result_cartesian)
print("Back to geodetic:", result)
