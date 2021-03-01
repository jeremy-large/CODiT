import random

from codit.config import set_config


class Isolation:
    def __init__(self):
        self.days_elapsed = 0

    def update_time(self, timedelta):
        self.days_elapsed += timedelta


class Person:
    def __init__(self, society, config=None, name=None, home=None):
        set_config(self, config)
        self.society = society
        self.isolation = None
        self.infectious = False
        self.time_since_infection = 0
        self.disease = None
        self.infector = None
        self.victims = set()
        self.covid_experiences = []
        self.episode_time = 1. / self.society.episodes_per_day
        self.name = name
        self.vaccinations = []
        # Add home attribute for CityPopulation
        self.home = home

    def __repr__(self):
        if self.name is None:
            return f"Unnamed person"
        return str(self.name)

    @property
    def symptomatic(self):
        return self.infectious

    @property
    def infected(self):
        return len(self.covid_experiences) > 0

    @property
    def immunities(self):
        """
        The idea is that the immunities a person have are a simple dictionary lookup of their covid_experiences
        """
        immunities = set()
        for d in self.covid_experiences:
            immunities |= self.cfg.CROSS_IMMUNITY[str(d)]
        for v in self.vaccinations:
            immunities |= self.cfg.VACCINATION_IMMUNITY[v]
        return immunities

    def succeptible_to(self, disease):
        return str(disease) not in self.immunities

    def vaccinate_with(self, vaccine):
        self.vaccinations.append(vaccine)

    def attack(self, other, days):
        if self.infectious:
            self.infectious_attack(other, days)

    def infectious_attack(self, other, days):
        if other.succeptible_to(self.disease):
            if random.random() < self.disease.pr_transmit_per_day * days:
                other.set_infected(self.disease, infector=self)
                self.victims.add(other)

    def set_infected(self, disease, infector=None):
        assert self.succeptible_to(disease)
        self.covid_experiences.append(disease)
        self.infectious = True
        self.disease = disease
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
        self.disease = None

    def update_time(self):

        if self.isolating:
            self.isolation.update_time(self.episode_time)
            self.consider_leaving_isolation()

        if self.disease is not None:
            self.time_since_infection += 1
            self.update_disease(self.days_infected())
        else:
            pass

    def days_infected(self):
        return self.time_since_infection / self.society.episodes_per_day

    def consider_leaving_isolation(self):
        if self.isolation.days_elapsed > self.cfg.DURATION_OF_ISOLATION:
            self.leave_isolation()

    def update_disease(self, days_since_infect):
        if days_since_infect == self.disease.days_infectious:
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
