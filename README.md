A Python script for running simulations in parallel. Similar to GNU Parallel, but facilitates parameter sweeps by allowing you to insert parameters (using the [Mako template library](http://www.makotemplates.org/)) for each simulation instance into whatever configuration format your simulation uses.

TODO: logging and timing for each process, control how many processes to run at once, multiple nodes, cleaning/moving of generated files, post-processing, more examples, errors if not all parameters are used in template, formatters for templates (i.e., for Fortran number formats)
