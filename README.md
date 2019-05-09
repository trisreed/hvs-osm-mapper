# HVS to OSM Mapper

This script attempts to map the HVS network to OSM path components. The steps
taken are:

1. Download the GeoJSON of the network from the MRWA Open Data repository;
2. Extract each feature and iterate over it;
3. Convert the LineString(s) that make up the feature into a sequence of
   coordinates (in the format expected by OSRM);
4. Call the online OSRM server's `match` function to determine a path that
   matches the coordinates on the OSM network (using a HMM approach);
5. Filter the result to get a list of lists corresponding to the OSM nodes
   traversed to achieve the path;
6. Output to `output.csv`.

This script is currently a work-in-progress as part of a research project with
other researchers.

## Contact

Please contact Tristan Reed, GitHub username 'trisreed', for any queries or to
be passed on to the other researchers.