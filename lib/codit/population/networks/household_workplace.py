import networkx as nx
import random
import itertools
import numpy as np
import logging

from codit.population import FixedNetworkPopulation

_h = []
for i in range(6):
    _h = [i * 4 + 1] * (6 - i) ** 2 + _h

HOUSEHOLD_SIZES_OF_REPRESENTATIVE_PEOPLE = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 5, 6, 7]

WORKPLACE_SIZE_REPRESENTATIVE_EXAMPLES = _h


class HouseholdWorkplacePopulation(FixedNetworkPopulation):
    def fix_cliques(self, mean_num_contacts, mean_household_size=2):
        return build_cliques(self.census)


def build_cliques(census):
    people = list(census.values())
    logging.info("Building households")
    household_graph = partition_graph(len(people), HOUSEHOLD_SIZES_OF_REPRESENTATIVE_PEOPLE, 1, 0)
    node_mapping = {i: people[i] for i in range(len(people))}
    households = nx.relabel_nodes(household_graph, node_mapping)
    logging.info("Done households, now moving on to workplaces")

    workplace_graph = partition_graph(len(people), WORKPLACE_SIZE_REPRESENTATIVE_EXAMPLES, 1, 0)
    workplaces = nx.relabel_nodes(workplace_graph, get_shuffle_mapping(people))

    logging.info("Composing households and workplaces")
    full_graph = nx.compose_all([households, workplaces])
    return [{p.name for p in x} for x in nx.find_cliques(full_graph)]


def get_shuffle_mapping(people):
    shuffled_population = [p for p in people]
    random.shuffle(shuffled_population)
    return {i: shuffled_population[i] for i in range(len(people))}


def partition_graph(n, samples, p_in, p_out, directed=False, seed=None, per_population=False):
    if p_in == p_out:
        return nx.erdos_renyi_graph(n, p_in)
    sizes = partition_sizes(n, samples, per_population=per_population)
    if (p_in, p_out) == (1, 0):
        return build_nx_graph(sizes)
    return nx.random_partition_graph(sizes, p_in, p_out, seed=seed, directed=directed)


def build_nx_graph(sizes):
    G = nx.Graph()
    counter = 0
    for s in sizes:
        rng = range(s)
        for i, j in itertools.combinations(rng, 2):
            G.add_edge(counter + i, counter + j)
        counter += s
    return G


def partition_sizes(n_individuals, representative_samples, per_population=True):
    """
    :param n_individuals: number of nodes in this network
    :param representative_samples: [group_size(i) for i in reasonable_sample(population)]
    :param per_population: if False, then representative_samples is rather [size(g) for g in reasonable_sample(groups)]
    :return:
    """
    if per_population:
        size_samples = list(itertools.chain(*([i] * (sum(representative_samples) // i) for i in representative_samples)))
    else:
        size_samples = representative_samples.copy()
    random.shuffle(size_samples)
    logging.info(f"Mean size is {np.mean(size_samples)}")
    assigned = 0
    sizes = []
    i = 0
    while True:
        size = size_samples[i % len(size_samples)]
        if assigned + size >= n_individuals:
            sizes.append(n_individuals - assigned)
            break
        assigned += size
        sizes.append(size)
        i += 1
    return sizes
