from typing import Collection, Any

import numpy


class DataArray:
    def __init__(self, data: numpy.ndarray,
                 coords: Collection[Collection[Any]], dims: Collection[str],
                 name: str): ...

    def to_netcdf(self, path: str) -> None: ...
