# !/usr/bin/env python

"""
Script to clear any pending alerts in the background.
"""

from codit.population.networks.home_locations import build_households_home_list


def main():
    build_households_home_list()



if __name__ == '__main__':
    main()

