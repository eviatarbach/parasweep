=========
parasweep
=========

.. image:: https://img.shields.io/pypi/v/parasweep.svg
        :target: https://pypi.python.org/pypi/parasweep

.. image:: https://readthedocs.org/projects/parasweep/badge/?version=latest
        :target: https://parasweep.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Utility for facilitating parallel parameter sweeps.

* Free software: MIT license
* Documentation: https://parasweep.readthedocs.io.


Features
--------

* Parameter sweep types:
    * Sweeps using all possible combinations of the given parameter values (Cartesian product)
    * Sweeps using specific parameter sets
* Dispatch types:
    * Python's `subprocess` (default)
    * DRMAA to interface with HPC job schedulers
* Template types:
    * Python format strings (default)
    * Mako templates for more powerful formatting

Usage
-----

To use parasweep::

    from parasweep import run_sweep

See the documentation for :func:`parasweep.sweep.run_sweep` for full usage details.

Dependencies
------------

* Python 3.6+
* xarray
* numpy
* Mako (optional)
* drmaa-python (optional)

Credits
-------

Developed by `Eviatar Bach <http://eviatarbach.com/>`_ <eviatarbach@protonmail.com>.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
