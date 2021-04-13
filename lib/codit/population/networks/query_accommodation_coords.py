#!/usr/bin/env python

import overpy # "conda install -c conda-forge overpy" -- a Python Wrapper to access the OpenStreepMap Overpass API
import csv
import time


# building_types are defined for key:building:accommodations at https://wiki.openstreetmap.org/wiki/Key:building
building_types = ["apartments",
                 "bungalow",
                 "cabin",
                 "detached",
                 "dormitory",
                 "farm",
                 "ger",
                 "hotel",
                 "house",
                 "houseboat",
                 "residential",
                 "semidetached_house",
                 "static_caravan",
                 "terrace"]


def request_coords_to_csv(csvfilename, city_area, seconds_sleep):
    """
    Request coordinates of each building type defined in building_types[] in Leeds area from OpenStreetMap, and save
    the results into csv file
    :param csvfilename: to save coordinates results
    :return:
    """
    api = overpy.Overpass()
    coords = []
    for building_type in building_types:
        r = api.query(f"""
        {city_area};
        (nwr["building"="{building_type}"](area);         
        );
        out center;
        """)        
        coords += [(float(node.lon), float(node.lat), building_type) 
                   for node in r.nodes]
        coords += [(float(way.center_lon), float(way.center_lat), building_type) 
                   for way in r.ways]
        coords += [(float(rel.center_lon), float(rel.center_lat), building_type) 
                   for rel in r.relations]   
        time.sleep(seconds_sleep) # leave enough interval between requests to OpenStreetMap server
    header_name = ['lon', 'lat', 'building_type']
    with open(csvfilename, 'w', newline='') as csv_coords_w:
        coords_wr = csv.writer(csv_coords_w)
        coords_wr.writerow(header_name)   
        for coord in coords:
            coords_wr.writerow(coord)
            
            
def get_coords(csvfilename):
    """
    Get Coordinates and building_types from csvfilename
    :param csvfilename: filename of coordinates csv
    :return: list of ['lon','lat','building_type']
    """
    coords = []
    with open(csvfilename, 'r') as csv_coords_f:
        coords_rd = csv.DictReader(csv_coords_f)
        coords += [[float(coord['lon']), float(coord['lat']), str(coord['building_type'])] 
               for coord in coords_rd]
        return coords
