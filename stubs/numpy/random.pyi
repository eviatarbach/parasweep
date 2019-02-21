from typing import Collection, Any


ndarray = Collection[Any]


def array(object: Collection[Any]) -> ndarray: ...


def reshape(a: ndarray, newshape: Collection[int]) -> ndarray: ...


class RandomState:
    def __init__(self, seed: int): ...
