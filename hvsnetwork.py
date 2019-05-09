#!/usr/bin/env python3
"""
HVS Network Mapper
Planning and Transport Research Centre (PATREC)

This script is used to map the HVS Network data to OSM node components. It is
currently a work-in-progress as part of investigating methods to match other
spatial data to OSM components.
"""


__author__ = "Tristan Reed"
__version__ = "0.1.0"


""" Specify the URL for the HVS network. """
HVS_SOURCE = "/Users/trisreed/Downloads/ArchiveToNAS-181017/Tandem_Drive_" + \
    "Concessional_Network_2.1_N2.1_Without_Conditions.geojson"

""" Specify where to read from URL or from File. """
READ_FROM_URL = False


""" Specify the base URL for the OSRM instance. """
OSRM_SOURCE = "https://router.project-osrm.org/"


""" Import required libraries. """
import json, pandas, polyline, requests, time, tqdm


""" Shapely likes to do its own thing. """
from shapely.geometry import shape
from shapely.ops import linemerge


def main():

    """ Check source type and switch. """
    if READ_FROM_URL:

        """ Pull the GeoJSON file from Main Roads / ESRI. """
        print("Retrieving data from Main Roads / ESRI...")
        hvs_data = requests.get(HVS_SOURCE)
        hvs_json = hvs_data.json()
    
    else:

        """ Read it out of the file. """
        print("Retrieving data from file.")
        hvs_data = open(HVS_SOURCE, "r")
        hvs_json = json.loads(hvs_data.read())

    """ Check for a CRS key and alert either way. """
    if ("crs" in hvs_json):
        print("""NOTE: A CRS has been specified. Ensure it is EPSG:4326 (WGS84)
        before relying on the output of this script.""")
    else:
        print("""NOTE: There is no CRS specified in the root element. If the
        file is standards compliant, this means it is in EPSG:4326 (WGS84).
        However, this might not be the case, or it may be incorrectly set on
        each feature.""")

    """ Only care about the 'feature list' so pull that out straight away. If
    you wish to take a subset, specify within the second brackets. """
    hvs_json = hvs_json["features"][0:100]

    """ Create a list for dictionaries for output. """
    return_list = []
    
    """ Iterate over that feature list. """
    for each_feature in tqdm.tqdm(hvs_json):

        """ Pull out the Road ID and Name (for reference). """
        road_id = each_feature["properties"]["ROAD"]
        road_name = each_feature["properties"]["ROAD_NAME"]

        """ Pull out the geographic data for this road. """
        road_geography = shape(each_feature["geometry"])

        """ Merge the lines (hopefully) if a MultiLineString. """
        if (road_geography.geom_type == "MultiLineString"):

            """ Do the Line Merging. """
            road_geography = linemerge(road_geography)

            """ Simplify it for cases of 'dual carriageways'. """
            road_geography = road_geography.simplify(0.1, 
                preserve_topology = False)

            """ Try Line Merging again. """
            road_geography = linemerge(road_geography)

        print(road_geography)

        """ Convert that into a list of the correct format. """
        road_geography = polyline.encode(road_geography.coords, precision = 5)

        """ Generate the URL for the OSRM Matcher. """
        osrm_url = OSRM_SOURCE + "route/v1/driving/polyline(" + \
            road_geography + ")?steps=false&geometries=geojson&" + \
            "overview=full&annotations=true"

        """ Specify which match from OSRM to take (this is mainly here to
        remind me to check it and work out which match is best). """
        chosen_osrm_match = 0

        """ Get the data from OSRM. 'Routes' is the key of interest. """
        osrm_data = requests.get(osrm_url)

        """ Sometimes (I am guessing due to the rate limiting) the service will
        return nothing (well, a 429). If so, go back and do it again. """
        while (osrm_data.status_code == 429):

            """ Get the retry time from the response (well, kind of since
            it doesn't present the right header). """
            retry_time = int(osrm_data.headers['X-Rate-Limit-Interval']) / 2

            """ Wait that amount of time. """
            time.sleep(retry_time)

            """ Try again. """
            osrm_data = requests.get(osrm_url)

        """ Ensure that we get a 200 at this point in time. """
        if (osrm_data.status_code == 200):
            
            """ Continue on, processing the result. """
            osrm_json = osrm_data.json()
            osrm_node_dualist = [leg["annotation"]["nodes"] for leg in \
                osrm_json["routes"][chosen_osrm_match]["legs"]]

            """ Pull out the list of coordinates as well. """
            osrm_node_coordlist = osrm_json["routes"][chosen_osrm_match]\
                ["geometry"]["coordinates"]
            
            """ Put it all together and add to list. """
            return_list.append({"id": road_id, "name": road_name, 
                "node_list": osrm_node_dualist, 
                "coord_list": osrm_node_coordlist})
        
        else:

            """ Inform if this failed. """
            print("Iteration failed with HTTP error code " + \
                str(osrm_data.status_code))
    
    """ Lazy mode: use Pandas to output to convert to a DataFrame to output to
    the CSV format. """
    print("Outputting to CSV...")
    output_df = pandas.DataFrame(return_list)
    output_df.to_csv("hvsnetwork.csv", index = False)


if __name__ == "__main__":

    """ This is executed when run from the command line. """
    main()