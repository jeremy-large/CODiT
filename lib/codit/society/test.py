import logging
from collections import defaultdict

class Test:
    def __init__(self, person, notes, time_to_complete, days_delayed_start=0):
        self.days_elapsed = 0
        self.person = person
        self.positive = None
        self.days_to_complete = time_to_complete + days_delayed_start
        self.notes = notes
        self.days_delayed_start = days_delayed_start
        targets = [q for q in person.contacts if person.disease not in q.immunities]
        self._succeptible_contacts = len(targets)
        self._succeptible_contacts_of_contacts = \
            len([s for v in targets for s in v.contacts if person.disease not in s.immunities])
        self._days_infected = person.days_infected() if person.disease else None
        self._isolating = person.isolating
        self.swab_taken = False

    def update_time(self, timedelta):
        if self.time_to_swab(timedelta):
            assert not self.swab_taken
            self.swab()
        self.days_elapsed += timedelta

    def swab(self):
        self.positive = self.person.infectious
        self.swab_taken = True

    def time_to_swab(self, timedelta):
        return self.days_delayed_start + timedelta > self.days_elapsed >= self.days_delayed_start


class TestQueue:
    def __init__(self):
        self._taken_and_planned = []
        self.completed_tests = []
        self._tests_of = defaultdict(list)

    @property
    def tests(self):
        """
        :return: for past reasons, this attribute only returns tests whose swabs have been taken
        """
        return (t for t in self._taken_and_planned if t.swab_taken)

    def remove_test(self, test):
        self._taken_and_planned.remove(test)
        self._tests_of[test.person].remove(test)

    def add_test(self, person, notes, time_to_complete, front_of_queue=False, days_delayed_start=0):

        if notes in [t.notes for t in self._tests_of[person]]:
            # then there's already a test being planned or processed in this queue with the same purpose as this one
            # do nothing ...
            return

        test = Test(person, notes, time_to_complete, days_delayed_start=days_delayed_start)
        if front_of_queue:
            self._taken_and_planned.insert(0, test)
        else:
            self._taken_and_planned.append(test)
        self._tests_of[person].append(test)

    def tests_of(self, person):
        return [t for t in self._tests_of[person] if t.swab_taken]

    def contains_planned_test_of(self, person):
        return [t for t in self._tests_of[person] if not t.swab_taken]

    def pick_actionable_tests(self, max_processed, logging_overrun=None):
        actionable_tests = []
        tests = [t for t in self.tests]
        for i, t in enumerate(tests):

            if max_processed is not None and i >= max_processed:
                if logging_overrun:
                    logging.info(logging_overrun)
                continue

            if t.days_elapsed >= t.days_to_complete:
                actionable_tests.append(t)

        return actionable_tests

    def update_tests(self, time_delta):
        for t in self._taken_and_planned:
            t.update_time(time_delta)
