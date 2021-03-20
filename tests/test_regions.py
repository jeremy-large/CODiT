from codit.population.networks import home_locations
import pytest
import numpy

"""
Note these tests can be destabilised if we change default files so that they refer to a new city.
Indeed, we plan to do this in the near future.
"""


def test_lsoa_allocation():
    df = home_locations.allocate_coordinates_to_districts('LSOA', test=True)
    assert df.shape == (2227, 6)
    assert df.describe().sum().sum() == pytest.approx(739097.0571)
    assert df.lsoa_code.apply(lambda x: not x).sum() == 1804


def test_ward_allocation():
    df = home_locations.allocate_coordinates_to_districts('Ward', test=True)
    assert df.shape == (2227, 6)
    assert df.describe().sum().sum() == pytest.approx(739097.0571)
    assert df.ward_code.apply(lambda x: not x).sum() == 1713


def test_build_home_list():
    numpy.random.seed(42)
    df = home_locations.build_households_home_list(test=True)
    assert df.shape == (271781, 7)
    assert df.describe().sum().sum() == pytest.approx(543875.654865)


