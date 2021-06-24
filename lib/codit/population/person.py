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

        self.simplify_state()
        self.adopt_society(society)

        self.isolation = None
        self.infectious = False
        self.time_since_infection = 0
        self.disease = None
        self.name = name

        self.covid_experiences = []
        self.vaccinations = []
        self.update_immunities()
        # Add home attribute for CityPopulation
        self.home = home

    def simplify_state(self):
        self.infectors = []
        self.chain_length = None
        self.victims = set()
        self.society = None

    def adopt_society(self, society):
        self.society = society
        self.episode_time = 1. / self.society.episodes_per_day

    def __repr__(self):
        if self.name is None:
            return f"Unnamed person"
        return f"person {self.name}"

    @property
    def symptomatic(self):
        return self.infectious

    @property
    def infected(self):
        return len(self.covid_experiences) > 0

    def update_immunities(self):
        """
        The idea is that the immunities a person have are a simple dictionary lookup of their covid_experiences
        """
        immunities = dict()
        for d in self.covid_experiences:
            for name, value in self.cfg.CROSS_IMMUNITY[str(d)].items():
                immunities[name] = max(value, immunities.get(name, 0.0))

        for v in self.vaccinations:
            for name, value in self.cfg.VACCINATION_IMMUNITY[v].items():
                immunities[name] = max(value, immunities.get(name, 0.0))

        self.immunities = immunities

    def succeptibility_to(self, disease):
        return 1. - self.immunities.get(str(disease), 0.)

    def vaccinate_with(self, vaccine):
        assert vaccine in self.cfg.VACCINATION_IMMUNITY
        self.vaccinations.append(vaccine)
        self.update_immunities()

    def attack(self, other, days):
        if self.infectious:
            self.infectious_attack(other, days)

    def infectious_attack(self, other, days):
        succeptibility = other.succeptibility_to(self.disease)
        if succeptibility > 0:
            if random.random() < self.disease.pr_transmit_per_day * days * succeptibility:
                other.set_infected(self.disease, infector=self)
                self.victims.add(other.name)

    def set_infected(self, disease, infector=None):
        assert self.succeptibility_to(disease) > 0
        self.covid_experiences.append(disease)
        self.update_immunities()
        self.infectious = True
        self.disease = disease
        self.chain_length = 1
        if infector:
            self.chain_length = infector.chain_length + 1
            self.infectors.append(infector.name)

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
        self.time_since_infection = 0

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

    def contact_persons(self, census):
        return [census[c] for c in self.contacts]

    def chain(self, census):
        """
        :param census: a population.census()
        :return:
        """
        assert self.covid_experiences, f"We cannot generate a chain for a person who has not been infected. {self}"
        chain = [self]
        m_inf = self
        while m_inf.infectors:
            m_inf = census[m_inf.infectors[0]]
            chain.append(m_inf)
        chain.reverse()
        return chain
