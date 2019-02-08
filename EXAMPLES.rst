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

    Hello {x}, {y}, {z}\n

**Command**::

    >>> from parasweep import run_sweep, CartesianSweep
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=CartesianSweep({'x': [1, 2],
    ...                                           'y': [3, 4, 5],
    ...                                           'z': [6, 7]}),
    ...                     verbose=False)
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
    array([[['00', '01'],
            ['02', '03'],
            ['04', '05']],

           [['06', '07'],
            ['08', '09'],
            ['10', '11']]], dtype='<U2')
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

    Hello {x}, {y}, {z}\n

**Command**::

    >>> from parasweep import run_sweep, FilteredCartesianSweep
    >>> sweep = FilteredCartesianSweep({'x': [1, 2, 3], 'y': [1, 2, 3],
    ...                                 'z': [4, 5]},
    ...                                filter_func=lambda x, y, **kwargs: x > y)
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'], sweep=sweep,
    ...                     verbose=False)
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
    {'0': {'x': 2, 'y': 1, 'z': 4},
     '1': {'x': 2, 'y': 1, 'z': 5},
     '2': {'x': 3, 'y': 1, 'z': 4},
     '3': {'x': 3, 'y': 1, 'z': 5},
     '4': {'x': 3, 'y': 2, 'z': 4},
     '5': {'x': 3, 'y': 2, 'z': 5}}

SetSweep
~~~~~~~~

Instead of a Cartesian sweep, specific parameter sets can be used with
``SetSweep``:

**template.txt**::

    Hello {x} {y} {z}\n

**Command**::

    >>> from parasweep import run_sweep, SetSweep
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=SetSweep([{'x': 2, 'y': 8, 'z': 5},
    ...                                     {'x': 1, 'y': -4, 'z': 9}]),
    ...                     verbose=False)
    Hello 2, 8, 5
    Hello 1, -4, 9

Here, as with ``FilteredCartesianSweep``, the parameter mapping is a
dictionary::

    >>> mapping
    {'0': {'x': 2, 'y': 8, 'z': 5}, '1': {'x': 1, 'y': -4, 'z': 9}}

Multiple configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multiple configuration files and their corresponding templates can be used:

**template1.txt**::

    Hello {x},\n

**template2.txt**::

    hello again {y}\n

**Command**::

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

DRMAA
-----

Instead of dispatching simulations with Python's ``subprocess`` module, we can
use the Distributed Resource Management Application API (DRMAA) to interface
with a number of high-performance computing systems. The following example
assumes that DRMAA and an interface to a job scheduler are installed.

**template.txt**::

    Hello {x}\n

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

Advanced template usage
-----------------------

Formatting
~~~~~~~~~~

The following is an example of the basic formatting that can be done with the
Python formatting templates:

**template.txt**::

    Hello {x:.2f}\n

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

    Hello ${x*10}\n

**Command**::

    >>> from parasweep.templates import MakoTemplate
    >>> mapping = run_sweep(command='cat {sim_id}.txt',
    ...                     configs=['{sim_id}.txt'],
    ...                     templates=['template.txt'],
    ...                     sweep=CartesianSweep({'x': [1, 2, 3]}),
    ...                     verbose=False, template_engine=MakoTemplate())
    Hello 10
    Hello 20
    Hello 30
