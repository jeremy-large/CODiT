import random
import numpy as np

from codit.population.person import Person


class PersonCovid(Person):
    def __init__(self, name, config=None, home=None):
        Person.__init__(self, name, config=config, home=home)
        self._symptomatic = False
        self.has_tested_positive = False

    @property
    def symptomatic(self):
        return self._symptomatic

    def set_infected(self, disease, infector=None):
        Person.set_infected(self, disease, infector=infector)
        self.infectious = False

    def update_disease(self, days, society):
        """
        :param days: days since you got infected with the disease
        """
        cov = self.disease
        if np.isclose(days, cov.days_before_infectious):
            self.infectious = True

        elif np.isclose(days, cov.days_before_infectious + cov.days_to_symptoms):
            if random.random() < cov.prob_symptomatic:
                self._symptomatic = True
                self.react_to_new_symptoms(society)

        elif np.isclose(days, cov.days_before_infectious + cov.days_infectious):
            self._symptomatic = False
            self.recover()

    def react_to_new_symptoms(self, society):
        if random.random() < self.cfg.PROB_ISOLATE_IF_SYMPTOMS:
            self.isolate()
        if random.random() < self.cfg.PROB_APPLY_FOR_TEST_IF_SYMPTOMS:
            society.get_test_request(self, notes='symptoms')

    def update_time(self, society):
        if random.random() < self.prob_worry:
            self.react_to_new_symptoms(society)
        Person.update_time(self, society)

    def get_test_results(self, positive):
        if not positive:
            if self.isolating:
                self.leave_isolation()   # TODO: even if it was a lateral flow test that turned out negative!
        elif random.random() < self.cfg.PROB_ISOLATE_IF_TESTPOS:
            self.isolate()

    def consider_leaving_isolation(self, society):
        if self.isolation.days_elapsed > self.cfg.DURATION_OF_ISOLATION:
            society.remove_stale_test(self)
            if not society.currently_testing(self):
                self.leave_isolation()
