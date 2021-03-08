

class Ward:
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

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return f"Ward <{self.name} {self.code}>"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))
