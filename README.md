A Python script for running simulations in parallel. Similar to GNU Parallel, but facilitates parameter sweeps by allowing you to insert parameters for each simulation instance into whatever configuration format your simulation uses.

By default, Python format strings are used. Optionally, you can also use the [Mako template library](http://www.makotemplates.org/), which is more powerful.

Advantages:
- don't have to build a parser in your simulation, just use its current configuration files
- easily specify parameter sweeps using ranges
- convenient mapping between each parameter set and the simulation ID in the form of an N-dimensional array, allowing for slicing, etc.
- saves information about which simulation was run with which parameter set, so you can retrieve this later
- easy post-processing with a Python function

Dependencies:
- numpy
- xarray
- Mako (optional)
- drmaa-python (optional)

TODO:
- logging and timing for each process
- control how many processes to run at once
- multiple nodes (?)
- cleaning/moving of generated files
- post-processing
- more examples, testing
- formatters for templates (i.e., for Fortran number formats)
- command-line interface
- Python functions
- non-Cartesian product sweeps
- restart from NetCDF
- run without config template
- interface with SLURM job arrays (DRMAA)
- use sweep IDs with sim IDs, auto-generate sweep IDs
- multiple configuration files
- default templates (e.g., JSON)
