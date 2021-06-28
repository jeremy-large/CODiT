from codit.society import UKSociety


class StrategicTester(UKSociety):

    MIN_CONTACTS_SYMPTOMS = 4
    MIN_CONTACTS = 2

    def act_on_test(self, test, census=None, test_contacts=False):
        UKSociety.act_on_test(self, test, census=census, test_contacts=True)

    def get_test_request(self, person, notes=''):
        if len(person.contacts) < self.MIN_CONTACTS:
            return

        if self.currently_testing(person):
            return

        if notes == 'symptoms':
            if len(person.contacts) >= self.MIN_CONTACTS_SYMPTOMS:
                self.add_test(person, notes)

        elif notes == 'contact':
            # go to the head of the queue:
            self.add_test(person, notes, front_of_queue=True)
