from codit.society import UKSociety
from codit.society.test import TestQueue, LateralFlowTest
import random
import logging
from numpy.random import exponential as exp_dis


def coopt_existing_test(track, notes, person):
    if notes[0] == 'contact':
        for test in track._tests_of[person]:
            if test.notes[0] == 'contact' and (notes[1] < test.notes[1]):
                test.notes = notes
                return True


class LateralFlowUK(UKSociety):

    VALENCY_TEST_FREQUENCY_DAYS = 4
    GENERAL_VALENCY_QUANTILE_THRESHOLD = 0.9
    LATERAL_TO_PCR_RATIO = 20
    RETEST_POSITIVE_CASES = True
    DAYS_BETWEEN_REPEATED_TESTS = 4  # not operational at the moment

    def __init__(self, **kwargs):
        UKSociety.__init__(self, **kwargs)
        self.fast_track = TestQueue(test_type=LateralFlowTest)
        self.slow_track = TestQueue()
        self.queues = (self.fast_track, self.slow_track)
        self.valency_threshold = None
        logging.info(f"The city has {self.LATERAL_TO_PCR_RATIO}x the number of lateral flow tests available, as PCRs")

    def act_on_test(self, test, census=None, n_reps_lateral_test=1):
        if test.positive:
            for id in test.person.contacts:
                if random.random() < self.cfg.PROB_TRACING_GIVEN_CONTACT:
                    c = census[id]
                    if random.random() < self.cfg.PROB_GET_TEST_IF_TRACED:
                        self.get_test_request(c, notes=('contact', 1), lateral_flow=True, census=census)
            return

        if 'contact' in test.notes:
            rep = test.notes[1]
            if rep == n_reps_lateral_test:
                return

            self.get_test_request(test.person,
                                  notes=('contact', rep + 1),
                                  lateral_flow=True,
                                  days_delayed_start=self.DAYS_BETWEEN_REPEATED_TESTS)

    def get_test_request(self, person, notes=None, lateral_flow=False, days_delayed_start=0, census=None):

        if person.has_tested_positive and not self.RETEST_POSITIVE_CASES:
            return

        if person.has_tested_positive and person.isolating:
            return

        if self.overlook_test():
            return

        track = self.fast_track
        processing_days = 0.02   # about half an hour
        if not lateral_flow:
            track = self.slow_track
            processing_days = exp_dis(self.cfg.TEST_DAYS_ELAPSED)

        if coopt_existing_test(track, notes, person):
            return

        track.add_test(person, notes, processing_days, False, days_delayed_start, census=census)

        if lateral_flow and (days_delayed_start == 0):
            # isolate for the (normally) short period while they get the first test result
            if random.random() < self.cfg.PROB_ISOLATE_IF_TRACED:
                person.isolate()

    def add_test(self, person, notes, front_of_queue=False):
        raise NotImplementedError

    def set_actionable_tests(self, max_processed):
        fast_max = int(max_processed * self.LATERAL_TO_PCR_RATIO)
        self.fast_track.completed_tests = self.fast_track.pick_actionable_tests(fast_max)

        slow_max = fast_max - len(self.fast_track.completed_tests) + max_processed
        self.slow_track.completed_tests = self.slow_track.pick_actionable_tests(slow_max)

    def manage_outbreak(self, population, max_days_wait_for_lateral=2):

        if self.valency_threshold is None:
            self.set_valency_threshold(population)

        for person in population.people:

            for test in self.fast_track.contains_planned_test_of(person):
                if test.days_elapsed > max_days_wait_for_lateral:
                    self.fast_track.remove_test(test)

            if len(person.contacts) > self.valency_threshold:
                self.handle_connected_person(person)

        UKSociety.manage_outbreak(self, population)

    def set_valency_threshold(self, population):
        degrees = sorted(population.contacts.values(), key=len)
        idx = int(self.GENERAL_VALENCY_QUANTILE_THRESHOLD * len(population.people))
        self.valency_threshold = len(degrees[idx - 1])
        logging.info(f"Setting mass testing valency/degree limit to {len(degrees[idx - 1])}")

    def handle_connected_person(self, person):
        if not self.currently_testing(person):
            if not self.fast_track.contains_planned_test_of(person):
                self.get_test_request(person,
                                      notes='valency',
                                      lateral_flow=True,
                                      days_delayed_start=exp_dis(self.VALENCY_TEST_FREQUENCY_DAYS))
