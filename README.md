A Python script for running simulations in parallel. Similar to GNU Parallel, but facilitates parameter sweeps by allowing you to insert parameters (using the [Mako template library](http://www.makotemplates.org/)) for each simulation instance into whatever configuration format your simulation uses.

Advantages:
- don't have to build a parser in your simulation, just use its current configuration files
- easily specify parameter sweeps using ranges
- convenient mapping between each parameter set and the simulation ID in the form of an N-dimensional array, allowing for slicing, etc.
- saves information about which simulation was run with which parameter set, so you can retrieve this later
- easy post-processing with a Python function

Dependencies:
- numpy
- xarray
- Mako

TODO:
- logging and timing for each process
- control how many processes to run at once
- multiple nodes (?)
- cleaning/moving of generated files
- post-processing
- more examples, testing
- errors if not all parameters are used in template
- formatters for templates (i.e., for Fortran number formats)
- command-line interface
- Python functions
- non-Cartesian product sweeps
- restart from NetCDF
- run without config template
- interface with SLURM job arrays (DRMAA)
- sweep IDs
- multiple configuration files
- default templates (e.g., JSON)
