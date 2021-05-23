import random
from codit.config import set_config
from codit.immunity import ImmuneResponse, INFECTIONS

class Person:
    def __init__(self, id, society, config=None, home=None):
        self.id = id
        set_config(self, config)
        self.reset(society)

        # Add home attribute for CityPopulation
        self.home = home

    def reset(self, society):
        self.days_in_isolation = None
        self.infectious = False  # TODO: Make property  is not None and time_since_infection > DAYS_BEFORE_INFECTIOUS
        self.time_since_infection = 0
        self.disease = None
        self.immunities = ImmuneResponse(0)
        self.simplify_state()
        self.adopt_society(society)

    def simplify_state(self):
        self.infectors = []  # first infector
        self.victims = set()
        self.society = None

    def adopt_society(self, society):
        self.society = society
        self.episode_time = 1. / self.society.episodes_per_day

    def __repr__(self):
        return f"Person {id}"

    @property
    def symptomatic(self):
        return self.infectious  # TODO: Make property time_since_infection is not None and time_since_infection > DAYS_BEFORE_INFECTIOUS + DAYS_INFECTIOUS_TO_SYMPTOMS

    @property
    def infected(self):
        return (self.immunities & INFECTIONS) != 0

    def succeptibility_to(self, disease):
        return 1.0 - max((self.cfg.IMMUNITIES[response].get(disease.variant, 0.0) for response in self.immunities), default=0.0)

    def vaccinate_with(self, immune_response):
        assert immune_response in self.cfg.IMMUNITIES
        self.immunities |= immune_response

    def attack(self, other, days):
        if self.infectious:
            self.infectious_attack(other, days)

    def infectious_attack(self, other, days):
        assert other.id != self.id, "Can not attack self"
        succeptibility = other.succeptibility_to(self.disease)
        if succeptibility > 0:
            if random.random() < self.disease.pr_transmit_per_day * days * succeptibility:
                other.set_infected(self.disease, infector=self)
                self.victims.add(other.id)

    def set_infected(self, disease, infector=None):
        if disease.variant:
            self.immunities |= disease.variant
        self.infectious = True
        self.disease = disease

        if  self.infectors:
            self.infectors.append(infector.id)

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
