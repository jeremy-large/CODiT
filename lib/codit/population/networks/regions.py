import pandas as pd
import smart_open

from codit.config import POPULATION_LSOA_CSV


class Place:
    """
    Defined by its name
    """
    def __eq__(self, other):
        return str(self) == str(other)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))


class Building(Place):
    def __init__(self, lon, lat):
        self.lat = lat
        self.lon = lon

    def __str__(self):
        return f"Building at <Lon {self.lon}   Lat {self.lat}>"


class Ward(Place):
    """
    This object will keep all the information about a given ward
    """
    def __init__(self, code, name):
        """
        :param code: string for example 'E05001430'
        :param name: string for example 'Killingbeck and Seacroft'
        In time, this init can pull in other contextual information about the ward such as:
           - population density
           - rural/urban
           - IMD
           - population
           - area
           - amenities
        """
        self.code = code
        self.name = name

    def __str__(self):
        return f"Ward <{self.name} {self.code}>"


with smart_open.open(POPULATION_LSOA_CSV) as fh:
    LSOAs = pd.read_csv(fh)
LSOAs.set_index('lsoa11cd', inplace=True)


class LSOA(Place):
    """
    This object will keep all the information about a given LSOA
    """

    def __init__(self, code, name):
        """
        :param code: string for example 'E09000021'
        :param name: string for example 'Kingston upon Thames'
        """
        self.code = code
        self.name = name
        self.features = LSOAs.loc[self.code].to_dict()

    def __str__(self):
        return f"LSOA <{self.name} {self.code}>"
