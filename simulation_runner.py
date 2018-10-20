"""
Copyright Eviatar Bach (eviatarbach@protonmail.com) 2015–2018.

Licensed under the MIT License. See license text at
https://opensource.org/licenses/MIT.

Part of simulation_runner, https://github.com/eviatarbach/simulation_runner.
"""
from namers import SequentialNamer
from dispatchers import PythonSubprocessDispatcher
from templates import PythonFormatTemplate, MakoTemplate

import itertools
import time
import operator
from functools import reduce

import numpy
import xarray


def run_sweep(command, config_path, sweep_id=None, template_path=None,
              template_text=None, fixed_parameters={},
              sweep_parameters={}, naming=SequentialNamer(),
              dispatcher=PythonSubprocessDispatcher,
              template_engine=PythonFormatTemplate,
              run=True, verbose=True, delay=False, wait=False):
    r"""
    Run parameter sweeps.

    This function runs the program with the Cartesian product of the parameter
    ranges.

    EXAMPLES:
    >>> run_sweep('cat {sim_id}.txt', '{sim_id}.txt',
    ...           template_text='Hello ${x*10}\n',
    ...           sweep_parameters={'x': [1, 2, 3]}, verbose=False,
    ...           template_engine=MakoTemplate)
    Hello 10
    Hello 20
    Hello 30

    >>> run_sweep('cat {sim_id}.txt', '{sim_id}.txt',
    ...           template_text='Hello ${x*10} ${z}\n',
    ...           sweep_parameters={'x': [1, 2, 3]}, verbose=False,
    ...           template_engine=MakoTemplate)
    NameError: Undefined

    >>> run_sweep('cat {sim_id}.txt', '{sim_id}.txt',
    ...           template_text='Hello ${x*10}\n',
    ...           sweep_parameters={'x': [1, 2, 3], 'y': [4]},
    ...           verbose=False, template_engine=MakoTemplate)
    NameError: The names {'y'} are not used in the template.

    """
    if (((template_path is None) and (template_text is None))
            or (not (template_path is None) and not (template_text is None))):
        raise ValueError('Exactly one of `template_path` or `template_text` must be provided.')

    if template_path:
        config = template_engine(path=template_path)
    else:
        config = template_engine(text=template_text)

    params = fixed_parameters.copy()
    keys = list(sweep_parameters.keys())
    values = list(sweep_parameters.values())
    lengths = [len(value) for value in values]

    if sweep_parameters:
        product = itertools.product(*values)
    else:
        product = [params]

    naming.start(length=reduce(operator.mul, lengths, 1))

    sim_ids = []
    processes = []
    for param_set in product:
        sweep_params = params.copy()
        if keys:
            for index, value in enumerate(param_set):
                sweep_params[keys[index]] = value

        sim_id = naming.next(keys, sweep_params.values())
        sim_ids.append(sim_id)

        config_rendered = config.render(sweep_params).encode('utf-8', 'replace')
        with open(config_path.format(sim_id=sim_id), 'wb') as config_file:
            config_file.write(config_rendered)
        if run:
            if verbose:
                print("Running simulation {sim_id} with parameters:".format(sim_id=sim_id))
                print('\n'.join('{key}: {param}'.format(key=key,
                                                        param=param)
                                for key, param in zip(keys, param_set)))
            proc = dispatcher()
            proc.dispatch(command.format(sim_id=sim_id))
            processes.append(proc)
            if delay:
                time.sleep(delay)

    # Wait until all processes are finished
    if wait:
        for process in processes:
            process.wait()

    sim_ids_array = xarray.DataArray(numpy.reshape(numpy.array(sim_ids),
                                                   lengths),
                                     coords=values, dims=keys)

    if sweep_id:
        sim_ids_filename = 'sim_ids_{sweep_id}.nc'.format(sweep_id=sweep_id)
    else:
        sim_ids_filename = 'sim_ids.nc'

    sim_ids_array.to_netcdf(sim_ids_filename)

    return sim_ids_array
