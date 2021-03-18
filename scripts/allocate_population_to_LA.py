# !/usr/bin/env python

"""
Script to clear any pending alerts in the background.
"""
import argparse
import sys
from codit.population.networks import query_accommodation_coords
from codit.population.networks.city_config.city_cfg import city_paras
from codit.population.networks.home_locations import build_households_home_list, allocate_coordinates_to_districts, \
    COORDINATES_CSV

CITY_OBSERVE = 'Leeds'
DISTRICT_WARD = 'Ward'
DISTRICT_LSOA = 'LSOA'

parser = argparse.ArgumentParser()

parser.add_argument("--city", type=str, default=None,
                    help="name of the area for coordinates enquiries")
parser.add_argument("--extract_coordinates", action='store_true', default=False,
                    help="query the coordinates of accommodation buildings")
parser.add_argument("--allocate_coordinates_to_wards", action='store_true', default=False,
                    help="allocate coordinates of buildings to wards")
parser.add_argument("--allocate_coordinates_to_lsoa", action='store_true', default=False,
                    help="allocate coordinates of buildings to LSOA")
parser.add_argument("--create_full_homes_list", action='store_true', default=False,
                    help="allocate households into the accommodation buildings in wards")


args = parser.parse_args()


def main():
    if args.extract_coordinates:
        if args.city is not None:
            city_name = args.city
        else:
            city_name = CITY_OBSERVE
        query_accommodation_coords.request_coords_to_csv(COORDINATES_CSV, city_paras[city_name]['area_str'])

    if args.allocate_coordinates_to_wards:
        allocate_coordinates_to_districts(DISTRICT_WARD)

    if args.allocate_coordinates_to_lsoa:
        allocate_coordinates_to_districts(DISTRICT_LSOA)

    if args.create_full_homes_list:
        build_households_home_list()

    sys.exit()


if __name__ == '__main__':
    main()


