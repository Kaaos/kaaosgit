#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
* Reads ESRI Shapefile header information and prints it on the screen
* Shapefile header contains information about geometry type, file length
* and bounding coordinates.
*/

char *get_geometry(int type_n) {
    switch (type_n) {
        case 0:
            return "Null shape";
        case 1:
            return "Point";
        case 3:
            return "Polyline";
        case 5:
            return "Polygon";
        case 8:
            return "MultiPoint";
        case 11:
            return "PointZ";
        case 13:
            return "PolylineZ";
        case 15:
            return "PolygonZ";
        case 18:
            return "MultiPointZ";
        case 21:
            return "PointM";
        case 23:
            return "PolylineM";
        case 25:
            return "PolygonM";
        case 28:
            return "MultiPointM";
        case 31:
            return "MultiPatch";
    }
    return NULL;
}

int main(void) {
    int len = 1000;
    char filepath[len];
    int headerlen = 100; 
    char *header = malloc(headerlen);   // Shapefile header is always 100 bytes

    printf("Enter full filepath to shapefile (e.g. /users/jesus/desktop/test.shp): \n");
    fgets(filepath, len, stdin);

    len = strlen(filepath);
    filepath[len-1] = '\0';

    if (filepath[len-4] != 's' || filepath[len-3] != 'h' || filepath[len-2] != 'p') {
        printf("Invalid filename extension - File is not a shapefile. Exiting.\n");
        free(header);           // Free allocated heap memory
        exit(0);
    }

    FILE *f = fopen(filepath, "r");

    if (!f) {
        printf("\nFile read error. Exiting.\n");
        free(header);           // Free allocated memory
        exit(0);
    }   else {
        printf("\nFile read successful.\n\n");
    }   

    for (int i = 0; i < headerlen; i++) {
        header[i] = fgetc(f);   // Read bytes 0-99 from shapefile (header)
    }

    // File code & file length, Big Endian:
    int filecode = (((header[0] & 0xff) << 24) | ((header[1] & 0xff) << 16) | ((header[2] & 0xff) << 8) | ((header[3] & 0xff)));
    int file_len = (((header[24] & 0xff) << 24) | ((header[25] & 0xff) << 16) | ((header[26] & 0xff) << 8) | ((header[27] & 0xff)));
    file_len *= 2; // Length in bytes

    // Version & Geometry type, Little Endian:
    int version = (((header[31] & 0xff) << 24) | ((header[30] & 0xff) << 16) | ((header[29] & 0xff) << 8) | ((header[28] & 0xff)));
    int geometry_type = (((header[35] & 0xff) << 24) | ((header[34] & 0xff) << 16) | ((header[33] & 0xff) << 8) | ((header[32] & 0xff)));

    // Bounding box:
    double min_x, min_y, max_x, max_y;
    memcpy(&min_x, &header[36], sizeof(min_x));
    memcpy(&min_y, &header[44], sizeof(min_y));
    memcpy(&max_x, &header[52], sizeof(max_x));
    memcpy(&max_y, &header[60], sizeof(max_y));

    // Min & Max Z:
    double min_z, max_z;
    memcpy(&min_z, &header[68], sizeof(min_z));
    memcpy(&max_z, &header[76], sizeof(max_z));

    // Min & Max M:
    double min_m, max_m;
    memcpy(&min_m, &header[84], sizeof(min_m));
    memcpy(&max_m, &header[92], sizeof(max_m));

    if (filecode != 9994) {
        printf("Incorrect filecode - File is not a shapefile. Exiting.\n");
        free(header);   // Free allocated memory
        fclose(f);      // Close file
        exit(0);
    }   else {
        printf("Filecode: \t%d - Shapefile filetype verified.\n", filecode);
    }

    printf("File length: \t%d bytes\n", file_len);
    printf("Version: \t%d\n", version);
    printf("Geometry: \t%s", get_geometry(geometry_type));

    printf("\nBounding box: \t(%f, %f) - (%f, %f)\n", min_x, min_y, max_x, max_y);
    printf("Z range: \t%f - %f\n", min_z, max_z);
    printf("M range: \t%f - %f\n\n", min_m, max_m);

    free(header);   // Free allocated memory
    fclose(f);      // Close file
    
    return 1;
}
