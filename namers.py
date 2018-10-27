import math
from abc import ABC, abstractmethod


class _Namer(ABC):
    """
    Abstract class for assigning simulation IDs to simulation.

    Only the `next` method has to be implemented.
    """

    def start(self, length):
        pass

    @abstractmethod
    def next(self, keys, param_set):
        """Generate simulation ID for a given parameter set."""
        pass


class SequentialNamer(_Namer):
    """
    Name simulations with consecutive numbers and leading zeros.

    EXAMPLES:
    >>> counter = SequentialNamer()
    >>> counter.start(length=11)
    >>> counter.next(['key1'], [['key_value1']])
    '00'
    >>> counter.next(['key2'], [['key_value2']])
    '01'

    """

    def __init__(self, zfill=None, start_at=0):
        self.zfill = zfill
        self.start_at = start_at

    def start(self, length):
        """Initialize counter."""
        self.count = self.start_at - 1
        if self.zfill is None:
            # Compute how many digits are needed to represent all the numbers
            self.zfill = math.floor(math.log10(length - 1) + 1)
        self.length = length

    def next(self, keys, param_set):
        """Return next simulation ID."""
        if self.count + 1 >= self.length + self.start_at:
            raise StopIteration
        self.count += 1
        return str(self.count).zfill(self.zfill)
