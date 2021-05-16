import random

from codit.config import set_config
from codit.immunity import ImmuneResponse, INFECTIONS

class Person:
    def __init__(self, society, config=None, name=None, home=None):
        set_config(self, config)

        self.simplify_state()
        self.adopt_society(society)

        self.days_in_isolation = None
        self.infectious = False
        self.time_since_infection = 0

        self.disease = None
        self.name = name


        self.immunities = ImmuneResponse(0)

        # Add home attribute for CityPopulation
        self.home = home

    def simplify_state(self):
        self.infectors = []
        self.victims = set()
        self.society = None

    def adopt_society(self, society):
        self.society = society
        self.episode_time = 1. / self.society.episodes_per_day

    def __repr__(self):
        if self.name is None:
            return f"Unnamed person"
        return str(self.name)

    @property
    def symptomatic(self):
        return self.infectious

    @property
    def infected(self):
        return (self.immunities & INFECTIONS) != 0

    def succeptibility_to(self, disease):
        if disease.variant:
            return 1.0 - max((self.cfg.IMMUNITIES[response].get(disease.variant, 0.0) for response in self.immunities), default=0.0)
        return 0.0

    def vaccinate_with(self, immune_response):
        assert immune_response in self.cfg.IMMUNITIES
        self.immunities |= immune_response

    def attack(self, other, days):
        if self.infectious:
            self.infectious_attack(other, days)

    def infectious_attack(self, other, days):
        succeptibility = other.succeptibility_to(self.disease)
        if succeptibility > 0:
            if random.random() < self.disease.pr_transmit_per_day * days * succeptibility:
                other.set_infected(self.disease, infector=self)
                self.victims.add(other)

    def set_infected(self, disease, infector=None):
        assert self.succeptibility_to(disease) > 0

        self.immunities |= disease.variant
        self.infectious = True
        self.disease = disease
        if infector:
            self.infectors.append(infector)

    def isolate(self):
        self.days_in_isolation = 0

    def leave_isolation(self):
        self.days_in_isolation = None

    @property
    def isolating(self):
        return self.days_in_isolation is not None

    def recover(self):
        self.infectious = False
        self.disease = None
        self.time_since_infection = 0

    def update_time(self):
        if self.isolating:
            self.days_in_isolation += self.episode_time
            if self.days_in_isolation > self.cfg.DURATION_OF_ISOLATION:
                self.leave_isolation()

        if self.disease is not None:
            self.time_since_infection += 1
            self.update_disease(self.days_infected())

    def days_infected(self):
        return self.time_since_infection / self.society.episodes_per_day

    def update_disease(self, days_since_infect):
        if days_since_infect >= self.disease.days_infectious:
            self.recover()

    def chain(self):
        assert self.infected, f"We cannot generate a chain for a person who has not been infected. {self}"
        chain = [self]
        m_inf = self
        while m_inf.infectors:
            m_inf = m_inf.infectors[0]
            chain.append(m_inf)
        chain.reverse()
        return chain
