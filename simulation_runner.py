"""
Copyright Eviatar Bach (eviatarbach@protonmail.com) 2015–2018.

Licensed under the MIT License. See license text at
https://opensource.org/licenses/MIT.

Part of simulation_runner, https://github.com/eviatarbach/simulation_runner.
"""
import subprocess
import itertools
import time
import math
import operator
from functools import reduce
from abc import ABC, abstractmethod

from mako.template import Template
import numpy
import xarray


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
    >>> counter = Sequential()
    >>> counter.start(length=11)
    >>> counter.next(['key1'], [['key_value1']])
    '00'
    >>> counter.next(['key2'], [['key_value2']])
    '01'

    >>> counter = Sequential(zfill=3, start_at=3)
    >>> counter.start(length=2)
    >>> counter.next(['key1'], [['key_value1']])
    '003'
    >>> counter.next(['key2'], [['key_value2']])
    '004'
    >>> counter.next(['key3'], [['key_value3']])
    StopIteration

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


class _Dispatcher(ABC):

    @abstractmethod
    def dispatch(self, command):
        pass


class PythonSubprocessDispatcher(_Dispatcher):

    def dispatch(self, command):
        self.process = subprocess.Popen(command, shell=True)
        return self

    def wait(self):
        self.process.wait()


def run_simulation(command, config_path, sweep_id=None, template_path=None,
                   template_text=None, fixed_parameters={},
                   sweep_parameters={}, naming=SequentialNamer(),
                   dispatcher=PythonSubprocessDispatcher,
                   run=True, verbose=True, delay=False, wait=False):
    r"""
    Run parameter sweeps.

    EXAMPLES:
    >>> run_simulation('cat {sim_id}.txt', '{sim_id}.txt',
    ...                template_text='Hello ${x*10}\n',
    ...                sweep_parameters={'x': [1, 2, 3]}, verbose=False)
    Hello 10
    Hello 20
    Hello 30

    """
    if (((template_path is None) and (template_text is None))
            or (not (template_path is None) and not (template_text is None))):
        raise ValueError('Exactly one of `template_path` or `template_text` must be provided.')

    params = fixed_parameters.copy()
    keys = list(sweep_parameters.keys())
    values = list(sweep_parameters.values())
    lengths = [len(value) for value in values]

    if sweep_parameters:
        product = itertools.product(*values)
    else:
        product = [params]

    if template_path:
        config = Template(filename=template_path, input_encoding='utf-8')
    else:
        config = Template(text=template_text, input_encoding='utf-8')

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

        config_rendered = config.render_unicode(**sweep_params).encode('utf-8', 'replace')
        config_file = open(config_path.format(sim_id=sim_id), 'wb')
        config_file.write(config_rendered)
        config_file.close()
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
