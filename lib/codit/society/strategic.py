from codit.society import UKSociety, HighValencyTester
from codit.society.test import TestQueue
import random


class TwoTrackTester(UKSociety):

    CONTACT_VALENCY_THRESHOLD = 22   # vF
    PROPORTION_FAST_TRACK = 0.5
    DAYS_TO_CONTACTS_SECOND_TEST = 3
    MIN_CONTACTS_TEST = 0

    def __init__(self, **kwargs):
        UKSociety.__init__(self, **kwargs)
        self.fast_track = TestQueue()
        self.slow_track = TestQueue()
        self.queues = (self.fast_track, self.slow_track)

    def act_on_test(self, test, census=None, test_contacts=False):
        UKSociety.act_on_test(self, test, census=census, test_contacts=True)

        if not test.positive and test.notes == 'contact':
            if random.random() < self.cfg.PROB_ISOLATE_IF_TRACED:
                test.person.isolate()
                self.get_test_request(test.person, notes='contact part two',
                                      priority=True, days_delayed_start=self.DAYS_TO_CONTACTS_SECOND_TEST)

    def screen_contact_for_testing(self, c, do_test=None):
        if len(c.contacts) >= self.CONTACT_VALENCY_THRESHOLD:
            self.get_test_request(c, notes='contact', priority=True)

    def get_test_request(self, person, notes='', priority=False, days_delayed_start=0):

        if len(person.contacts) < self.MIN_CONTACTS_TEST:
            return

        if random.random() < self.cfg.PROB_TEST_IF_REQUESTED:
            if not self.currently_testing(person):
                args = (person, notes, self.cfg.TEST_DAYS_ELAPSED, False, days_delayed_start)
                if priority:
                    self.fast_track.add_test(*args)
                else:
                    self.slow_track.add_test(*args)

    def add_test(self, person, notes, front_of_queue=False):
        raise NotImplementedError

    def set_actionable_tests(self, max_processed):
        fast_max = int(max_processed * self.PROPORTION_FAST_TRACK)
        self.fast_track.completed_tests = self.fast_track.pick_actionable_tests(fast_max)

        slow_max = max_processed - len(self.fast_track.completed_tests)
        self.slow_track.completed_tests = self.slow_track.pick_actionable_tests(slow_max)


class TwoTrackTesterofSymptoms(TwoTrackTester):

    def get_test_request(self, person, notes='', priority=False, days_delayed_start=0):

        if notes == 'symptoms' and len(person.contacts) > self.CONTACT_VALENCY_THRESHOLD:
            assert not priority
            priority = True

        TwoTrackTester.get_test_request(self, person,
                                        notes=notes,
                                        priority=priority,
                                        days_delayed_start=days_delayed_start)


class TwoTrackSystem(TwoTrackTesterofSymptoms):

    VALENCY_TEST_FREQUENCY_DAYS = 0
    GENERAL_VALENCY_THRESHOLD = 20

    def manage_outbreak(self, population, max_processed=None):
        HighValencyTester.handle_high_valencies(self, population)
        UKSociety.manage_outbreak(self, population)

    def handle_connected_person(self, person):
        if not self.currently_testing(person):
            if not self.fast_track.contains_planned_test_of(person):
                self.fast_track.add_test(person, 'valency', self.cfg.TEST_DAYS_ELAPSED,
                                         days_delayed_start=self.VALENCY_TEST_FREQUENCY_DAYS)
