import random
from collections import defaultdict
from codit.population.person import Person
from codit.config import CFG

import numpy as np


class Population:
    def __init__(self, n_people, society, person_type=None):
        person_type = person_type or Person
        self.people = [person_type(id, society, config=society.cfg.__dict__) for id in range(n_people)]
        self.census = self.build_census()

    def reset_people(self, society):
        for person in self.people:
            person.__init__(person.name, society, config=society.cfg.__dict__, home=person.home)

    def adopt_society(self, society):
        for person in self.people:
            person.adopt_society(society)

    def clear_memory(self):
        for person in self.people:
            person.simplify_state()

    def attack_in_groupings(self, group_size):
        groups = self.form_groupings(group_size)
        for g in groups:
            g = (self.census[p] for p in g)
            g = [p for p in g if not p.isolating]
            if len(g) < 2:
                continue
            for p1 in g:
                if p1.infectious:
                    days = 1. / p1.society.episodes_per_day
                    for p2 in g:
                        if p2 != p1:
                            p1.infectious_attack(p2, days=days)

    def form_groupings(self, group_size):
        return (random.sample(self.census.keys(), group_size) for _ in range(len(self.people)))

    def seed_infections(self, n_infected, diseases, seed_periods=None):
        seed_infection(n_infected, self.people, diseases, seed_periods=seed_periods)

    def count_infectious(self, disease=None):
        infected = self.infected(disease)
        return sum(p.infectious for p in infected)

    def count_infected(self, disease=None):
        return len(self.infected(disease))

    def infected(self, disease=None):
        if disease is None:
            return [p for p in self.people if p.covid_experiences]
        return [p for p in self.people if disease in p.covid_experiences]

    def update_time(self):
        for p in self.people:
            p.update_time()

    def victim_dict(self):
        """
        :return: a dictionary from infector to the tuple of people infected
        """
        return {person: [self.census[v] for v in person.victims] for person in self.people if person.infected}

    def realized_r0(self, max_chain_len=3):
        """
        :return: We look at early infectees only.
        """
        n_victims = [len(person.victims) for person in self.people if
                     person.infectors and
                     person.chain_length <= max_chain_len]
        return np.mean(n_victims)

    def build_census(self):
        census = dict()
        for p in self.people:
            if p.name in census:
                raise ValueError(f"Cannot create census: the people in this population "
                                 f"do not have unique names, e.g. {p.name}")
            census.update({p.name: p})
        return census


def seed_infection(n_infected, people, diseases, seed_periods=None):
    if type(diseases) is not set:
        diseases = {diseases}
    if type(n_infected) is not dict:
        assert type(n_infected) == int
        n_infected = {str(d): n_infected for d in diseases}
    for d in diseases:
        seed_periods = seed_periods or d.days_infectious
        succeptibles = [p for p in people if p.succeptibility_to(d) > 0]
        for p in random.sample(succeptibles, n_infected[str(d)]):
            p.set_infected(d)
            stage = random.random() * seed_periods
            while p.disease and p.days_infected() < stage:
                p.update_time()


class FixedNetworkPopulation(Population):
    def __init__(self, n_people, society, person_type=None):
        Population.__init__(self, n_people, society, person_type=person_type)
        self.set_structure(society)

    def set_structure(self, society, **kwargs):
        self.fixed_cliques = self.fix_cliques(society.encounter_size, **kwargs)
        self.contacts = self.find_contacts()

    def find_contacts(self):
        d = defaultdict(set)
        for gr_set in self.fixed_cliques:
            for p1 in gr_set:
                d[p1] |= gr_set
        for p in self.people:
            contacts = d[p.name] - {p.name}
            p.contacts = tuple(self.census[q] for q in contacts)
        return {p: p.contacts for p in self.people}

    def fix_cliques(self, mean_num_contacts, group_size=2, people=None):
        people = people or self.people
        people = [p.name for p in people]
        # TODO: the int below rounds *down*
        n_groups = int((len(people) + 1) * mean_num_contacts / group_size)
        ii_jj = [random.choices(people, k=n_groups) for _ in range(group_size)]
        return [set(g) for g in zip(*ii_jj) if len(set(g)) == group_size]

    def form_groupings(self, group_size):
        """
        :param group_size: Does nothing in this method
        :return: So, people meet all their contacts on each round. If they have
        3 contacts on average, and a 1/3 chance of infecting one of them in a day,
         then they will infect on average one other each day.
        In our baseline config, this goes on for 2 days,
        after which they probably isolate.
        """
        for grp in self.fixed_cliques:
            yield grp
