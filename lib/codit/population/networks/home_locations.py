"""
An spatial attribute for each household
"""

import pandas as pd
import os
import csv
import numpy as np
import random
from codit import share_dir

DATA_PATH = os.path.join(share_dir(), 'codit', 'data')
COORDINATES_CSV = os.path.join(DATA_PATH, 'city', 'population', 'coordinates.csv')
TYPES_CONSTRAINTS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'types_households_constraints.csv')
COORDINATES_NUM_HOUSEHOLDS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'coordinates_num_households.csv')
FULL_HOME_LIST_CSV = os.path.join(DATA_PATH, 'city', 'population', 'full_home_list.csv')

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


class Home:
    def __init__(self, lon=0.0, lat=0.0, accommodation_type=''):
        self.coordinate = {'lon': lon, 'lat': lat}
        self.type = accommodation_type


def get_coords(csvfilename):
    """
    Get coordinates and building_type from previous queries to OpenStreetMap
    :param csvfilename: csv file that stores the coordinates and building_type
    :return: return list of [float(coord['lon']), float(coord['lat']), str(coord['building_type'])]
    """
    coords  = []
    with open(csvfilename, 'r') as csv_coords_f:
        coords_rd = csv.DictReader(csv_coords_f)
        coords += [[float(coord['lon']), float(coord['lat']), str(coord['building_type'])]
               for coord in coords_rd]
        return coords


def count_coords_for_types(coords):
    """
    Count number of coordinates for each building-type from coordinates-building_type list
    The coordinates list requested from Openstreetmap is organized as a list of ['lon','lat','building_type'].
    Here I just want to get the number of coordinates for eacy building_type within the coordinates list,
    e.g. number of houses, number of apartments.
    I also use 'types_households_constraints.csv' to assume a minimum number and maximum number of households for each building-type.
    For example, I assumed the min and max number of households of a house are both 1.
    The min number of households in an apartment is 20, while max number of households in an apartment is 100.
    Number of households' distribution in the map should follow the distribution of each type of building.
    E.g. Apartment and terrace coordinates should have higher density of population.
    :param coords: list of coordinates-building_type pairs
    :return: list of (building_type, count)
    """
    types_counts = []
    for building_type in building_types:
        count = 0
        for coord in coords:
            if coord[2] == building_type:
                count += 1
        types_counts += [(building_type, count)]
    return types_counts


def merge_building_types_constraints_to_accommodations(types_count_list, types_constraints_csv):
    """
    merge manually-set assumed constraints to Min-Max number of households for each type of accommodations with the
    building_type-count list
    :param types_count_list: list of building_type-count
    :param types_constraints_csv: csv filename that contains preset assumed constraints to Min-Max number of households for each type of accommodations
    :return: inner merged pandas.DataFrame
    """
    df_types_count = pd.DataFrame(types_count_list, columns=['building_type', 'number'])
    df_types_constraints = pd.read_csv(types_constraints_csv)
    return pd.merge(df_types_count, df_types_constraints, on="building_type", how="inner")


def allocate_households_to_each_building(num_of_households, list_types_average_households, list_coords):
    """
    If there's a previously saved csv file, then directly use the previously generated full list in the csv file
    to save time.
    Use Poisson distribution to randomly allocate specified number of households to each accommodation building, as Poisson
    distribution is discreet non-negative integers, here we use the return from (Possion() + Min number of households
    for that type of accommodation building) as the number of households for each accommodation building

    :param num_of_households: Total number of households to be allocated
    :param list_types_average_households: list of ['building_type', 'number of buildings for each building type',\
    ('average_num_households of that building type'-'min_households of that building type'), 'min_households of that building type']
    :param list_coords: list of coordinates of all accommodation buildings with building_type
    :return: full list of ['lon', 'lat', 'building_type', 'num_of_households'] for all the accommodation buildings
    while saving the full list to csv file
    """
    if os.path.isfile(COORDINATES_NUM_HOUSEHOLDS_CSV):
        df_result = pd.read_csv(COORDINATES_NUM_HOUSEHOLDS_CSV)
    else:
        valid = 0
        df_coords_types = pd.DataFrame(list_coords, columns=['lon', 'lat', 'building_type'])
        while valid != num_of_households:
            df_result = pd.DataFrame()
            list_num_households = []
            for types_average_households in list_types_average_households:
                list_num_households = list(types_average_households[3] + np.random.poisson(types_average_households[2],
                                                                                           size=types_average_households[
                                                                                               1]))
                df_temp = pd.DataFrame(df_coords_types[df_coords_types['building_type'] == types_average_households[0]])
                df_temp['num_of_households'] = list_num_households
                df_result = pd.concat([df_result, df_temp])
            valid = np.sum(df_result['num_of_households'])

        df_result.to_csv(COORDINATES_NUM_HOUSEHOLDS_CSV, index=False)
    return df_result.values.tolist()


def build_households_home_list(total_h=50000):
    """
    Build a list of total_h households: ['lon', 'lat', 'building_type']
    :param total_h: total number of households
    :return: a full list of ['lon', 'lat', 'building_type']
    """
    coords_types = get_coords(COORDINATES_CSV)
    types_counts = count_coords_for_types(coords_types)
    df_types_constraints_households = merge_building_types_constraints_to_accommodations(types_counts, TYPES_CONSTRAINTS_CSV)

    aver_num_households = (df_types_constraints_households['min_households'] + df_types_constraints_households['max_households']) / 2
    df_types_constraints_households['average_num_households'] = aver_num_households
    init_total_households = np.sum(df_types_constraints_households['number'] * aver_num_households)
    index_apartments = df_types_constraints_households['building_type']=='apartments'
    remaining_households_in_apartments = total_h - (init_total_households - df_types_constraints_households.loc[index_apartments, 'average_num_households'] *
                                                    df_types_constraints_households.loc[index_apartments, 'number'])
    df_types_constraints_households.loc[index_apartments, 'average_num_households'] = remaining_households_in_apartments\
                                                                                      / df_types_constraints_households.loc[index_apartments, 'number']
    df_types_constraints_households.drop('max_households', axis=1, inplace=True)

    list_types_average_households = list(
        zip(df_types_constraints_households['building_type'], df_types_constraints_households['number'],
            df_types_constraints_households['average_num_households'] - df_types_constraints_households['min_households'],
            df_types_constraints_households['min_households']))
    list_num_households_per_building = allocate_households_to_each_building(total_h, list_types_average_households, coords_types)
    list_households_info = []
    for num_households_per_building in list_num_households_per_building:

        if int(num_households_per_building[3]) > 0:
            list_households_info += [num_households_per_building[:3]] * int(num_households_per_building[3])
    df_home_list = pd.DataFrame(list_households_info, columns=['lon', 'lat', 'building_type'])
    df_home_list.to_csv(FULL_HOME_LIST_CSV, index=False)
    return df_home_list


def get_home_samples(total_h=50000):
    home_specs = []
    with open(FULL_HOME_LIST_CSV, 'r') as csv_homes_f:
        home_specs_rd = csv.DictReader(csv_homes_f)
        home_specs += [[float(home_spec['lon']), float(home_spec['lat']), str(home_spec['building_type'])] for home_spec
                       in home_specs_rd]
        if len(home_specs) < total_h:
            return home_specs
        else:
            return random.sample(home_specs, total_h)


