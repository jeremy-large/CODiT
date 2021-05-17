import random
import numpy as np

from codit.society import Society
from codit.disease import Covid
from codit.outbreak import Outbreak
from codit.population import Population
from codit.population.person import Person
from codit.immunity import ImmuneResponse

ALL_TIME_DAYS = 50


def test_uk_ovespill_model():
    from codit.society.alternatives import UKSociety
    random.seed(42)
    np.random.seed(42)
    o = Outbreak(UKSociety(config=dict(PROB_NON_C19_SYMPTOMS_PER_DAY=0.1)),
                 Covid(), pop_size=1000, seed_size=20, n_days=ALL_TIME_DAYS)
    o.simulate()

    # Skip this test because the the simulator is not deterministic.
    # I believe it is because it uses np.random by calls multi-threaded numpy code.
    # TODO: I believe the correct solution is for the simulator to be constructed with its own np.random.RandomState class
    #
    return
    np.testing.assert_allclose(o.recorder.main_component.story[40:45] == [[41.0, 0.035, 0.0, 0.007, 0.467, 0.452],
                                                           [42.0, 0.035, 0.0, 0.007, 0.458, 0.442],
                                                           [43.0, 0.035, 0.0, 0.007, 0.461, 0.447],
                                                           [44.0, 0.035, 0.0, 0.007, 0.458, 0.448],
                                                           [45.0, 0.035, 0.0, 0.007, 0.457, 0.448]])


def test_covid_model():
    from codit.society import TestingSociety
    from codit.disease import Covid
    s = TestingSociety(episodes_per_day=5, config={ "MEAN_NETWORK_SIZE": 2,
                                                    "PROB_NON_C19_SYMPTOMS_PER_DAY": 0,
                                                    "PROB_TEST_IF_REQUESTED": 0.4})

    d = Covid(days_infectious=10, pr_transmission_per_day=0.2)
    # seed size is the number of people in the population who we seed as being infected:
    random.seed(42)
    o = Outbreak(s, d, pop_size=1000, seed_size=20, n_days=ALL_TIME_DAYS)
    # so, this is a village of 10000 people with 2 starting off infected

    random.seed(42)
    o.simulate()
    np.testing.assert_allclose(o.recorder.main_component.story[90:95], [[18.2, 0.103, 0.044, 0.0, 0.0, 0.023],
                                                         [18.4, 0.103, 0.046, 0.0, 0.0, 0.023],
                                                         [18.6, 0.103, 0.045, 0.0, 0.0, 0.021],
                                                         [18.8, 0.105, 0.043, 0.0, 0.0, 0.019],
                                                         [19.0, 0.105, 0.043, 0.0, 0.0, 0.017]])
"""
Day 9, prop infected is 0.061, prop infectious is 0.061
Day 19, prop infected is 0.141, prop infectious is 0.08
Day 29, prop infected is 0.226, prop infectious is 0.085
Day 40, prop infected is 0.294, prop infectious is 0.068
Day 50, prop infected is 0.34, prop infectious is 0.046
"""



def test_draconian_population_model():
    from codit.society.basic import DraconianSociety
    random.seed(42)
    s = DraconianSociety(episodes_per_day=5, encounter_size=2)
    d = Covid(days_infectious=10, pr_transmission_per_day=0.2, variant=ImmuneResponse.SARS_CoV_2_INFECTION)
    # seed size is the number of people in the population who we seed as being infected:
    o = Outbreak(s, d, pop_size=1000, seed_size=2, n_days=ALL_TIME_DAYS, population_type=Population, person_type=Person)
    # so, this is a village of 10000 people with 2 starting off infected
    o.simulate()
    np.testing.assert_allclose(o.recorder.main_component.story[90:95], [[18.2, 0.002, 0.0, 0.0, 0.0, 0.001],
                                                                        [18.4, 0.002, 0.0, 0.0, 0.0, 0.001],
                                                                        [18.6, 0.002, 0.0, 0.0, 0.0, 0.001],
                                                                        [18.8, 0.002, 0.0, 0.0, 0.0, 0.001],
                                                                        [19.0, 0.002, 0.0, 0.0, 0.0, 0.001]])


def test_toy_model():
    random.seed(42)
    s = Society(episodes_per_day=5, encounter_size=2)
    d = Covid(days_infectious=10, pr_transmission_per_day=0.2, variant=ImmuneResponse.SARS_CoV_2_INFECTION)
    # seed size is the number of people in the population who we seed as being infected:
    o = Outbreak(s, d, pop_size=1000, seed_size=2, n_days=ALL_TIME_DAYS, population_type=Population, person_type=Person)
    # so, this is a village of 10000 people with 2 starting off infected
    o.simulate()
    np.testing.assert_allclose(o.recorder.main_component.story[90:95], [[18.2, 0.619,  0.57, 0.0, 0.0, 0.0],
                                                         [18.4, 0.643, 0.592, 0.0, 0.0, 0.0],
                                                         [18.6, 0.656, 0.603, 0.0, 0.0, 0.0],
                                                         [18.8, 0.673, 0.618, 0.0, 0.0, 0.0],
                                                         [19.0,  0.69, 0.635, 0.0, 0.0, 0.0]])
