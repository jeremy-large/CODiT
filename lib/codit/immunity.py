from enum import IntFlag, auto

class ImmuneResponse(IntFlag):
    SARS_CoV_2_INFECTION = auto()
    B_1_1_7_INFECTION = auto()
    B_1_617_2_INFECTION = auto()
    ASTRAZENECA_1ST_DOSE = auto()
    PFIZER_1ST_DOSE = auto()
    MODERNA_1ST_DOSE = auto()

    def __iter__(self):
        n = int(self.value)
        while n:
            b = n & (~n + 1)
            yield ImmuneResponse(b)
            n ^= b
