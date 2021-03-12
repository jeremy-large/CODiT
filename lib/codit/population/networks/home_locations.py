"""
An spatial attribute for each household
"""

import pandas as pd
import os
import csv
import numpy as np
import random
from codit import share_dir
from codit.population.networks.regions import Ward
from codit.population.networks.city_config.city_cfg import AVERAGE_HOUSEHOLD_SIZE
import logging

DATA_PATH = os.path.join(share_dir(), 'codit', 'data')
COORDINATES_CSV = os.path.join(DATA_PATH, 'city', 'population', 'coordinates.csv')
TYPES_CONSTRAINTS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'types_households_constraints.csv')
FULL_HOME_LIST_CSV = os.path.join(DATA_PATH, 'city', 'population', 'full_home_list.csv')
COORDINATES_WARDS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'coordinates_wards_list.csv')
POPULATION_WARDS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'sample_wards_population.csv')

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

multiple_households_building_types = [
    "apartments",
    "residential",
    "terrace"
]


class Home:
    def __init__(self, lon=None, lat=None, accommodation_type='', ward_code='', ward_name=''):
        self.coordinate = {'lon': lon, 'lat': lat}
        self.type = accommodation_type
        self.ward = Ward(ward_code, ward_name)


def get_coords(csvfilename):
    """
    Get coordinates and building_type from previous queries to OpenStreetMap
    :param csvfilename: csv file that stores the coordinates and building_type
    :return: return list of [float(coord['lon']), float(coord['lat']), str(coord['building_type']),
                                                    str(coord['ward_name']), str(coord['ward_code'])]
    """
    coords = []
    with open(csvfilename, 'r') as csv_coords_f:
        coords_rd = csv.DictReader(csv_coords_f)
        coords += [
            [float(coord['lon']), float(coord['lat']), coord['building_type'].strip(), coord['ward_name'].strip(),
             coord['ward_code'].strip()] for coord in coords_rd]
        return coords


def get_population_wards(csvfilename):
    """
    Get Population of each ward in a LA
    :param csvfilename: csv file that stores the ward_name ward_code and population
    :return: return list of [str(pop_ward['ward_code']), str(pop_ward['ward_name']), int(pop_ward['population'])]
    """
    population_wards = []
    with open(csvfilename, 'r') as csv_pop_ward_f:
        pop_ward_rd = csv.DictReader(csv_pop_ward_f)
        population_wards += [
            [str(pop_ward['ward_code']).strip(), str(pop_ward['ward_name']).strip(), int(pop_ward['population'])]
            for pop_ward in pop_ward_rd]
        return population_wards


def count_coords_for_types(coords):
    """
    Count number of coordinates for each building-type from coordinates-building_type list
    The coordinates list requested from Openstreetmap is organized as a list of ['lon','lat','building_type','ward_name','ward_code'].
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


def allocate_households_to_each_building(list_types_average_households, list_coords):
    """
    Use Poisson distribution to randomly allocate specified number of households to each accommodation building, as Poisson
    distribution is discreet non-negative integers, here we use the return from (Possion() + Min number of households
    for that type of accommodation building) as the number of households for each accommodation building
    :param list_types_average_households: list of ['building_type', 'number of buildings for each building type',\
    ('average_num_households of that building type'-'min_households of that building type'), 'min_households of that building type']
    :param list_coords: list of coordinates of all accommodation buildings with building_type and their ward_name, ward_code
    :return: full list of ['lon', 'lat', 'building_type', 'ward_name', 'ward_code', 'num_of_households'] for all the accommodation buildings
    """

    df_coords_types = pd.DataFrame(list_coords, columns=['lon', 'lat', 'building_type', 'ward_name', 'ward_code'])

    df_result = pd.DataFrame()

    for types_average_households in list_types_average_households:
        if types_average_households[1] > 0:
            list_num_households_per_type = list(types_average_households[3] + np.random.poisson(
                types_average_households[2], size=types_average_households[1]))
            df_temp = pd.DataFrame(df_coords_types[df_coords_types['building_type'] == types_average_households[0]])
            df_temp['num_of_households'] = list_num_households_per_type
            df_result = pd.concat([df_result, df_temp])

    return df_result.values.tolist()


def allocate_homes_to_wards(total_h, coords_per_ward):
    """
    Allocate homes to wards
    :param total_h: total number of households in the Ward
    :param coords_per_ward: The coordinates list of all accommodation buildings ['lon', 'lat', 'building_type', 'ward_name', 'ward_code'] in the Ward
    :return: a full list of households in a Ward with info ['lon', 'lat', 'building_type', 'ward_name', 'ward_code']
    """
    logging.info(
        f"number of household in this ward is {total_h}, number of coordinates in this ward is {len(coords_per_ward)}")
    df_types_constraints_households = generate_average_number_homes_for_building_type(total_h, coords_per_ward)
    list_types_average_households = list(
        zip(df_types_constraints_households['building_type'], df_types_constraints_households['number'],
            df_types_constraints_households['average_num_households'] - df_types_constraints_households[
                'min_households'],
            df_types_constraints_households['min_households']))
    list_num_households_per_building = allocate_households_to_each_building(list_types_average_households,
                                                                            coords_per_ward)

    list_households_info = []
    for num_households_per_building in list_num_households_per_building:
        if int(num_households_per_building[5]) > 0:
            list_households_info += [num_households_per_building[:5]] * int(num_households_per_building[5])
    return list_households_info


def build_households_home_list():
    """
    Build a full list of households: ['lon', 'lat', 'building_type','ward_name', 'ward_code']
    :return: a full list of ['lon', 'lat', 'building_type', 'ward_name', 'ward_code']
    """
    coords_types = get_coords(COORDINATES_WARDS_CSV)
    population_wards = get_population_wards(POPULATION_WARDS_CSV)
    list_households_info = []
    for pop_ward in population_wards:
        tmp_coords_ward = []
        for coord_type in coords_types:
            if coord_type[4] == pop_ward[0]:
                tmp_coords_ward += [[*coord_type]]
        list_households_info += allocate_homes_to_wards(pop_ward[2] / AVERAGE_HOUSEHOLD_SIZE, tmp_coords_ward)

    df_home_list = pd.DataFrame(list_households_info, columns=['lon', 'lat', 'building_type', 'ward_name', 'ward_code'])
    df_home_list.to_csv(FULL_HOME_LIST_CSV, index=False)
    return df_home_list


def get_home_samples(total_h=50000):
    home_specs = []
    with open(FULL_HOME_LIST_CSV, 'r') as csv_homes_f:
        home_specs_rd = csv.DictReader(csv_homes_f)
        home_specs += [[float(home_spec['lon']),
                        float(home_spec['lat']),
                        str(home_spec['building_type']),
                        str(home_spec['ward_code']),
                        str(home_spec['ward_name'])] for home_spec
                       in home_specs_rd]
        if len(home_specs) < total_h:
            return home_specs
        else:
            return random.sample(home_specs, total_h)


def generate_average_number_homes_for_building_type(total_h, coords_types):
    """
    Calculate average number of homes in each type of accommodation building for one ward
    :param total_h: num of homes in one ward
    :param coords_types: list of ['lon', 'lat', 'building_type', 'ward_name', 'ward_code']
    :return: dataframe with columns=['building_type','number', 'average_num_households', 'min_households']
    """
    types_counts = count_coords_for_types(coords_types)
    df_types_constraints_households = merge_building_types_constraints_to_accommodations(types_counts,
                                                                                         TYPES_CONSTRAINTS_CSV)
    aver_num_households = (df_types_constraints_households['min_households'] + df_types_constraints_households[
        'max_households']) / 2
    df_types_constraints_households['average_num_households'] = aver_num_households
    init_total_households = np.sum(df_types_constraints_households['number'] * df_types_constraints_households['min_households'])
    total_unallocated_households = total_h - init_total_households
    if total_unallocated_households > 0:
        num_households_in_multi_reside_building_list = []
        unallocated_average_households_list=[]
        df_temp = df_types_constraints_households[df_types_constraints_households['building_type'].isin(multiple_households_building_types)]
        num_households_in_multi_reside_building_list = df_temp['number'] * df_temp['average_num_households']
        total_households_in_multi_reside_building = np.sum(num_households_in_multi_reside_building_list)
        percent_households_in_multi_reside_building_list = num_households_in_multi_reside_building_list / \
                                                           total_households_in_multi_reside_building

        df_temp['unallocated_households'] = percent_households_in_multi_reside_building_list * total_unallocated_households
        for building_type in multiple_households_building_types:
            index_all_types = df_types_constraints_households['building_type'] == building_type
            index_temp = df_temp['building_type'] == building_type
            df_types_constraints_households.loc[index_all_types, 'average_num_households'] = \
                df_types_constraints_households.loc[index_all_types, 'min_households'] + \
                df_temp.loc[index_temp, 'unallocated_households'] / df_temp.loc[index_temp, 'number']
        index_inf = ~np.isfinite(df_types_constraints_households['average_num_households'])
        df_types_constraints_households.loc[index_inf, 'average_num_households'] = 0
    else:
        df_types_constraints_households['average_num_households'] = df_types_constraints_households['min_households']
    df_types_constraints_households.drop('max_households', axis=1, inplace=True)
    return df_types_constraints_households
