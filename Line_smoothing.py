# Line smoothing for WKT geometries

import math


# Visvalingam algorithm
# See https://en.wikipedia.org/wiki/Visvalingam–Whyatt_algorithm
def visvalingam(wkt, epsilon):
    line = geometryparser(wkt)
    run = True

    # Line with less than 3 vertices cannot be simplified:
    if (len(line) < 3):
        return None

    while run is True:
        min_area = float("inf")         # Placeholder
        min_area_index = None           # Placeholder

        # Loop through all vertices:
        for i in range(len(line) - 2):  # -2 due to need of +2 vertices to create triangle
            vertex_index = i + 1        # Vertex "responsible for area" - middle vertex of three
            area = get_area(line[i], line[i+1], line[i+2])
            if (area < min_area):
                min_area = area
                min_area_index = i + 1  # Vertex to possibly be removed
        if (min_area < epsilon and min_area_index is not None and len(line) >= 3):
            line = pop_vertex(line, min_area_index)
        else:
            run = False

    return geometryparser_wkt(line)     # Return WKT


# Get triangle area (used in Visvalingam algorithm)
def get_area(p1, p2, p3):
    return math.fabs(0.5 * (((p2[0] - p1[0]) * (p3[1] - p1[1])) - ((p3[0] - p1[0]) * (p2[1] - p1[1]))))


# Remove vertex from line
#   Removes a certain vertex from line. The vertex to be removed is indicated by index number.
#   - Inputs: a line and vertex index number
#   - Output: line with vertex removed
def pop_vertex(line, index):
    ret = []
    for i in range(len(line)):
        if (i == index):
            continue
        else:
            ret.append(line[i])
    return tuple(ret)


# Douglas-Peucker algorithm
def douglas_peucker(wkt, epsilon):
    # TODO
    pass


# Parses WKT geometries to point tuples ((x,y), (x,y), (x,y), ...)
def geometryparser(wkt):
    ret = None
    if (wkt[:10].upper() == "LINESTRING"):  # Only linestrings allowed (needed)
        tmp_array = []
        ret = wkt[10:].strip("() ").replace("(", "").replace(")", "")
        for i in ret.split(","):
            tmp = i.strip().split(" ")
            tmp_array.append((float(tmp[0]), float(tmp[1])))
        ret = tuple(tmp_array)
    else:                                   # Other geometry types are not allowed, terminate
        print("Invalid geometry type. Exiting.")
        exit()
    return ret


# Parses WKT strings from point tuples
#   - Input: tuple of vertices ((x,y), (x,y), (x,y), ...)
#   - Output: WKT Linestring, See https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry 
def geometryparser_wkt(vertices):
    wkt = "LINESTRING ("                    # No need for other geometry types
    for i in range(len(vertices)):
        wkt += str(vertices[i][0]) + " " + str(vertices[i][1]) + ", "
    wkt = wkt[:-2]
    wkt += ")"
    return wkt


#
# # Tests:
#


line_orig = "LINESTRING (30 10, 10 30, 40 40)"
line_orig = "LineString (0.02358596078098546 0.09620633145582302, 0.02375448281602302 0.09603780942078546, 0.02426004892113571 0.09536372128063521, 0.0247656150262484 0.09435258907040983, 0.025692486218955 0.09544798229815399, 0.02586100825399256 0.09418406703537227, 0.02645083537662403 0.09401554500033471, 0.02754622860436819 0.09393128398281592, 0.0302425811649692 0.09283589075507176, 0.03251762863797631 0.09182475854484638, 0.03327597779564535 0.0917404975273276, 0.0362251134088027 0.09081362633462101, 0.03858442189932858 0.08980249412439562, 0.04338729989789914 0.09131919243973369, 0.0513920965621834 0.08921266700176415, 0.05206618470233365 0.09013953819447075, 0.05417271014030319 0.08980249412439562, 0.05509958133300979 0.09022379921198953, 0.05602645252571639 0.09013953819447075, 0.0577959338936108 0.09106640938717735, 0.05939689322646766 0.09317293482514688, 0.0605765474717306 0.09334145686018445, 0.06133489662939964 0.09519519924559765, 0.06293585596225648 0.09603780942078546, 0.06285159494473769 0.09696468061349206, 0.0641997712250382 0.09907120605146161, 0.06453681529511335 0.0999980772441682, 0.06495812038270724 0.10100920945439358, 0.06546368648781994 0.10311573489236311, 0.06580073055789507 0.10480095524273875, 0.06605351361045139 0.10623339254055804, 0.06605351361045139 0.10800287390845245, 0.0656322085228575 0.11078348748657225, 0.06436829326007576 0.11255296885446667, 0.06125063561188086 0.11347984004717326, 0.05899506163220557 0.11347908643171864, 0.0559421915081976 0.11524932141506768, 0.05172914063225852 0.1151650603975489, 0.05054948638699558 0.1151650603975489, 0.04591513042346259 0.1151650603975489, 0.04246042870519254 0.11432245022236108, 0.04043816428474178 0.11558636548514281, 0.03740476765406565 0.11524932141506768, 0.0362251134088027 0.11541784345010524, 0.03361302186572047 0.11457523327491742, 0.02998979811241286 0.11457523327491742, 0.02864162183211235 0.11398540615228596, 0.02746196758684941 0.11364836208221082, 0.02746196758684941 0.11364836208221082, 0.02619805232406769 0.11255296885446667, 0.02619805232406769 0.11255296885446667, 0.02619805232406769 0.11255296885446667, 0.0247656150262484 0.10994087731138444, 0.02265908958827886 0.10859270103108393, 0.02257482857076008 0.10665469762815195, 0.02341743874594789 0.10345277896243825, 0.02299613365835398 0.09974529419161185, 0.02341743874594789 0.09831285689379257, 0.02493413706128596 0.09747024671860476)"
tolerance = 0.003 ** 2

print("Line originally: ", line_orig)
print("\nSimplified geometry: ", visvalingam(line_orig, tolerance), "\n\nTolerance: ", tolerance, "\n")
