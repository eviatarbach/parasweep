from typing import Collection, Any

from .random import *

ndarray = Collection[Any]


def array(object: Collection[Any]) -> ndarray: ...


def reshape(a: ndarray, newshape: Collection[int]) -> ndarray: ...
