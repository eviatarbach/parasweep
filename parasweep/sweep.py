# -*- coding: utf-8 -*-
"""
Main sweep functionality.
"""
from parasweep.namers import SequentialNamer
from parasweep.dispatchers import PythonSubprocessDispatcher
from parasweep.templates import PythonFormatTemplate

import itertools
import time
import operator
import datetime
import os
from functools import reduce


def run_sweep(command, config_paths, template_paths=None, template_texts=None,
              sweep_parameters={}, parameter_sets=[], sweep_id=None,
              naming=SequentialNamer(),
              dispatcher=PythonSubprocessDispatcher(),
              template_engine=PythonFormatTemplate, run=True, delay=0.0,
              serial=False, wait=False, cleanup=False, verbose=True,
              overwrite=True, mapping=True):
    r"""
    Run parameter sweeps.

    This function runs the program with the Cartesian product of the parameter
    ranges.

    Parameters
    ----------
    command : str
        The command to run. Must include '{sim_id}' indicating where the
        simulation ID is to be inserted.
    config_paths : list
        List of paths indicating where the configuration files should be saved
        after substitution of the parameters into the templates. Must be in the
        same order as `template_paths` or `template_texts`.
    Either
        **template_paths** (*list*)
            List of paths of templates to substitute parameters into. Must be
            in the same order as `config_paths`. Or,
        **template_texts** (*list*)
            List of template strings to substitute parameters into. Must be
            in the same order as `config_paths`.
    Either
        **sweep_parameters** (*dict*):
            Using this option will do a grid sweep (Cartesian product).
            Dictionary where the keys are the parameter names and the values
            are lists of parameter values to sweep over. E.g.,
            `{'x': [1, 2], 'y': [3, 4]}`. Or,
        **parameter_sets** (*list*):
            Using this option will run a sweep with the provided parameter
            sets. List of dictionaries where the keys are the parameter names
            and the values are the fixed parameter values. E.g.,
            `[{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]`
    sweep_id : str, optional
        A name for the sweep. By default, the name is generated automatically
        from the date and time.
    naming : namers.Namer instance, optional
        A :class:`parasweep.namers.Namer` object that specifies how to assign
        simulation IDs. By default, assigns simulation IDs sequentially.
    dispatcher : dispatchers.Dispatcher instance, optional
        A :class:`parasweep.dispatchers.Dispatcher` object that specifies how
        to run the jobs. By default, uses Python's `subprocess` module.
    template_engine : templates.Template class, optional
        A :class:`parasweep.templates.Template` class that specifies the
        template engine to use. By default, uses Python format strings.
    run : bool, optional
        Whether to run the parameter sweep. True by default.
    delay : float, optional
        How many seconds to delay between running successive simulations.
        0.0 by default.
    serial : bool, optional
        Whether to run simulations serially, i.e., to wait for each simulation
        to complete before executing the next one. Enabling this turns off
        parallelism. False by default.
    wait : bool, optional
        Whether to wait for all simulations to complete before returning.
        False by default.
    cleanup : bool, optional
        Whether to delete configuration files after all the simulations are
        done. This will cause the command to wait on all processes before
        returning (as with the `wait` argument). False by default.
    verbose : bool, optional
        Whether to print some information about each simulation as it is
        launched. True by default.
    overwrite : bool, optional
        Whether to overwrite existing files when creating configuration files.
        If False, a `FileExistsError` will be raised when a configuration
        filename coincides with an existing one in the same directory. True by
        default.
    mapping : bool, optional
        Whether to return a mapping between the parameters to the simulation
        IDs. If the sweep is a grid sweep, an N-dimensional labelled array
        (using `xarray`) which maps the parameters to the simulation IDs will
        be returned. The array coordinates correspond to each sweep parameter,
        while the values contain the simulation IDs. This array will also be
        saved as a netCDF file with the name 'sim_ids_{sweep_id}.nc'. If
        instead specific parameter sets are provided (using the
        `parameter_sets` argument) then a dictionary mapping the simulation IDs
        to the parameter sets will be returned. True by default.

    Examples
    --------
    An example of the basic formatting that can be done with the Python
    formatting templates:

    >>> from parasweep import run_sweep
    >>> run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
    ...           template_texts=['Hello {x:.2f}\n'],
    ...           sweep_parameters={'x': [1/3, 2/3, 3/3]},
    ...           verbose=False, mapping=False)
    Hello 0.33
    Hello 0.67
    Hello 1.00

    Mako templates provide functionality that is not available with Python
    formatting templates, being able to insert code within the template:

    >>> from parasweep.templates import MakoTemplate
    >>> run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
    ...           template_texts=['Hello ${x*10}\n'],
    ...           sweep_parameters={'x': [1, 2, 3]}, verbose=False,
    ...           template_engine=MakoTemplate, mapping=False)
    Hello 10
    Hello 20
    Hello 30

    Multiple configuration files and their corresponding templates can be used:

    >>> run_sweep(command='cat {sim_id}_1.txt {sim_id}_2.txt',
    ...           config_paths=['{sim_id}_1.txt', '{sim_id}_2.txt'],
    ...           template_texts=['Hello {x:.2f}\n',
    ...                           'Hello again {y}\n'],
    ...           sweep_parameters={'x': [1/3, 2/3, 3/3], 'y': [4]},
    ...           verbose=False, mapping=False)
    Hello 0.33
    Hello again 4
    Hello 0.67
    Hello again 4
    Hello 1.00
    Hello again 4

    By default (if `mapping` is True), a mapping will be returned between
    the parameters and the simulation IDs, which facilitates postprocessing::

        >>> run_sweep('cat {sim_id}.txt >> out', ['{sim_id}.txt'],
        ...           template_texts=['Hello {x} {y} {z}\n'],
        ...           sweep_parameters={'x': [1, 2], 'y': [3, 4, 5],
        ...                             'z': [6, 7, 8, 9]})
        <xarray.DataArray 'sim_id' (x: 2, y: 3, z: 4)>
        array([[['0', '1', '2', '3'],
                ['4', '5', '6', '7'],
                ['8', '9', '10', '11']],

               [['12', '13', '14', '15'],
                ['16', '17', '18', '19'],
                ['20', '21', '22', '23']]], dtype='<U2')
        Coordinates:
          * x        (x) int64 1 2
          * y        (y) int64 3 4 5
          * z        (z) int64 6 7 8 9


    The default sweep is a Cartesian sweep, meaning that all the combinations
    of all the parameters are used (every member in the Cartesian product of
    the parameter values). Alternatively, specific parameter sets can be used:

    >>> mapping = run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
    ...                     template_texts=['Hello {x}, {y}, {z}\n'],
    ...                     parameter_sets=[{'x': 2, 'y': 8, 'z': 5},
    ...                                     {'x': 1, 'y': -4, 'z': 9}],
    ...                     verbose=False)
    Hello 2, 8, 5
    Hello 1, -4, 9

    In the case that parameter sets are used, the parameter mapping is a
    dictionary like the following:

    >>> mapping
    {'0': {'x': 2, 'y': 8, 'z': 5}, '1': {'x': 1, 'y': -4, 'z': 9}}

    """
    if (((template_paths is None) and (template_texts is None))
            or (not (template_paths is None)
                and not (template_texts is None))):
        raise ValueError('Exactly one of `template_paths` or `template_texts` '
                         'must be provided.')

    if ((sweep_parameters and parameter_sets)
            or (not sweep_parameters and not parameter_sets)):
        raise ValueError('Exactly one of `sweep_parameters` or '
                         '`parameter_sets` must be provided.')

    if (isinstance(config_paths, str) or isinstance(template_paths, str)
            or isinstance(template_texts, str)):
        raise TypeError('`config_paths` and `template_paths` or'
                        '`template_texts` must be a list.')

    if not sweep_id:
        current_time = datetime.datetime.now()
        sweep_id = current_time.strftime('%Y-%m-%dT%H:%M:%S')

    if template_paths:
        config = template_engine(paths=template_paths)
    else:
        config = template_engine(texts=template_texts)

    if sweep_parameters:
        keys = list(sweep_parameters.keys())
        values = list(sweep_parameters.values())

        product = itertools.product(*values)
        lengths = [len(value) for value in values]
        sweep_length = reduce(operator.mul, lengths, 1)
    else:
        keys = parameter_sets[0].keys()

        product = parameter_sets
        sweep_length = len(parameter_sets)

    naming.start(length=sweep_length)

    sim_ids = []
    config_filenames = []

    if run:
        dispatcher.initialize_session()

    for param_set in product:
        if sweep_parameters:
            sweep_params = {}
            for index, value in enumerate(param_set):
                sweep_params[keys[index]] = value
        else:
            sweep_params = param_set

        sim_id = naming.next(keys, sweep_params.values())
        sim_ids.append(sim_id)

        rendered = config.render(sweep_params)
        for config_rendered, config_path in zip(rendered, config_paths):
            config_filename = config_path.format(sim_id=sim_id)
            config_filenames.append(config_filename)
            if not overwrite:
                if os.path.isfile(config_filename):
                    raise FileExistsError(f'{config_filename} exists, set '
                                          '`overwrite` to True to overwrite.')
            with open(config_filename, 'wb') as config_file:
                config_file.write(config_rendered.encode('utf-8', 'replace'))
        if run:
            if verbose:
                print(f'Running simulation {sim_id} with parameters:')
                print('\n'.join(f'{key}: {param}' for key, param
                                in sweep_params.items()))
            dispatcher.dispatch(command.format(sim_id=sim_id), serial)
            if delay:
                time.sleep(delay)

    if wait and run:
        dispatcher.wait_all()

    if cleanup and run:
        dispatcher.wait_all()
        for config_filename in config_filenames:
            os.remove(config_filename)

    if mapping and sweep_parameters:
        import xarray
        import numpy

        sim_ids_array = xarray.DataArray(numpy.reshape(numpy.array(sim_ids),
                                                       lengths),
                                         coords=values, dims=keys,
                                         name='sim_id')

        sim_ids_filename = f'sim_ids_{sweep_id}.nc'

        sim_ids_array.to_netcdf(sim_ids_filename)

        return sim_ids_array
    elif mapping and parameter_sets:
        return dict(zip(sim_ids, parameter_sets))
