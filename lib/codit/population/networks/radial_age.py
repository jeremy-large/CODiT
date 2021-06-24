import random

import numpy as np

from codit.population import FixedNetworkPopulation


class RadialAgePopulation(FixedNetworkPopulation):

    def fix_cliques(self, mean_num_contacts, group_size=2, radius=15, max_group_size=40, max_age=80):
        return build_cliques(self.people, max_age, radius, max_group_size, mean_num_contacts)


def build_cliques(people, max_age, radius, max_group_size, mean_num_contacts):
    n_people = len(people)
    coord = locate_population(people)
    groups = []
    n_contacts = 0
    max_contacts = mean_num_contacts * n_people
    while n_contacts < max_contacts:
        location = np.random.uniform(-max_age - radius, max_age + radius, size=len(coord[0]))
        grp = build_clique(location, radius, people, coord, max_group_size, n_people)
        if (len(grp) > 1):  #  and (grp not in groups):
            n_contacts += (len(grp) * (len(grp) - 1))
            groups.append(grp)
    return groups


def locate_population(people):
    coord = []
    for person in people:
        degree = random.random() * 2 * np.pi
        person.age = random.random() * 60 + 20
        coord.append(person.age * np.array([np.sin(degree), np.cos(degree)]))
    return np.array(coord)


def build_clique(location, radius, people, people_coordinates, max_group_size, population_size):
    cidx = random.sample(range(population_size), max_group_size)
    diffs = people_coordinates[cidx] - location
    distances = np.sum(diffs ** 2, axis=1)
    candidates = (people[ix] for ix in cidx)
    return set([p.name for i, p in enumerate(candidates) if distances[i] < radius ** 2])