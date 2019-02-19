=========
parasweep
=========

.. image:: https://img.shields.io/pypi/v/parasweep.svg
        :target: https://pypi.python.org/pypi/parasweep

.. image:: https://readthedocs.org/projects/parasweep/badge/?version=latest
        :target: https://parasweep.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

parasweep is a free and open-source Python utility for facilitating parallel
parameter sweeps with computational models. Instead of requiring parameters to
be passed by command-line, which can be error-prone and time-consuming,
parasweep leverages the model's existing configuration files using a template
system, requiring minimal code changes. After the sweep values are specified,
a parallel job is dispatched for each parameter set, with support for common
high-performance computing job schedulers. Post-processing is facilitated by
providing a mapping between the parameter sets and the simulations.

* Free software: MIT license
* Documentation: http://www.parasweep.io
* Code: https://github.com/eviatarbach/parasweep

Dependencies
------------

* Python 3.6+
* xarray
* numpy
* scipy
* Mako (optional)
* drmaa-python (optional)

Credits
-------

Developed by `Eviatar Bach <http://eviatarbach.com/>`_ <eviatarbach@protonmail.com>.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
