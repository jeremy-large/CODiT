import random

from codit.society.basic import Society


class TestingSociety(Society):

    def get_test_request(self, person, notes=''):
        if self.overlook_test():
            return
        if not self.currently_testing(person):
            self.add_test(person, notes)

    def overlook_test(self):
        return (self.cfg.PROB_TEST_IF_REQUESTED < 1) and (random.random() >= self.cfg.PROB_TEST_IF_REQUESTED)

    def add_test(self, person, notes, front_of_queue=False):
        q, = self.queues
        q.add_test(person, notes, self.cfg.TEST_DAYS_ELAPSED, census=self.census, front_of_queue=front_of_queue)

    def act_on_test(self, t, census):
        pass

    def remove_test(self, test, queue):
        queue.remove_test(test)
        self.test_recorder.append(test.__dict__)

    def remove_stale_test(self, person):
        for q in self.queues:
            for t in q.tests_of(person):
                if t.days_elapsed > person.cfg.DURATION_OF_ISOLATION:
                    q.remove_test(t)
                    continue

    def currently_testing(self, person):
        for q in self.queues:
            if len(list(q.tests_of(person))) > 0:
                return True
        return False

    def manage_outbreak(self, population, max_processed=None):
        for q in self.queues:
            q.update_tests(1. / self.episodes_per_day)
        self.set_actionable_tests(max_processed)
        self.act_on_tests(population.census)

    def act_on_tests(self, census):
        for q in self.queues:
            for r_test in q.completed_tests:
                self.remove_test(r_test, q)
                r_test.person.get_test_results(r_test.positive)
                if r_test.positive:
                    r_test.person.has_tested_positive = True
                #     for t in q._tests_of[r_test.person]:
                #         q.remove_test(t)
                self.act_on_test(r_test, census)

    def set_actionable_tests(self, max_processed):
        for q in self.queues:
            q.completed_tests = q.pick_actionable_tests(max_processed)


class TestingTracingSociety(TestingSociety):

    def act_on_test(self, test, census=None, test_contacts=False):
        if test.positive:
            for id in test.person.contacts:
                if random.random() < self.cfg.PROB_TRACING_GIVEN_CONTACT:
                    c = census[id]
                    self.screen_contact_for_testing(c, do_test=test_contacts)
                    if random.random() < self.cfg.PROB_ISOLATE_IF_TRACED:
                        c.isolate()

    def screen_contact_for_testing(self, c, do_test=True):
        if do_test:
            self.get_test_request(c, notes='contact')


class UKSociety(TestingTracingSociety):
    """
    Here we add the UK's capacity constraint
    """
    def manage_outbreak(self, population):
        assert self.cfg.PROB_TEST_IF_REQUESTED == 1.
        tests_processed = self.cfg.DAILY_TEST_CAPACITY_PER_HEAD / self.episodes_per_day * len(population.people)
        TestingTracingSociety.manage_outbreak(self, population, max_processed=int(tests_processed))


class ContactTestingSociety(UKSociety):

    def act_on_test(self, test, census=None, test_contacts=False):
        TestingTracingSociety.act_on_test(self, test, census=census, test_contacts=True)


class ContactDoubleTestingSociety(UKSociety):

    def act_on_test(self, test, census=None, test_contacts=False):
        ContactTestingSociety.act_on_test(self, test, census=census)

        if not test.positive and test.notes == 'contact':
            if random.random() < self.cfg.PROB_ISOLATE_IF_TRACED:
                test.person.isolate()
                if not self.currently_testing(test.person):
                    q, = self.queues
                    q.add_test(test.person, 'contact two', self.cfg.TEST_DAYS_ELAPSED, days_delayed_start=3)


class HighValencyTester(ContactDoubleTestingSociety):

    GENERAL_VALENCY_THRESHOLD = 25
    VALENCY_TEST_FREQUENCY_DAYS = 7

    def manage_outbreak(self, population, max_processed=None):
        self.handle_high_valencies(population)
        ContactDoubleTestingSociety.manage_outbreak(self, population)

    def handle_high_valencies(self, population):
        for person in population.people:
            if len(person.contacts) >= self.GENERAL_VALENCY_THRESHOLD:
                self.handle_connected_person(person)

    def handle_connected_person(self, person):
        if not self.currently_testing(person):
            q = self.queues[0]
            # add the test to the first queue (of 1!) (later we will make this the high-priority queue)
            if not (q.contains_planned_test_of(person)):
                q.add_test(person, 'valency', self.cfg.TEST_DAYS_ELAPSED,
                           days_delayed_start=self.VALENCY_TEST_FREQUENCY_DAYS)


class HighValencyIsolator(HighValencyTester):

    def handle_connected_person(self, person):
        person.isolate()
