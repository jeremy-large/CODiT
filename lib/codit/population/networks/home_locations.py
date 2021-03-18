"""
An spatial attribute for each household
"""

import pandas as pd
import os
import csv
import numpy as np
import random
from codit import share_dir
from codit.population.networks.regions import Ward, LSOA
from codit.population.networks.city_config.city_cfg import AVERAGE_HOUSEHOLD_SIZE
import logging
import geopandas as gpd
import time

DATA_PATH = os.path.join(share_dir(), 'codit', 'data')
COORDINATES_CSV = os.path.join(DATA_PATH, 'city', 'population', 'coordinates.csv')
TYPES_CONSTRAINTS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'types_households_constraints.csv')
FULL_HOME_LIST_CSV = os.path.join(DATA_PATH, 'city', 'population', 'full_home_list.csv')

COORDINATES_WARDS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'coordinates_wards_list.csv')
POPULATION_WARDS_CSV = os.path.join(DATA_PATH, 'city', 'population', 'sample_wards_population.csv')
COORDINATES_LSOA_CSV = os.path.join(DATA_PATH, 'city', 'population', 'coordinates_lsoa_list.csv')
POPULATION_LSOA_CSV = os.path.join(DATA_PATH, 'city', 'population', 'sample_lsoa_population.csv')
WARDS_SHAPEFILE_PATH = os.path.join(DATA_PATH, 'city', 'population', 'Wards_May_2020_Boundaries_UK_BGC.shp')
LSOA_SHAPEFILE_PATH = os.path.join(DATA_PATH, 'city', 'population', 'LSOA_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales.shp')
DEFAULT_DISTRICT_TYPE = 'Ward'

DISTRICT_PARAMETERS = \
    {
        'Ward':
        {
            'intermediary_file': COORDINATES_WARDS_CSV,
            'population_data_file': POPULATION_WARDS_CSV,
            'shape_file': WARDS_SHAPEFILE_PATH,
            'shape_file_columns': ["wd20cd", "wd20nm", "geometry"],
            'population_columns': ['wd20cd', 'wd20nm', 'population'],
            'join_column': 'wd20cd',
            'district_columns': ['wd20cd', 'wd20nm'],
            'output_additional_columns': ['ward_code', 'ward_name']
        },
        'LSOA':
        {
            'intermediary_file': COORDINATES_LSOA_CSV,
            'population_data_file': POPULATION_LSOA_CSV,
            'shape_file': LSOA_SHAPEFILE_PATH,
            'shape_file_columns': ["lsoa11cd", "lsoa11nm", "geometry"],
            'population_columns': ['lsoa11cd', 'lsoa11nm', 'population'],
            'join_column': 'lsoa11cd',
            'district_columns': ['lsoa11cd', 'lsoa11nm'],
            'output_additional_columns': ['lsoa_code', 'lsoa_name']
        }
    }

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
    def __init__(self, lon=None, lat=None, accommodation_type='', ward_code='', ward_name='', lsoa_code='', lsoa_name=''):
        self.coordinate = {'lon': lon, 'lat': lat}
        self.type = accommodation_type
        self.ward = Ward(ward_code, ward_name)
        self.lsoa = LSOA(lsoa_code, lsoa_name)


def get_population_district(district_type = DEFAULT_DISTRICT_TYPE):
    """
    Get Population of each ward in a LA
    :param district_type: district type, 'Ward' or 'LSOA' for now
    :return: return list of [str(pop_ward['ward_code']), str(pop_ward['ward_name']), int(pop_ward['population'])]
    """
    df_population_district = pd.read_csv(DISTRICT_PARAMETERS[district_type]['population_data_file'])
    return df_population_district.to_dict('records')


def count_coords_for_types(coords):
    """
    Count number of coordinates for each building-type from coordinates-building_type list
    The coordinates list requested from Openstreetmap is organized as a list of ['lon','lat','building_type','district_name','district_code'].
    Here I just want to get the number of coordinates for each building_type within the coordinates list,
    e.g. number of houses, number of apartments.
    I also use 'types_households_constraints.csv' to assume a minimum number and maximum number of households for each building-type.
    For example, I assumed the min and max number of households of a house are both 1.
    Number of households' distribution in the map should follow the distribution of each type of building.
    E.g. Apartment and terrace coordinates should have higher density of population.
    :param coords: list of coordinates-building_type pairs
    :return: list of (building_type, count)
    """
    types_counts = []
    for building_type in building_types:
        count = 0
        for coord in coords:
            if coord['building_type'] == building_type:
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


def allocate_households_to_each_building(df_types_average_households, list_coords):
    """
    Use Poisson distribution to randomly allocate specified number of households to each accommodation building, as Poisson
    distribution is discreet non-negative integers, here we use the return from (Possion() + Min number of households
    for that type of accommodation building) as the number of households for each accommodation building
    :param df_types_average_households: df of ['building_type', 'number of buildings for each building type',\
    ('average_num_households of that building type'-'min_households of that building type'), 'min_households of that
    building type']
    :param list_coords: list of coordinates of all accommodation buildings ['lon', 'lat', 'building_type', 'ward_code',
    'ward_name', 'lsoa_code', 'lsoa_name']
    :return: A list of ['lon', 'lat', 'building_type', 'ward_code', 'ward_name', 'lsoa_code', 'lsoa_name',
    'num_of_households']
    """

    homes = pd.DataFrame(list_coords)
    df_result = pd.DataFrame()
    for _, hh_types in df_types_average_households.iterrows():
        if hh_types['number'] > 0:
            list_num_households_per_type = hh_types['average_num_households'] + \
                                           np.random.poisson(hh_types['min_households'], size=hh_types['number'])
            df_temp = homes[homes['building_type'] == hh_types['building_type']]
            df_temp['num_of_households'] = list_num_households_per_type
            df_result = pd.concat([df_result, df_temp])

    return df_result.to_dict('records')


def allocate_homes_to_district(total_h, coords_per_district):
    """
    Allocate homes to wards
    :param total_h: total number of households in the Ward
    :param coords_per_district: The coordinates list of all accommodation buildings ['lon', 'lat', 'building_type', 'ward_code', 'ward_name', 'lsoa_code', 'lsoa_name'] in the district
    :return: a full list of households in a district with info ['lon', 'lat', 'building_type', 'ward_code', 'ward_name', 'lsoa_code', 'lsoa_name']
    """
    logging.info(
        f"number of household in this district is {total_h}, number of coordinates in this district is {len(coords_per_district)}")
    df = generate_average_number_homes_for_building_type(total_h, coords_per_district)
    df['mean_minus_min'] = df['average_num_households'] - df['min_households']
    list_num_households_per_building = allocate_households_to_each_building(df, coords_per_district)

    list_households_info = []
    for num_households_per_building in list_num_households_per_building:
        if int(num_households_per_building['num_of_households']) > 0:
            n_hh = num_households_per_building.pop('num_of_households')
            list_households_info += [num_households_per_building] * int(n_hh)
    return list_households_info


def build_households_home_list():
    """
    :param district_type:  district type, 'Ward' or 'LSOA' for now
    Build a full list of households: ['lon', 'lat', 'building_type'] with 'district_code', 'district_name'
    :return: a full list of ['lon', 'lat', 'building_type', 'district_code', 'district_name']
    """
    df_coordinates_ward = pd.read_csv(DISTRICT_PARAMETERS['Ward']['intermediary_file'])
    df_coordinates_lsoa = pd.read_csv(DISTRICT_PARAMETERS['LSOA']['intermediary_file'])
    df_coordinates = pd.merge(df_coordinates_ward, df_coordinates_lsoa, on=['lon', 'lat', 'building_type'])
    additional_columns = []
    additional_columns += DISTRICT_PARAMETERS['Ward']['output_additional_columns']
    additional_columns += DISTRICT_PARAMETERS['LSOA']['output_additional_columns']
    df_coordinates.loc[:, additional_columns] = df_coordinates.loc[:, additional_columns].replace('', np.nan)
    # Given coordinates outliers only 4-6 for either Wards or LSOA allocations,
    # remove coordinates without either Wards or LSOAs:
    df_coordinates.dropna(inplace=True)
    coords_types = df_coordinates.to_dict('records')
    population_district = get_population_district('Ward')
    list_households_info = []
    for pop_district in population_district:
        tmp_coords_district = []
        for coord_type in coords_types:
            if coord_type.get('allocated', False):
                continue
            if coord_type['ward_code'] == pop_district['wd20cd']:
                tmp_coords_district.append(coord_type)
                coord_type['allocated'] = True
        list_households_info += allocate_homes_to_district(pop_district['population'] / AVERAGE_HOUSEHOLD_SIZE,
                                                           tmp_coords_district)

    df_home_list = pd.DataFrame(list_households_info)[df_coordinates.columns]
    df_home_list.to_csv(FULL_HOME_LIST_CSV, index=False)
    return df_home_list


def get_home_samples(total_h=50000):
    home_specs = []
    df_home_specs = pd.read_csv(FULL_HOME_LIST_CSV)
    home_specs = df_home_specs.values.tolist()
    if len(home_specs) < total_h:
        return home_specs
    else:
        return random.sample(home_specs, total_h)


def generate_average_number_homes_for_building_type(total_h, coords_types):
    """
    Calculate average number of homes in each type of accommodation building for one district
    :param total_h: num of homes in one district
    :param coords_types: list of ['lon', 'lat', 'building_type', 'ward_code', 'ward_name', 'lsoa_code', 'lsoa_name']
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


def allocate_coordinates_to_districts(district_type=DEFAULT_DISTRICT_TYPE):
    """
    Allocate coordinates to geographic districts by examine the shapefile of that district
    :param district_type:  district type, 'Ward' or 'LSOA' for now
    :return: a dataframe of coordinates with respective district name and code, also save the result to intermediary csv file
    """

    # Obtain coordinates.csv
    df_home_list = pd.read_csv(COORDINATES_CSV)
    # Obtain geodataframe from shapefile of all districts
    districts_shapes_gdf_full = gpd.read_file(DISTRICT_PARAMETERS[district_type]['shape_file'])
    districts_shapes_gdf = districts_shapes_gdf_full[DISTRICT_PARAMETERS[district_type]['shape_file_columns']].copy()

    # #### Obtain list of districts names
    sample_districts_names_df = pd.read_csv(DISTRICT_PARAMETERS[district_type]['population_data_file'])

    # #### Pare down districts shapes dataframe into only the relevant districts (ones in Samples)
    sample_districts_shapes_gdf = districts_shapes_gdf.loc[districts_shapes_gdf[DISTRICT_PARAMETERS[district_type]
    ['join_column']].isin(list(sample_districts_names_df[DISTRICT_PARAMETERS[district_type]['join_column']]))]

    # Create geodataframe, same as df_home_list but with a geometry column containing Point objects made from lon/lat
    gdf_home_list = gpd.GeoDataFrame(df_home_list,
                                     geometry=gpd.points_from_xy(df_home_list['lon'], df_home_list['lat']))


    # Creating df_home_district_list, same as df_home_list but includes district_name and district_code, by checking
    # each Leeds district polygon to see if it contains the Point defined by the lon/lat of the home.
    # If no district contains the Point, then the number of outliners added up in number_outliers.


    df_home_district_list = df_home_list.copy()
    new_columns = [['']*2]*len(df_home_district_list.index)
    df_home_district_list[DISTRICT_PARAMETERS[district_type]['output_additional_columns']] = new_columns
    number_outliers = 0
    print_every = 500
    start_time = time.time()
    prev_time = time.time()
    time_list = []
    for home_index, home_row in gdf_home_list.iterrows():
        now_time = time.time()
        time_list.append(now_time - prev_time)
        if home_index % print_every == 0:
            print(f'Processed {home_index} coordinates, {number_outliers} number of coordinates are outliers, {now_time - start_time}')
        prev_time = now_time
        home_pt = home_row["geometry"]
        missing_district = True
        for district_index, district_row in sample_districts_shapes_gdf.iterrows():
            # TODO: this could be materially sped up by making a quick guess of the district
            if district_row["geometry"].contains(home_pt):
                df_home_district_list.loc[home_index, DISTRICT_PARAMETERS[district_type]['output_additional_columns']] = \
                    district_row.loc[DISTRICT_PARAMETERS[district_type]["district_columns"]].values
                missing_district = False
                break
        if missing_district:
            number_outliers += 1

    # Save dataframe with homes and district info to csv file
    sample_homes_districts_df_nogeo = df_home_district_list.drop("geometry", axis=1)
    sample_homes_districts_df_nogeo.to_csv(DISTRICT_PARAMETERS[district_type]['intermediary_file'], index=False)
    return sample_homes_districts_df_nogeo

