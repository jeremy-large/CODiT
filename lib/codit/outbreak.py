import logging

from codit.outbreak_recorder import OutbreakRecorder
from codit.population.covid import PersonCovid
from codit.population.population import FixedNetworkPopulation


class Outbreak:
    def __init__(self, society, diseases=set(), pop_size=0, seed_size=0, n_days=0,
                 population=None,
                 population_type=None,
                 person_type=None,
                 show_heatmap=False,
                 reset_population=True):

        self.pop = self.prepare_population(pop_size, population, population_type, society, person_type,
                                           reset=reset_population)
        if reset_population:
            society.clear_queues()
            self.pop.seed_infections(seed_size, diseases)

        self.initialize_timers(n_days, society.episodes_per_day)
        self.group_size = society.encounter_size

        self.society = society
        self.diseases = diseases
        # Add a switch of heatmap video
        self.set_recorder(show_heatmap=show_heatmap)

    def prepare_population(self, pop_size, population, population_type, society, person_type, reset=True):
        """
        :param reset: if set to False, then a population is passed in without being reset
        :return:
        """
        if population:
            assert pop_size in (0, len(population.people)), "provide a population of the correct size"
            logging.debug("Using a pre-existing population")
            if person_type is not None:
                assert {person_type} == set(type(p) for p in population.people), \
                    "The people in this population are of the wrong type"
            if reset:
                population.reset_people(society)
            self.pop = population
            return population

        population_type = population_type or FixedNetworkPopulation
        person_type = person_type or PersonCovid
        return population_type(pop_size, society, person_type=person_type)

    def set_recorder(self, recorder=None, show_heatmap=False):
        self.recorder = recorder or OutbreakRecorder(self, show_heatmap)

    def initialize_timers(self, n_days, enc_per_day):
        self.n_days = n_days
        self.n_periods = n_days * enc_per_day
        self.time_increment = 1 / enc_per_day

        self.time = 0
        self.step_num = 0

    def simulate(self):
        for t in range(self.n_periods):
            self.update_time()
            self.society.manage_outbreak(self.pop)
            self.pop.attack_in_groupings(self.group_size)
            self.record_state()

        self.recorder.realized_r0 = self.pop.realized_r0()
        self.recorder.society_config = self.society.cfg

        if type(self.diseases) is set:
            self.recorder.disease_config = [d.cfg for d in self.diseases]
        else:
            self.recorder.disease_config = self.diseases.cfg

        return self.recorder

    def update_time(self):
        self.pop.update_time()
        self.time += self.time_increment
        self.step_num += 1

    def record_state(self):
        self.recorder.record_step(self)

    def plot(self, **kwargs):
        self.recorder.plot(**kwargs)
