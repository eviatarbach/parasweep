========
Examples
========

As a toy "simulation", in these examples we make use of the standard Unix
command ``cat``, which concatenates the files given to it as arguments and
prints the results.

Sweeps
------

CartesianSweep
~~~~~~~~~~~~~~

In a Cartesian sweep, all the combinations of all the parameters are used
(every member in the Cartesian product of the sets of parameter values).

**template.txt**::

    Hello {x}, {y}, {z}

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=CartesianSweep({'x': [1, 2],
    ...                                           'y': [3, 4, 5],
    ...                                           'z': [6, 7]}),
    ...                     verbose=False, sweep_id='test')
    Hello 1, 3, 6
    Hello 1, 3, 7
    Hello 1, 4, 6
    Hello 1, 4, 7
    Hello 1, 5, 6
    Hello 1, 5, 7
    Hello 2, 3, 6
    Hello 2, 3, 7
    Hello 2, 4, 6
    Hello 2, 4, 7
    Hello 2, 5, 6
    Hello 2, 5, 7

.. Note:: Although the commands may execute in the order shown above, this is
   not guaranteed since the simulations are dispatched in parallel. To run
   serially, the option ``serial=True`` can be set.

An xarray ``DataArray`` will be returned between the parameters and the
simulation IDs, which facilitates postprocessing::

    >>> mapping
    <xarray.DataArray 'sim_id' (x: 2, y: 3, z: 2)>
    array([[['test_00', 'test_01'],
            ['test_02', 'test_03'],
            ['test_04', 'test_05']],

           [['test_06', 'test_07'],
            ['test_08', 'test_09'],
            ['test_10', 'test_11']]], dtype='<U7')
    Coordinates:
      * x        (x) int64 1 2
      * y        (y) int64 3 4 5
      * z        (z) int64 6 7

In this case, it is three-dimensional, since three parameters are being swept
over.

FilteredCartesianSweep
~~~~~~~~~~~~~~~~~~~~~~

There is also a filtered Cartesian sweep, allowing for a Cartesian sweep
where only elements meeting satisfying some condition on the parameters
are used. For example, suppose we want to sweep over ``x``, ``y``, and ``z``
but only include those parameter sets where ``x > y``:

**template.txt**::

    Hello {x}, {y}, {z}

**Command**::

    >>> from parasweep import run_sweep, FilteredCartesianSweep
    >>> sweep = FilteredCartesianSweep({'x': [1, 2, 3], 'y': [1, 2, 3],
    ...                                 'z': [4, 5]},
    ...                                filter_func=lambda x, y, **kwargs: x > y)
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'], sweep=sweep,
    ...                     verbose=False, sweep_id='test')
    Hello 2, 1, 4
    Hello 2, 1, 5
    Hello 3, 1, 4
    Hello 3, 1, 5
    Hello 3, 2, 4
    Hello 3, 2, 5

.. Note:: Parameters that are not used in the filtering function, ``z`` in this
   case, can be ignored in ``filter_func`` by using the ``**kwargs`` argument.

In this case, the parameter mapping is a dictionary like the following::

    >>> mapping
    {'test_0': {'x': 2, 'y': 1, 'z': 4},
     'test_1': {'x': 2, 'y': 1, 'z': 5},
     'test_2': {'x': 3, 'y': 1, 'z': 4},
     'test_3': {'x': 3, 'y': 1, 'z': 5},
     'test_4': {'x': 3, 'y': 2, 'z': 4},
     'test_5': {'x': 3, 'y': 2, 'z': 5}}

SetSweep
~~~~~~~~

Instead of a Cartesian sweep, specific parameter sets can be used with
``SetSweep``:

**template.txt**::

    Hello {x}, {y}, {z}

**Command**::

    >>> from parasweep import run_sweep, SetSweep
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=SetSweep([{'x': 2, 'y': 8, 'z': 5},
    ...                                     {'x': 1, 'y': -4, 'z': 9}]),
    ...                     verbose=False, sweep_id='test')
    Hello 2, 8, 5
    Hello 1, -4, 9

Here, as with ``FilteredCartesianSweep``, the parameter mapping is a
dictionary::

    >>> mapping
    {'test_0': {'x': 2, 'y': 8, 'z': 5}, 'test_1': {'x': 1, 'y': -4, 'z': 9}}

RandomSweep
~~~~~~~~~~~

There is also a random sweep, where parameters are drawn from independent
random distributions.

**template.txt**::

    Hello {x}, {y}

**Command**::

    >>> import scipy.stats
    >>> from parasweep import run_sweep, RandomSweep
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=RandomSweep({'x': scipy.stats.norm(),
    ...                                        'y': scipy.stats.uniform()},
    ...                                       length=3),
    ...                     verbose=False, sweep_id='test')
    Hello 0.9533238364874957, 0.8197338171659898
    Hello -1.966220661588362, 0.3213785864763252
    Hello -0.057572896338656816, 0.17615488655036005

Here, ``x`` is drawn from a standard normal distribution and ``y`` is uniform
between 0 and 1.

The parameter mapping is again a dictionary::

    >>> mapping
    {'test_0': {'x': 0.9533238364874957, 'y': 0.8197338171659898},
     'test_1': {'x': -1.966220661588362, 'y': 0.3213785864763252},
     'test_2': {'x': -0.057572896338656816, 'y': 0.17615488655036005}}

Multiple configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multiple configuration files and their corresponding templates can be used:

**template1.txt**::

    Hello {x},

**template2.txt**::

    hello again {y}

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> mapping = run_sweep(command='cat {sim_id}_1.txt {sim_id}_2.txt',
    ...                     configs=['{sim_id}_1.txt', '{sim_id}_2.txt'],
    ...                     templates=['template1.txt', 'template2.txt'],
    ...                     sweep=CartesianSweep({'x': [1, 2, 3],
    ...                                           'y': [4]}),
    ...                     verbose=False)
    Hello 1,
    hello again 4
    Hello 2,
    hello again 4
    Hello 3,
    hello again 4

Sweep IDs
~~~~~~~~~

Sweep IDs are used to name the mapping structure if it is saved to disk, and
also in assigning simulation IDs in some cases. If it is not provided
explicitly it is generated based on the current time.

**template.txt**::

    Hello {x},

**Command**::

    >>> import os
    >>> from parasweep import run_sweep, CartesianSweep
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=CartesianSweep({'x': [1, 2, 3]}),
    ...                     verbose=False, sweep_id='test_sweep')
    Hello 1
    Hello 2
    Hello 3
    >>> os.path.exists('sim_ids_test_sweep.nc')
    True

Dispatchers
-----------

Number of processes
~~~~~~~~~~~~~~~~~~~

By default, the maximum number of processes run simultaneously with
``SubprocessDispatcher`` is equal to the number of processors on the machine.
We can choose a custom number, however.

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> from parasweep.dispatchers import SubprocessDispatcher
    >>> dispatcher = SubprocessDispatcher(max_procs=2)

This dispatcher should then be passed to ``run_sweep`` as the ``dispatcher``
argument.

DRMAA
~~~~~

Instead of dispatching simulations with Python's ``subprocess`` module, we can
use the Distributed Resource Management Application API (DRMAA) to interface
with a number of high-performance computing systems. The following example
assumes that DRMAA and an interface to a job scheduler are installed.

**template.txt**::

    Hello {x}

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> from parasweep.dispatchers import DRMAADispatcher

We can specify a ``JobTemplate`` which specifies job options for DRMAA. Here,
we set errors to output to ``err_test.txt``.

    >>> from drmaa import JobTemplate
    >>> jt = JobTemplate(errorPath=':err_test.txt')

.. Note:: Some options specific to each job scheduler, called the native
   specification, may have to be set using the
   ``job_template.nativeSpecification`` attribute, the options for which can be
   found in the job scheduler's DRMAA interface (e.g., slurm-drmaa for Slurm
   and pbs-drmaa for PBS).

We set the command to print the contents of the configuration file to
``stderr`` (this syntax may only work on bash)::

   >>> mapping = run_sweep(command='>&2 cat {sim_id}.txt',
   ...                     configs=['{sim_id}.txt'],
   ...                     templates=['template.txt'],
   ...                     sweep=CartesianSweep({'x': [1]}),
   ...                     verbose=False, dispatcher=DRMAADispatcher(jt))
   >>> with open('err_test.txt', 'r') as err_file:
   ...     print(err_file.read())
   Hello 1

Template engines
----------------

Formatting
~~~~~~~~~~

The following is an example of the basic formatting that can be done with the
Python formatting templates:

**template.txt**::

    Hello {x:.2f}

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=CartesianSweep({'x': [1/3, 2/3, 3/3]}),
    ...                     verbose=False)
    Hello 0.33
    Hello 0.67
    Hello 1.00

Mako templates
~~~~~~~~~~~~~~

Mako templates provide functionality that is not available with Python
formatting templates, being able to insert code within the template:

**template.txt**::

    Hello ${x*10}

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> from parasweep.templates import MakoTemplate
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=CartesianSweep({'x': [1, 2, 3]}),
    ...                     verbose=False, template_engine=MakoTemplate())
    Hello 10
    Hello 20
    Hello 30

Naming
------

HashNamer
~~~~~~~~~

In the case where many parameter sweeps are run on the same model, it may be
helpful to use ``HashNamer`` to avoid collision of the output files.

**template.txt**::

    Hello {x}

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> from parasweep.namers import HashNamer
    >>> mapping = run_sweep(command='echo {sim_id}',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=CartesianSweep({'x': [1, 2, 3]}),
    ...                     namer=HashNamer(), verbose=False)
    16bcb7a1
    7e3245fa
    1780e76b

.. Note:: The hash for each parameter set is generated based on the parameter
   set itself as well as the sweep ID. Thus if the sweep IDs are different,
   hashes will vary between sweeps even if the parameters sets are identical.
   If ``sweep_id`` is not provided as an argument to ``run_sweep`` it will be
   generated based on the current time.
