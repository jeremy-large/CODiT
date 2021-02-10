import random
import numpy as np
import logging

from codit.population.population import FixedNetworkPopulation
from codit.population.networks import household_workplace
from codit.population.networks.city_config.city_cfg import MINIMUM_WORKING_AGE, MAXIMUM_WORKING_AGE, MAXIMUM_CLASS_AGE, MINIMUM_CLASS_AGE, AVERAGE_HOUSEHOLD_SIZE
from codit.population.networks.city_config.typical_households import build_characteristic_households
# Import home module
from codit.population.networks.home import Home, build_households_home_list

EPHEMERAL_CONTACT = 0.1  # people per day


class CityPopulation(FixedNetworkPopulation):
    def reset_people(self, society):
        """
        Override reset_people() to allow the new attribute person.home in CityPopulation can be saved when reset the
        population according to different type of society
        :param society:
        :return:
        """
        for person in self.people:
            person.__init__(society, config=society.cfg.__dict__, name=person.name, home=person.home)

    def fix_cliques(self, encounter_size):
        """
        :param encounter_size: not used
        :return:
        """
        static_cliques = build_city_cliques(self.people)
        logging.info(f"Adding {len(static_cliques)} permanent contact groups")
        dynamic_cliques = FixedNetworkPopulation.fix_cliques(self, EPHEMERAL_CONTACT)
        logging.info(f"Adding {len(dynamic_cliques)} ephemeral contact pairs")
        return static_cliques + dynamic_cliques


def build_city_cliques(people):
    """
    :param people: a list of population.covid.PersonCovid() objects
    :return: a list of little sets, each is a 'clique' in the graph, some are households, some are workplaces
    each individual should belong to exactly one household and one workplace
    for example: [{person_0, person_1, person_2}, {person_0, person_10, person_54, person_88, person_550, person_270}]
    - except not everyone is accounted for of course
    """
    households = build_households(people)
    report_size(households, 'households')

    classrooms = build_class_groups(people)

    working_age_people = [p for p in people if MINIMUM_WORKING_AGE < p.age < MAXIMUM_WORKING_AGE]
    teachers = random.sample(working_age_people, len(classrooms))
    classrooms = [clss | {teachers[i]} for i, clss in enumerate(classrooms)]
    report_size(classrooms, 'classrooms')

    care_homes = [h for h in households if is_care_home(h)]
    carers = assign_staff(care_homes, working_age_people)

    working_age_people = list(set(working_age_people) - set(teachers) - set(carers))
    random.shuffle(working_age_people)
    workplaces = build_workplaces(working_age_people)
    report_size(workplaces, 'workplaces')

    return households + workplaces + classrooms + care_homes


def is_care_home(home):
    return min([p.age for p in home]) >= MAXIMUM_WORKING_AGE and len(home) > 20


def assign_staff(care_homes, working_age_people, staff=5):
    carers = set()
    for home in care_homes:
        home_carers = set(random.sample(working_age_people, staff))
        home |= home_carers
        carers |= home_carers
    report_size(care_homes, 'care_homes')
    return carers


def report_size(care_homes, ch):
    logging.info(f"{len(care_homes)} {ch} of mean size {np.mean([len(x) for x in care_homes]):2.2f}")


def build_class_groups(people):
    classrooms = []
    for kids_age in range(MINIMUM_CLASS_AGE, MAXIMUM_CLASS_AGE+1):
        schoolkids = [p for p in people if p.age == kids_age]
        random.shuffle(schoolkids)
        classrooms += build_workplaces(schoolkids, classroom_size=30)
    logging.info(f"Only putting children >{MINIMUM_CLASS_AGE} years old into classrooms.")
    return classrooms


def build_households(people):
    """
    :param people: a list of population.covid.PersonCovid() objects
    :return: a list of households, where households are a list of person objects. now with an assigned age.
    """
    n_individuals = len(people)
    assigned = 0
    households = []
    num_h = int(n_individuals / AVERAGE_HOUSEHOLD_SIZE)
    household_examples = build_characteristic_households(num_h)
    # create num_h of homes
    homes_examples = build_households_home_list(num_h)
    logging.info(f"There are {len(homes_examples)} households generated for accommodation buildings")

    while assigned < n_individuals:
        ages = next_household_ages(household_examples)
        size = len(ages)
        # randomly pick up a home from list of homes
        home_specification = next_household_home(homes_examples)

        if assigned + size > n_individuals:
            ages = ages[:n_individuals - assigned - size]
            size = len(ages)

        hh = []
        for j, age in enumerate(ages):
            indiv = people[j + assigned]
            indiv.age = age
            # Initialise Home instance with (coordinates and building_type) to each person's home attribute within the population
            indiv.home = Home(*home_specification)

            hh.append(indiv)
        households.append(set(hh))
        assigned += size

    return households


def next_household_ages(household_list):
    """
    :param: complete list of households
    :return: randomly select a type of household from a distribution suitable to City,
    and return the list of the ages of the people in that household
    """
    return random.choice(household_list)


def build_workplaces(people, classroom_size=-1):
    """
    :param people: lets for now let these be a list of N population.covid.PersonCovid() objects
    :return: a list of workplaces, where workplaces are a list of person objects.
    """
    n_individuals = len(people)
    assigned = 0
    workplaces = []
    while assigned < n_individuals:
        if classroom_size > 0:
            size = 30
        else:
            size = next_workplace_size()

        if assigned + size >= n_individuals:
            size = n_individuals - assigned

        assert size > 0

        hh = people[assigned: assigned + size]
        workplaces.append(set(hh))
        assigned += size

    return workplaces


def next_workplace_size():
    return random.choice(household_workplace.WORKPLACE_SIZE_REPRESENTATIVE_EXAMPLES)


def next_household_home(homes_examples):
    """
    Randomly pick up a ['lon', 'lat', 'building_type'] from homes list
    :param: homes_examples
    :return: one home ['lon', 'lat', 'building_type']
    """
    return random.choice(homes_examples)

