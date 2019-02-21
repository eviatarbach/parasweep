"""Namers for generating simulation IDs."""
import math
from abc import ABC, abstractmethod
import json
from typing import Optional, Iterable

from parasweep._annotation_types import ParameterSet


class Namer(ABC):
    """
    Abstract class for assigning simulation IDs to simulation.

    Only the ``next`` method has to be implemented.
    """

    def start(self, length: int) -> None:
        """
        Initialize naming.

        Parameters
        ----------
        length : int
            Indicates how many total simulations are in the sweep.

        """
        pass

    @abstractmethod
    def generate_id(self, param_set: ParameterSet, sweep_id: str) -> str:
        """Generate simulation ID for a given parameter set.

        Parameters
        ----------
        param_set : dict
            The parameter set
        sweep_id : str
            The sweep ID

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
    >>> counter.generate_id({'key1': 'value1'}, '')
    '00'
    >>> counter.generate_id({'key2': 'value2'}, '')
    '01'

    """

    def __init__(self, zfill: Optional[int] = None, start_at: int = 0):
        self.zfill_arg = zfill
        self.start_at = start_at

    def start(self, length: int) -> None:
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

    def generate_id(self, param_set: ParameterSet, sweep_id: str) -> str:
        if self.count + 1 >= self.length + self.start_at:
            raise StopIteration
        self.count += 1
        return str(self.count).zfill(self.zfill)


class HashNamer(Namer):
    """
    Name simulations using hashing.

    Parameters
    ----------
    hash_length : int, optional
        How many hexadecimal numbers to truncate the hash to. 6 by default.

    Examples
    --------
    >>> namer = HashNamer()
    >>> namer.generate_id({'key1': 'value1'}, '')
    '31fc462e'
    >>> namer.generate_id({'key2': 'value2'}, '')
    '9970c8f5'

    """

    def __init__(self, hash_length: int = 8):
        self.hash_length = hash_length

    def generate_id(self, param_set: ParameterSet, sweep_id: str) -> str:
        from hashlib import sha1

        h = sha1()
        h.update(bytes(json.dumps(param_set), 'utf-8'))
        h.update(bytes(sweep_id, 'utf-8'))

        return h.hexdigest()[:self.hash_length]


class SetNamer(Namer):
    """
    Name simulations consecutively with a provided iterable.

    Parameters
    ----------
    names : Iterable[str]
        The sequence of names to assign to consecutive simulations.

    Examples
    --------
    >>> namer = SetNamer(['name1', 'name2'])
    >>> namer.generate_id({'key1': 'value1'}, '')
    'name1'
    >>> namer.generate_id({'key2': 'value2'}, '')
    'name2'

    """

    def __init__(self, names: Iterable[str]):
        self.names = iter(names)

    def generate_id(self, param_set: ParameterSet, sweep_id: str) -> str:
        return next(self.names)
