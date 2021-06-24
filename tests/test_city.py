import numpy as np

ALL_TIME_DAYS = 15

from codit.society import UKSociety
from codit.population.population import Population
from codit.population.networks.city import build_households
from codit.population.networks.city import build_class_groups
from codit.population.networks.city import is_care_home
from codit.population.networks.city_config import city_cfg as cfg
from codit.population.networks.city_config import typical_households as thh

POP_SIZE = 23000


def setup_population():
    return Population(POP_SIZE, UKSociety())


def setup_households(people):
    return build_households(people)  # creates households & sets ages


def test_pop():
    pop = setup_population()
    assert len(pop.people) == POP_SIZE


def test_classroom_age():
    """
     - (1) MIN class age must be MINIMUM_CLASS_AGE
     - (2) MAX class age must be MAXIMUM_CLASS_AGE
     - (3) Ages of students in classroom must all be equal
    """
    pop = setup_population()
    setup_households(pop.people)
    classrooms = build_class_groups(pop.people)
    ages = [pop.census[s].age for room in classrooms for s in room]

    assert min(ages) == cfg.MINIMUM_CLASS_AGE
    assert max(ages) == cfg.MAXIMUM_CLASS_AGE
    assert all(pop.census[p].age == cfg.MINIMUM_CLASS_AGE for p in classrooms[0])


def test_care_homes():
    """
     - (1) MIN care home age must be MAXIMUM_WORKING_AGE
    """
    pop = setup_population()
    houses = build_households(pop.people)
    care_homes = [h for h in houses if is_care_home(h, pop.census)]
    ages = [pop.census[s].age for room in care_homes for s in room]

    assert min(ages) == cfg.MAXIMUM_WORKING_AGE


def test_house_size():
    """
     - (1) normal houses should build houses of size; house_size
    """
    houses = thh.house(10, cfg.SENIOR_WEIGHT, house_size=3)
    mean = np.mean([len(home) for home in houses])

    assert mean == 3