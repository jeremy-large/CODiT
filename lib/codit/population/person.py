import random

from codit.config import set_config


class Isolation:
    def __init__(self):
        self.days_elapsed = 0

    def update_time(self, timedelta):
        self.days_elapsed += timedelta


class Person:
    def __init__(self, society, config=None, name=None):
        set_config(self, config)
        self.society = society
        self.isolation = None
        self.infectious = False
        self.time_since_infection = 0
        self.diseases = None
        self.infector = None
        self.covid_experiences = set()
        # self.immunities = set()
        # self.infected = False
        self.victims = set()
        self.episode_time = 1. / self.society.episodes_per_day
        self.name = name

    def __repr__(self):
        if self.name is None:
            return f"Unnamed person"
        return str(self.name)

    @property
    def symptomatic(self):
        return self.infectious

    # @property
    # def infected(self):
    #    return len(self.covid_experiences) > 0

    # @property
    # def immunities(self):
    #    """
    #    The idea is that the immunities a person have are a simple dictionary lookup of their covid_experiences
    #    """
    #    immunities = set()
    #    for d in self.covid_experiences:
    #        immunities.add(self.cfg.CROSS_IMMUNITY[d])
    #    # for v in self.vacciations:
    #    #    immunities.add(self.cfg.VACCINATION_IMMUNITY[v])
    #    return immunities

    def attack(self, other, days):
        if self.infectious:
            self.infectious_attack(other, days)

    def infectious_attack(self, other, days):
        if self.diseases not in other.immunities:
            if random.random() < self.diseases.pr_transmit_per_day * days:
                other.set_infected(self.diseases, infector=self)
                self.victims.add(other)

    def set_infected(self, diseases, infector=None):
        self.covid_experiences.add(diseases)
        self.infectious = True
        self.diseases = diseases
        self.infector = infector

    def isolate(self):
        if self.isolation is None:
            self.isolation = Isolation()

    def leave_isolation(self):
        assert self.isolating
        self.isolation = None

    @property
    def isolating(self):
        return self.isolation is not None

    def recover(self):
        self.infectious = False
        self.diseases = None

    def update_time(self):

        if self.isolating:
            self.isolation.update_time(self.episode_time)
            self.consider_leaving_isolation()

        if self.diseases is not None:
            self.time_since_infection += 1
            self.update_diseases(self.days_infected())
        else:
            pass

    def days_infected(self):
        return self.time_since_infection / self.society.episodes_per_day

    def consider_leaving_isolation(self):
        if self.isolation.days_elapsed > self.cfg.DURATION_OF_ISOLATION:
            self.leave_isolation()

    def update_diseases(self, days_since_infect):
        if days_since_infect == self.diseases.days_infectious:
            self.recover()

    def chain(self):
        assert self.covid_experiences, f"We cannot generate a chain for a person who has not been infected. {self}"
        chain = [self]
        m_inf = self.infector
        while m_inf is not None:
            chain.append(m_inf)
            m_inf = m_inf.infector
        chain.reverse()
        return chain
