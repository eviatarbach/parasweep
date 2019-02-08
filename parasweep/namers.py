"""Namers for generating simulation IDs."""
import math
from abc import ABC, abstractmethod


class Namer(ABC):
    """
    Abstract class for assigning simulation IDs to simulation.

    Only the ``next`` method has to be implemented.
    """

    def start(self, length):
        """
        Initialize naming.

        Parameters
        ----------
        length : int
            Indicates how many total simulations are in the sweep.

        """
        pass

    @abstractmethod
    def generate_id(self, param_set):
        """Generate simulation ID for a given parameter set.

        Parameters
        ----------
        param_set : dict

        """
        pass


class SequentialNamer(Namer):
    """
    Name simulations with consecutive numbers and leading zeros.

    Parameters
    ----------
    zfill : None or int, optional
        If provided, sets the width to which the name string is to be
        padded with zeros.
    start_at : int, optional
        Sets the integer to start at in the sequential naming.

    Examples
    --------
    >>> counter = SequentialNamer()
    >>> counter.start(length=11)
    >>> counter.generate_id({'key1': 'value1'})
    '00'
    >>> counter.generate_id({'key2': 'value2'})
    '01'

    """

    def __init__(self, zfill=None, start_at=0):
        self.zfill_arg = zfill
        self.start_at = start_at

    def start(self, length):
        self.count = self.start_at - 1

        # Need to have `zfill_arg` separate because otherwise state can persist
        # across multiple evaluations of `run_sweep`
        if self.zfill_arg is None:
            # Compute how many digits are needed to represent all the numbers
            self.zfill = (math.floor(math.log10(length - 1) + 1) if length != 1
                          else 1)
        else:
            self.zfill = self.zfill_arg
        self.length = length

    def generate_id(self, param_set):
        if self.count + 1 >= self.length + self.start_at:
            raise StopIteration
        self.count += 1
        return str(self.count).zfill(self.zfill)
