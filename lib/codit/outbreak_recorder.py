import logging
import numpy as np

import pandas as pd
from codit.outbreakvisualiser import VisualizerComponent


class OutbreakRecorder:
    def __init__(self, o, show_heatmap=False):
        self.realized_r0 = None
        self.components = [MainComponent()]
        if show_heatmap:
            self.components.append(VisualizerComponent(False, o))
        self.main_component = self.components[0]

    def add_component(self, component):
        self.components.append(component)

    def record_step(self, o):
        for component in self.components:
            component.update(o)

    def plot(self, **kwargs):
        df = self.get_dataframe()
        ax = (df.drop(columns=['ever infected']) * 100).plot(grid=True, **kwargs)
        ax.set_ylabel("percent of the population")
        logging.info(f" Realized R0 of early infections is {self.realized_r0:2.2f}")
        logging.info(f" {self.main_component.story[-1][1] * 100:2.1f} percent of the proportion was infected during the epidemic")

    def get_dataframe(self):
        df = pd.DataFrame(self.main_component.story)
        df.columns = ['days of epidemic', 'ever infected', 'infectious',
                      'tested daily', 'waiting for test results', 'isolating']  # , 'daily_detected_']
        df = df.set_index('days of epidemic')
        return df


class MainComponent:
    def __init__(self):
        self.story = []

    def update(self, o):
        N = len(o.pop.people)
        # pot_haz = sum([covid_hazard(person.age) for person in o.pop.people])
        # tot_haz = sum([covid_hazard(person.age) for person in o.pop.infected()])

        all_completed_tests = [t for q in o.society.queues for t in q.completed_tests]
        step = [o.time,
                o.pop.count_infected() / N,
                o.pop.count_infectious() / N,
                len(all_completed_tests) / N / o.time_increment,
                sum(len([t for t in q.tests if t.swab_taken]) for q in o.society.queues) / N,
                sum(p.isolating for p in o.pop.people) / N,
                # len([t for t in all_completed_tests if t.positive]) / N / o.time_increment,
                # tot_haz/pot_haz,
                ]
        self.story.append(step)

        # wards = {p.home.ward for p in o.pop.people}
        # step_wards = [wards, [o.pop.count_infected(d, lamda)]]

        if o.step_num % (50 * o.society.episodes_per_day) == 1 or (o.step_num == o.n_periods):
            logging.info(f"Day {int(step[0])}, prop infected is {step[1]:2.2f}, "
                         f"prop infectious is {step[2]:2.4f}")


class VariantComponent:
    def __init__(self):
        self.story = []

    def update(self, o):
        variants = list({d for p in o.pop.people for d in p.covid_experiences})
        self.story.append([o.time,
                           variants,
                           [o.pop.count_infected(d) for d in variants],
                           [o.pop.count_infectious(d) for d in variants]])


class WardComponent:
    def __init__(self, o):
        self.wards = list({p.home.ward for p in o.pop.people if p.home.ward.name})
        self.infected = []
        self.infectious = []
        self.positive_tests = []
        self._pos_week = []
        self.people_of = dict()
        for ward in self.wards:
            self.people_of[ward] = [p for p in o.pop.people if p.home.ward == ward]

    def update(self, o):
        self.infected.append([o.time] +
                             [sum([p.infected for p in self.people_of[w]]) / len(self.people_of[w]) for w in self.wards]
                             )

        self.infectious.append([o.time] +
                               [sum([p.infectious for p in self.people_of[w]]) / len(self.people_of[w]) for w in
                                self.wards]
                               )
        pos_tests = [t for q in o.society.queues for t in q.completed_tests if t.positive]

        self._pos_week.append([len([t for t in pos_tests if t.person.home.ward == w]) for w in self.wards])
        if len(self._pos_week) > 7:
            # TODO using a 7 above is ad-hoc
            self._pos_week = self._pos_week[1:]

        self.positive_tests.append([o.time] +
                               [sum(d[i] for d in self._pos_week)
                                / len(self.people_of[w]) for i, w in enumerate(self.wards)]
                               )

    def dataframe(self, story):
        df = pd.DataFrame(story)
        df.columns = ['days of epidemic'] + [w.name for w in self.wards]
        df = df.T
        order = np.argsort(df.iloc[:, -1:].values, axis=None)  # get the order of the last column
        df = df.iloc[np.flip(order)].T
        return df.set_index('days of epidemic')
