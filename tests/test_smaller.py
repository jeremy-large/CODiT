import random
import numpy as np

from codit.outbreak import Outbreak
from codit.outbreak_recorder import WardComponent, MorbidityComponent
from codit.society import TestingTracingSociety
from codit.society.alternatives import StrategicTester
from codit.society.strategic import TwoTrackTester
from codit.society.lateral import LateralFlowUK
from codit.disease import Covid
from codit.population.networks.radial_age import RadialAgePopulation
from codit.population.networks.household_workplace import HouseholdWorkplacePopulation
from codit.population.networks.city import CityPopulation
from codit.config import CFG

ALL_TIME_DAYS = 15


def test_mutation():
    random.seed(42)
    mutation = Covid(pr_transmission_per_day=CFG.PROB_INFECT_IF_TOGETHER_ON_A_DAY["B.1.1.7"], name="B.1.1.7")
    o = Outbreak(TwoTrackTester(), mutation, pop_size=5000, seed_size=50, n_days=150)
    o.simulate()


def test_multiple_strain_society():
    random.seed(42)
    variant_1 = Covid(pr_transmission_per_day=CFG.PROB_INFECT_IF_TOGETHER_ON_A_DAY["B.1.1.7"], name="B.1.1.7")
    diseases = {Covid(), variant_1}
    o = Outbreak(TwoTrackTester(), diseases, pop_size=5000, seed_size=50, n_days=150)
    o.simulate()


def test_two_track_society():
    random.seed(42)
    o = Outbreak(TwoTrackTester(), Covid(), pop_size=5000, seed_size=50, n_days=150)
    o.simulate()


def test_two_track_hetero_society():
    random.seed(42)
    o = Outbreak(TwoTrackTester(), Covid(), pop_size=5000, seed_size=50, n_days=150,
                 population_type=RadialAgePopulation)
    o.simulate()


def test_two_track_hw_society():
    random.seed(42)
    o = Outbreak(TwoTrackTester(), Covid(), pop_size=5000, seed_size=50, n_days=150,
                 population_type=HouseholdWorkplacePopulation)
    o.simulate()


def test_two_track_city_society():
    random.seed(42)
    pop = CityPopulation(5600 * 5, TestingTracingSociety())
    o = Outbreak(LateralFlowUK(config=dict(SIMULATOR_PERIODS_PER_DAY=4, DAILY_TEST_CAPACITY_PER_HEAD=1)), Covid(),
                 pop_size=8000, seed_size=8000//80, n_days=150,
                 population_type=CityPopulation)
    o.recorder.add_component(WardComponent(o))
    o.recorder.add_component(MorbidityComponent(o.pop.people))
    o.simulate()


def test_smart_society():
    random.seed(42)
    o = Outbreak(StrategicTester(), Covid(), pop_size=5000, seed_size=50, n_days=150)
    o.simulate()


def test_covid_model():
    s = TestingTracingSociety(episodes_per_day=2, config=dict(PROB_TEST_IF_REQUESTED=0.4))
    random.seed(42)
    np.random.seed(42)
    o = Outbreak(s, Covid(), pop_size=8, seed_size=1, n_days=ALL_TIME_DAYS)
    o.simulate()
    # for k, v in o.pop.contacts.items():
    #     print(k, len(v))
    #                           t     cov   risks  tests  isol
    np.testing.assert_allclose(o.recorder.main_component.story[:15], [[0.5, 0.25, 0.125, 0.0, 0.125, 0.0],
                                                       [1.0, 0.25, 0.125, 0.25, 0.0, 0.0],
                                                       [1.5, 0.25, 0.125, 0.0, 0.0, 0.0],
                                                       [2.0, 0.375, 0.125, 0.0, 0.0, 0.0],
                                                       [2.5, 0.375, 0.125, 0.0, 0.0, 0.0],
                                                       [3.0, 0.375, 0.125, 0.0, 0.0, 0.0],
                                                       [3.5, 0.375, 0.125, 0.0, 0.0, 0.0],
                                                       [4.0, 0.375, 0.125, 0.0, 0.0, 0.125],
                                                       [4.5, 0.375, 0.25, 0.0, 0.0, 0.125],
                                                       [5.0, 0.5, 0.25, 0.0, 0.0, 0.125],
                                                       [5.5, 0.5, 0.125, 0.0, 0.0, 0.125],
                                                       [6.0, 0.5, 0.25, 0.0, 0.0, 0.125],
                                                       [6.5, 0.5, 0.25, 0.0, 0.0, 0.125],
                                                       [7.0, 0.5, 0.25, 0.0, 0.0, 0.125],
                                                       [7.5, 0.5, 0.25, 0.0, 0.0, 0.125]])
