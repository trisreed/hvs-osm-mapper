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
HVS_SOURCE = "https://opendata.arcgis.com/datasets/" +\
    "9eddd767132d46aebdef328ec79573d3_46.geojson"


""" Specify the base URL for the OSRM instance. """
OSRM_SOURCE = "https://router.project-osrm.org/"


""" Import required libraries. """
import pandas, requests, time, tqdm


def main():

    """ Pull the GeoJSON file from Main Roads / ESRI. """
    print("Retrieving data from Main Roads / ESRI...")
    hvs_data = requests.get(HVS_SOURCE)
    hvs_json = hvs_data.json()

    """ Check for a CRS key and alert either way. """
    if ("crs" in hvs_json):
        print("""NOTE: A CRS has been specified. Ensure it is EPSG:4326 (WGS84)
        before relying on the output of this script.""")
    else:
        print("""NOTE: There is no CRS specified in the root element. If the
        file is standards compliant, this means it is in EPSG:4326 (WGS84).
        However, this might not be the case, or it may be incorrectly set on
        each feature.""")

    """ Only care about the 'feature list' so pull that out straight away. """
    hvs_json = hvs_json["features"]

    """ Create a list for dictionaries for output. """
    return_list = []
    
    """ Iterate over that feature list. """
    for each_feature in tqdm.tqdm(hvs_json):

        """ Pull out the Road ID and Name (for reference). """
        road_id = each_feature["properties"]["ROAD"]
        road_name = each_feature["properties"]["ROAD_NAME"]

        """ Pull out the geographic data for this road. """
        road_geography = each_feature["geometry"]["coordinates"]

        """ Convert that into a String of the correct format. """
        """ @todo ensure both OSRM and the RVS are in same CRS. """
        road_geography = ";".join([",".join(str(x) for x in coord) for coord \
            in road_geography])

        """ Generate the URL for the OSRM Matcher. """
        osrm_url = OSRM_SOURCE + "route/v1/driving/" + road_geography + \
            "?steps=false&geometries=polyline&overview=full&annotations=true"

        """ Specify which match from OSRM to take (this is mainly here to
        remind me to check it and work out which match is best). """
        chosen_osrm_match = 0

        """ Get the data from OSRM. 'Routes' is the key of interest. """
        osrm_data = requests.get(osrm_url)
        print(osrm_data)

        """ Sometimes (I am guessing due to the rate limiting) the service will
        return nothing (well, a 429). If so, go back and do it again. """
        while (osrm_data.status_code != 200):
            time.sleep(0.5)
            osrm_data = requests.get(osrm_url)
        
        """ Continue on, processing the result. """
        osrm_json = osrm_data.json()
        osrm_node_dualist = [leg["annotation"]["nodes"] for leg in \
            osrm_json["routes"][chosen_osrm_match]["legs"]]
        
        """ Put it all together and add to list. """
        return_list.append({"id": road_id, "name": road_name, 
            "node_list": osrm_node_dualist})

        """ The OSRM online service is globally limited to 5999 requests 
        a minute. Generally, network latency means we aren't hitting it too 
        much. But, to be safe, we will sleep for half a second. """
        # time.sleep(0.5)
    
    """ Lazy mode: use Pandas to output to convert to a DataFrame to output to
    the CSV format. """
    print("Outputting to CSV...")
    output_df = pandas.DataFrame(return_list)
    output_df.to_csv("output.csv", index = False)


if __name__ == "__main__":

    """ This is executed when run from the command line. """
    main()