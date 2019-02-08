from abc import ABC, abstractmethod
import itertools
import operator
from functools import reduce
import json


def _sparse_mapping(parameter_sets, sim_ids, sweep_id, save):
    """
    Mapping function for sparse sweeps (not a full `n`-dimensional array).

    Returns a dictionary mapping simulation IDs to the parameter set used for
    that simulation.
    """
    sim_id_mapping = dict(zip(sim_ids, parameter_sets))

    if save:
        sim_ids_filename = 'sim_ids_{}.json'.format(sweep_id)

        with open(sim_ids_filename, 'w') as sim_ids_file:
            json.dump(sim_id_mapping, sim_ids_file)

    return sim_id_mapping


class Sweep(ABC):
    """
    Abstract class for parameter sweep types.

    Sweeps must define an initialization using ``__init__``, the sweep length
    using ``__len__``, an iteration using ``elements``, and a type of mapping
    using ``mapping``.
    """

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def __len__(self):
        """Return the number of elements of the sweep."""
        pass

    @abstractmethod
    def elements(self):
        """
        Return the elements of the sweep.

        May be lazily evaluated, depending on the type of sweep.
        """
        pass

    @abstractmethod
    def mapping(self, sim_ids, sweep_id, save=True):
        """
        Return a mapping between the simulation IDs and the parameter sets.

        The mapping may be from simulation IDs to parameter sets or vice-versa,
        depending on what is convenient for the type of sweep.

        Parameters
        ----------
        sim_ids : list
            The simulation IDs that were assigned to each parameter set, in the
            same order as returned by ``elements``.
        sweep_id : str
            The sweep ID
        save : bool
            Whether to save the mapping to disk. The filename should be of the
            form ``sim_ids_{sweep_id}``, with an extension depending on the
            mapping type. True by default.

        """
        pass


class CartesianSweep(Sweep):
    """
    A Cartesian product parameter sweep.

    Parameters
    ----------
    sweep_params : dict
        A dictionary containing the parameter names as keys and lists of values
        to sweep over as values.

    """
    def __init__(self, sweep_params):
        self.keys = list(sweep_params.keys())
        self.values = list(sweep_params.values())
        self.filter = filter

        self.lengths = [len(value) for value in self.values]

    def __len__(self):
        return reduce(operator.mul, self.lengths, 1)

    def elements(self):
        product = itertools.product(*self.values)

        return (dict(zip(self.keys, element)) for element in product)

    def mapping(self, sim_ids, sweep_id, save=True):
        """
        Return a labelled array which maps parameters to simulation IDs.

        See :func:`parasweep.sweepers.Sweep.mapping` for argument information.
        Returns a multidimensional labelled array (using xarray) which maps
        the parameters to the simulation IDs. The array coordinates correspond
        to each sweep parameter, while the values contain the simulation IDs.
        If ``save=True``, this array will be saved as a netCDF file with the
        name ``sim_ids_{sweep_id}.nc``.

        """
        import xarray
        import numpy

        sim_ids_array = xarray.DataArray(numpy.reshape(numpy.array(sim_ids),
                                                       self.lengths),
                                         coords=self.values, dims=self.keys,
                                         name='sim_id')

        if save:
            sim_ids_filename = 'sim_ids_{}.nc'.format(sweep_id)
            sim_ids_array.to_netcdf(sim_ids_filename)

        return sim_ids_array


class FilteredCartesianSweep(Sweep):
    """
    A parameter sweep which uses specified parameter sets.

    Parameters
    ----------
    sweep_params : dict
        A dictionary containing the parameter names as keys and lists of values
        to sweep over as values.
    filter_func : function
        A boolean function of parameter values; only parameter sets that
        return true will be included in the sweep. The arguments of the
        function should be named after the corresponding parameters. If not all
        the parameters in the sweep are used in the filtering, the ``**kwargs``
        argument should be defined, or else an error will be raised.

    """
    def __init__(self, sweep_params, filter_func):
        self.keys = list(sweep_params.keys())
        self.values = list(sweep_params.values())

        product = itertools.product(*self.values)

        # Here we cannot do lazy evaluation since we need the length of the
        # filtered elements.
        product_dicts = [dict(zip(self.keys, element)) for element in product]
        self.filtered = list(filter(lambda d: filter_func(**d), product_dicts))

    def __len__(self):
        return len(self.filtered)

    def elements(self):
        return self.filtered

    def mapping(self, sim_ids, sweep_id, save=True):
        """
        Return a dictionary which maps simulation IDs to parameter sets.

        See :func:`parasweep.sweepers.Sweep.mapping` for argument information.
        If ``save=True``, this dictionary will be saved as a JSON file with the
        name ``sim_ids_{sweep_id}.json``.
        """
        return _sparse_mapping(self.filtered, sim_ids, sweep_id, save)


class SetSweep(Sweep):
    """
    A Cartesian product parameter sweep with filtering.

    Parameters
    ----------
    param_sets : list
        A list containing the parameter sets to use in the sweep as
        dictionaries.

    """
    def __init__(self, param_sets):
        self.parameter_sets = param_sets
        self.keys = param_sets[0].keys()

    def __len__(self):
        return len(self.parameter_sets)

    def elements(self):
        return self.parameter_sets

    def mapping(self, sim_ids, sweep_id, save=True):
        """
        Return a dictionary which maps simulation IDs to parameter sets.

        See :func:`parasweep.sweepers.Sweep.mapping` for argument information.
        If ``save=True``, this dictionary will be saved as a JSON file with the
        name ``sim_ids_{sweep_id}.json``.
        """
        return _sparse_mapping(self.parameter_sets, sim_ids, sweep_id, save)
