import random
import numpy as np
import logging
from collections import defaultdict

from codit.population.population import FixedNetworkPopulation, Population
from codit.population.networks import household_workplace
from codit.population.networks.city_config.city_cfg import MINIMUM_WORKING_AGE, MAXIMUM_WORKING_AGE, MAXIMUM_CLASS_AGE, MINIMUM_CLASS_AGE, AVERAGE_HOUSEHOLD_SIZE
from codit.population.networks.city_config.typical_households import build_characteristic_households
from codit.population.networks.home_locations import Home, get_home_samples

EPHEMERAL_CONTACT = 0.1  # people per day
WITHIN_BUILDING_CONTACT = 0.75


class CityPopulation(FixedNetworkPopulation):
    def __init__(self, n_people, society, person_type=None, lockdown_config=None):
        Population.__init__(self, n_people, society, person_type=person_type)
        self.households, self.workplaces, self.classrooms, self.care_homes, self.buildings = build_city_structures(self.people)
        self.set_structure(society, lockdown_config=lockdown_config)

    def fix_cliques(self, encounter_size, group_size=None, lockdown_config=None):
        """
        :param encounter_size: not used
        :param group_size: not used
        :return:
        """
        lockdown_config = lockdown_config or {'classrooms': 0, 'workplaces': 0}
        static_cliques = self.build_city_cliques(lockdown_config)
        logging.info(f"Adding {len(static_cliques)} permanent contact groups")
        dynamic_cliques = FixedNetworkPopulation.fix_cliques(self, EPHEMERAL_CONTACT)
        logging.info(f"Adding {len(dynamic_cliques)} ephemeral contact pairs")

        building_cliques = []
        for b in self.buildings:
            building_cliques.extend(FixedNetworkPopulation.fix_cliques(self, WITHIN_BUILDING_CONTACT, people=b))
        logging.info(f"Adding {len(building_cliques)} contacts each within one of the {len(self.buildings)} buildings "
                     f"(contact density of {WITHIN_BUILDING_CONTACT})")

        return static_cliques + dynamic_cliques + building_cliques

    def build_city_cliques(self, lockdown_config, by_deprivation=True):

        workplaces = _suppress(self.workplaces, 'workplaces', lockdown_config['workplaces'],
                               by_deprivation=by_deprivation)

        classrooms = _suppress(self.classrooms, 'classrooms', lockdown_config['classrooms'],
                               by_deprivation=by_deprivation)

        return self.households + workplaces + classrooms + self.care_homes


def _suppress(workplaces, name, lockdown_factor, by_deprivation=True):

    def income_decile(p):
        """
        :param p: person
        :return: a float from most deprived to least in [1., 2., 3., 4., 5., 6., 7., 8., 9., 10.]
        """
        return p.home.lsoa.features['Income_Decile']

    def _dep(people):
        # :return: the mean decile of the people, transformed linearly to lie between -1 and 1.
        if not by_deprivation:
            return 0.
        return (np.mean([income_decile(person) for person in people]) / 10. - 0.55) / 0.45

    def _prob_lockdown(grp):
        """
        :param grp: a group of people
        :return: probability that this group will be locked down. While taking account of the global lockdown factor,
        this is linear in grp's mean_income_decile, and is set so that if all members of grp are of decile 10,
        then the probability of lockdown is exactly one.
        """
        return lockdown_factor + (_dep(grp) * (1 - lockdown_factor))

    open_workplaces = [g for g in workplaces if random.random() > _prob_lockdown(g)]
    report_lockdown(income_decile, lockdown_factor, name, open_workplaces)
    return open_workplaces


def report_lockdown(income_decile, lockdown_factor, name, open_workplaces):
    """
    Just do some logging
    """
    workplace_deciles = [income_decile(p) for g in open_workplaces for p in g]
    logging.info(f"{lockdown_factor * 100}% of {name} closed by lockdown, "
                 f"leaving {len(open_workplaces)} open, "
                 f"of average Income Decile "
                 f"{np.mean(workplace_deciles):2.2f} (and st dev {np.std(workplace_deciles):2.2f}).")


def build_city_structures(people, schools_by_ward=True):
    """
    :param people: a list of population.covid.PersonCovid() objects
    :param schools_by_ward: bool. If True, then school classrooms will contain only children of the same ward
    :return: a list of little sets, each is a 'clique' in the graph, some are households, some are workplaces
    each individual should belong to exactly one household and one workplace
    for example: [{person_0, person_1, person_2}, {person_0, person_10, person_54, person_88, person_550, person_270}]
    - except not everyone is accounted for of course
    """
    households = build_households(people)
    report_size(households, 'households')

    buildings = build_buildings(people)
    report_size(buildings, 'buildings')

    classrooms = build_classes_by_ward(people) if schools_by_ward else build_class_groups(people)

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

    return households, workplaces, classrooms, care_homes, buildings


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


def build_class_groups(people, class_size=30):
    classrooms = []
    for kids_age in range(MINIMUM_CLASS_AGE, MAXIMUM_CLASS_AGE + 1):
        schoolkids = [p for p in people if p.age == kids_age]
        random.shuffle(schoolkids)
        classrooms += build_workplaces(schoolkids, force_size=class_size)
    return classrooms


def build_classes_by_ward(people, class_size=30):

    def _inhabitants(wrd):
        return [p for p in people if p.home.ward == wrd]

    classes = []
    for ward in {p.home.ward for p in people}:
        classes += build_class_groups(_inhabitants(ward), class_size)
    return classes


def build_buildings(people):
    bdngs = defaultdict(list)
    for p in people:
        bdngs[p.home.building].append(p)
    return list(bdngs.values())


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
    homes_examples = get_home_samples(num_h)
    logging.debug(f"There are {len(homes_examples)} households generated for accommodation buildings")

    while assigned < n_individuals:
        ages = next_household_ages(household_examples)
        size = len(ages)
        # randomly pick up a home from list of homes
        home_specification = next_household_home(homes_examples)
        home = Home(*home_specification)
        if assigned + size > n_individuals:
            ages = ages[:n_individuals - assigned - size]
            size = len(ages)

        hh = []
        for j, age in enumerate(ages):
            indiv = people[j + assigned]
            indiv.age = age
            indiv.home = home

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


def build_workplaces(people, force_size=None):
    """
    :param people: lets for now let these be a list of N population.covid.PersonCovid() objects
    :param force_size: specify number of participants
    :return: a list of workplaces, where workplaces are a list of person objects.
    """
    n_individuals = len(people)
    assigned = 0
    workplaces = []
    while assigned < n_individuals:

        size = force_size or next_workplace_size()

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

