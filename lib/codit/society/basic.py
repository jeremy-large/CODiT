from codit.config import set_config
from codit.society.test import TestQueue

class Society:
    def __init__(self, census=None, episodes_per_day=None, encounter_size=None, prob_unnecessary_worry=0, config=None):
        set_config(self, config)
        if not prob_unnecessary_worry:
            prob_unnecessary_worry = self.cfg.PROB_NON_C19_SYMPTOMS_PER_DAY
        self.episodes_per_day = episodes_per_day or self.cfg.SIMULATOR_PERIODS_PER_DAY
        assert type(self.episodes_per_day) == int
        self.encounter_size = encounter_size or self.cfg.MEAN_NETWORK_SIZE
        self.prob_worry = prob_unnecessary_worry / self.episodes_per_day
        self.queues = [TestQueue()]
        self.test_recorder = []
        self.census = census

    def manage_outbreak(self, population):
        pass

    def get_test_request(self, person, notes):
        pass

    def remove_stale_test(self, person):
        pass

    def currently_testing(self, person):
        return False

    def clear_queues(self):
        for q in self.queues:
            q.__init__(test_type=q.test_type)

class DraconianSociety(Society):
    def manage_outbreak(self, population):
        for person in population.people:
            if person.symptomatic:
                person.isolate()
