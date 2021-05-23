import logging
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from codit.outbreakvisualiser import VisualizerComponent
from codit.disease import ifr, hospitalization

from codit.immunity import ImmuneResponse, INFECTIONS


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
        logging.info(f" {self.main_component.story[-1][1] * 100:2.1f} "
                     f"percent of the population was infected during the epidemic")

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

        all_completed_tests = [t for q in o.society.queues for t in q.completed_tests]
        step = [o.time,
                o.pop.count_infected() / N,
                o.pop.count_infectious() / N,
                len(all_completed_tests) / N / o.time_increment,
                sum(len([t for t in q.tests if t.swab_taken]) for q in o.society.queues) / N,
                sum(p.isolating for p in o.pop.people) / N,
                ]
        self.story.append(step)

        if o.step_num % (50 * o.society.episodes_per_day) == 1 or (o.step_num == o.n_periods):
            logging.info(f"Day {int(step[0])}, prop infected is {step[1]:2.2f}, "
                         f"prop infectious is {step[2]:2.4f}")


class MorbidityComponent:
    def __init__(self, people):
        self.naive_haz = sum([ifr(person.age) for person in people])
        self.story = []

    def update(self, o):
        admissions, death, ages = expected_morbidity(o.pop.people)
        self.story.append([o.time, death, admissions, ages])


def expected_morbidity(people, days_to_hospital=8):

    def _sum_weighted_ages(hospitalization_stage):
        return sum([hospitalization(person.age) * person.age for person in hospitalization_stage])

    daily_advancing_stage = [person for person in people
                             if days_to_hospital <= person.days_infected() < days_to_hospital + 1]
    death = sum([ifr(person.age) for person in daily_advancing_stage])
    admissions = sum([hospitalization(person.age) for person in daily_advancing_stage])

    age_at_admission = np.nan
    if admissions > 0:
        age_at_admission = _sum_weighted_ages(daily_advancing_stage) / admissions

    return admissions, death, age_at_admission


class VariantComponent:
    def __init__(self):
        self.story = []

    def update(self, o):
        # count the cases of each variant in the population
        infected_variants = defaultdict(lambda: 0)
        infectious_variants = defaultdict(lambda: 0)
        row = [o.time]
        for v in INFECTIONS:
            row.append(o.pop.count_infected(v))
            row.append(o.pop.count_infectious(v))
        self.story.append(row)

    def columns(self):
        """Get the column for each row in the story"""
        columns = ["time"]
        for v in INFECTIONS:
            columns.append(f"{v.name} infected")
            columns.append(f"{v.name} infectious")
        return columns


class WardComponent:
    def __init__(self, o):
        self.wards = list({p.home.ward for p in o.pop.people if p.home.ward.name})
        self.infected = []
        self.infectious = []
        self.positive_tests = []
        self.expected_death = []
        self.expected_hospitalization = []
        self.hospitalization_age = []
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

        admissions, deaths, ages = zip(*[expected_morbidity(self.people_of[w]) for w in self.wards])
        self.expected_death.append([o.time] + list(deaths))
        self.expected_hospitalization.append([o.time] + list(admissions))
        self.hospitalization_age.append([o.time] + list(ages))

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

    def plot_weekly_positivity(self, days, title=''):
        df = self.story_sorted_by_ward(days + 7, self.positive_tests)[7::7] * 100000
        rates_title = "Weekly positivity rates " + title
        y_legend = "Simulated positive tests per 100,000 of population in the previous week"
        self.plot_all_timeseries(df, rates_title, y_legend)

    def plot_all_timeseries(self, df, rates_title, y_legend):
        ax = df.plot(grid=True, figsize=(12, 8), title=rates_title)
        plt.legend(loc='right', bbox_to_anchor=(1.4, 0.5))
        ax.set_ylabel(y_legend)
        _ = ax.axhline(0, color='k')

    def story_sorted_by_ward(self, days, story, rolling_sum_days=None):
        df = self.dataframe(story)[:days]
        if rolling_sum_days:
            df = df.rolling(rolling_sum_days).sum()
        df = df.T
        order = np.argsort(df.iloc[:, -1:].values, axis=None)  # get the order of the last column
        df = df.iloc[np.flip(order)].T
        return df
