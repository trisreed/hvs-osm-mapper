#!/usr/bin/env python3
"""
RVA Network Mapper
Planning and Transport Research Centre (PATREC)

This script is used to map the RVA Network data to OSM components.
"""


__author__ = "Tristan Reed"
__version__ = "0.1.0"


""" Specify the URL for the RVA network. """
RVA_SOURCE = "https://opendata.arcgis.com/datasets/9eddd767132d46aebdef328ec79573d3_46.geojson"


""" Specify the base URL for the OSRM instance. """
OSRM_SOURCE = "https://router.project-osrm.org/"


""" Import required libraries. """
import pandas, requests, tqdm


def main():

    """ Pull the GeoJSON file from Main Roads / ESRI. Only care about the 
    'feature list' so pull that out straight away. """
    print("Retrieving data from Main Roads / ESRI...")
    rva_data = requests.get(RVA_SOURCE)
    """ @note For testing I am limiting this to the first two feature(s). """
    rva_json = rva_data.json()["features"][0:2]

    """ Create a list for dictionaries for output. """
    return_list = []
    
    """ Iterate over that feature list. """
    for each_feature in tqdm.tqdm(rva_json):

        """ Pull out the Road ID and Name (for reference). """
        road_id = each_feature["properties"]["ROAD"]
        road_name = each_feature["properties"]["ROAD_NAME"]

        """ Pull out the geographic data for this road. """
        road_geography = each_feature["geometry"]["coordinates"]

        """ Convert that into a String of the correct format. """
        road_geography = ";".join([",".join(str(x) for x in coord) for coord \
            in road_geography])

        """ Generate the URL for the OSRM Matcher. """
        osrm_url = OSRM_SOURCE + "route/v1/driving/" + road_geography + \
            "?steps=false&geometries=polyline&overview=full&annotations=true"

        """ Get the data from OSRM. 'Routes' is the key of interest. """
        """ @note There will be multiple matches. Take the first, for now. """
        osrm_data = requests.get(osrm_url)
        osrm_json = osrm_data.json()
        osrm_node_dualist = [leg["annotation"]["nodes"] for leg in \
            osrm_json["routes"][0]["legs"]]
        
        """ Put it all together and add to list. """
        return_list.append({"id": road_id, "name": road_name, 
            "node_list": osrm_node_dualist})

        """ @note the OSRM online service is globally limited to 5999 requests 
        a minute. Generally, network latency means we aren't hitting it too 
        much. But, be aware! """
    
    """ Lazy mode: use Pandas to output to CSV. """
    print("Outputting to CSV...")
    output_df = pandas.DataFrame(return_list)
    output_df.to_csv("output.csv", index = False)


if __name__ == "__main__":

    """ This is executed when run from the command line. """
    main()