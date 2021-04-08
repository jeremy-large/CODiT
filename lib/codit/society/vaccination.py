import numpy as np
import random
import logging

from codit import share_dir
import pandas as pd

VACCINE_DATA = share_dir() / "codit" / "data" / "city" / "population" / "COVID-19_Vaccine_update_Report -25_Mar_2021.csv"


def vaccinate(people, proportion, maker='AstraZeneca'):
    to_vaccinate = int(np.round(len(people) * proportion))
    for p in random.sample(people, to_vaccinate):
        p.vaccinate_with(maker)


def msoa_inhabitants(people, msoa, min_age=None, max_age=None):
    if min_age:
        people = (p for p in people if p.age >= min_age)
    if max_age:
        people = (p for p in people if p.age <= max_age)
    return [p for p in people if p.home.lsoa.features['msoa11cd'] == msoa]


def msoas(people):
    return sorted(list({p.home.lsoa.features['msoa11cd'] for p in people}))


def vaccinate_per_table(people):
    vaccine_rates = pd.read_csv(VACCINE_DATA).set_index('MSOA Code').T.to_dict()

    for msoa in msoas(people):
        ages = ((80, None, "80 yrs and over"), (50, 79, "50_to_79_yrs"))
        for min_age, max_age, desc in ages:
            residents = msoa_inhabitants(people, msoa, min_age=min_age, max_age=max_age)
            percent = vaccine_rates[msoa][desc]
            vaccinate(residents, percent * 0.01)
            logging.debug(f"Vaccinated {percent} % of {msoa} aged >= {min_age} and <= {max_age}")
