import pandas as pd
from codit import share_dir

def read_demographic_data(section, file_name, data_dir=share_dir() / "codit/data/city"):
    """
    :param section: population
    :param file_name: table-8.csv
    :param repo_dir: desired data type
    :return: value according to table
    """
    return pd.read_csv(data_dir / section / file_name, index_col=0)


DEMO_DATA = (read_demographic_data('population', 'table-8.csv')["%"] / 100).to_dict()
ROUNDING = 0.001  # rounding such that sum of rates equals 1

"Averages based on city's Data"
AVERAGE_HOUSEHOLD_SIZE = 2.5
AVERAGE_NUMBER_OF_CHILDREN = 1.6
AVERAGE_STUDENT_HOME_SIZE = 14
AVERAGE_CARE_HOME_SIZE = 100

"Household size percentage with respect to city's Population"
ONE_PERSON_RATE = round(sum(v for k, v in DEMO_DATA.items() if "One person household" in k), 3)  # 1 person: 24 < ages
TWO_PERSON_RATE = round(sum(v for k, v in DEMO_DATA.items() if "No children" in k), 3)  # 2 person: 24 < ages < 65
TWO_SENIOR_PERSON_RATE = DEMO_DATA['All aged 65 and over']  # 2 person household: 64 < ages

CARE_HOME_RATE = 0.0004  # care homes: 64 < ages
OTHER_SENIOR_PERSON_RATE = DEMO_DATA['Other household types: All aged 65 and over'] - CARE_HOME_RATE  # 3 person household: 64 < ages

PAREN_W_DEPENDENT_RATE = DEMO_DATA['Lone parent: Dependent children']  # 1 adult plus ~2.1 Children
FAMILY_W_DEPENDENT_RATE = round(sum(v for k, v in DEMO_DATA.items() if ' dependent children' in k.lower() and 'Lone' not in k), 1)  # 2 adults plus ~2.1 Children

PAREN_W_NON_DEPENDENT_RATE = DEMO_DATA['Lone parent: All children non-dependent']  # 1 adults plus ~2.1 Adult Children
FAMILY_W_NON_DEPENDENT_RATE = round(sum(v for k, v in DEMO_DATA.items() if 'non-dependent' in k.lower() and 'Lone' not in k), 3)  # 2 adults plus ~2.1 Adult Children

STUDENT_HOUSEHOLD_RATE = DEMO_DATA['Other household types: All full-time students']  # student residents: 19 < age < 27
OTHER_HOUSEHOLD_RATE = DEMO_DATA['Other household types: Other'] + ROUNDING  # other residents: 24 < ages < 65, 1 < size < 5

"Working Age"
MINIMUM_WORKING_AGE = 20
MAXIMUM_WORKING_AGE = 65

"Secondary School Student Age"
MINIMUM_CLASS_AGE = 12
MAXIMUM_CLASS_AGE = 18

"Weights of Age Group Distribution"
OVER_25_WEIGHT = ['25'] * 23 + ['35'] * 19 + ['45'] * 18 + ['55'] * 16 + ['65'] * 13 + ['75'] * 8 + ['85'] * 3  # 24 < ages
ADULT_WEIGHT = ['25'] * 30 + ['35'] * 25 + ['45'] * 24 + ['55'] * 21  # 24 < ages < 65
PARENT_WEIGHT = ['25'] * 30 + ['35'] * 25
GROWNUP_PARENT_WEIGHT = ['45'] * 24 + ['55'] * 21
CHILD_WEIGHT = ['0'] * 52 + ['10'] * 48  # 0 < ages < 20
SENIOR_WEIGHT = ['65'] * 34 + ['75'] * 32 + ['85'] * 34  # 64 < ages
STUDENT_WEIGHT = ['20'] * 100  # 19 < age < 27
