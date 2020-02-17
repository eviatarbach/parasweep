# -*- coding: utf-8 -*-
"""Main sweep functionality."""
import datetime
import os

from parasweep.namers import SequentialNamer
from parasweep.dispatchers import SubprocessDispatcher
from parasweep.templates import PythonFormatTemplate


def run_sweep(command, configs, templates, sweep, namer=SequentialNamer(),
              dispatcher=SubprocessDispatcher(),
              template_engine=PythonFormatTemplate(), sweep_id=None,
              serial=False, wait=False, cleanup=False, verbose=True,
              overwrite=True, save_mapping=True):
    r"""
    Run parameter sweeps.

    Parameters
    ----------
    command : str
        The command to run. Must include ``{sim_id}`` indicating where the
        simulation ID is to be inserted.
    configs : list
        List of paths indicating where the configuration files should be saved
        after substitution of the parameters into the templates. Each must
        include ``{sim_id}`` indicating where the simulation ID is to be
        inserted. Must be in the same order as ``templates``.
    templates : list
        List of paths of templates to substitute parameters into. Must be in
        the same order as ``configs``.
    sweep : sweepers.Sweep instance
        A :class:`parasweep.sweepers.Sweep` object that specifies the type of
        sweep. By default, it is a Cartesian sweep.
    namer : namers.Namer instance, optional
        A :class:`parasweep.namers.Namer` object that specifies how to assign
        simulation IDs. By default, assigns simulation IDs sequentially.
    dispatcher : dispatchers.Dispatcher instance, optional
        A :class:`parasweep.dispatchers.Dispatcher` object that specifies how
        to run the jobs. By default, uses Python's ``subprocess`` module.
    template_engine : templates.TemplateEngine instance, optional
        A :class:`parasweep.templates.TemplateEngine` object that specifies the
        template engine to use. By default, uses Python format strings.
    sweep_id : str, optional
        A name for the sweep. By default, the name is generated automatically
        from the date and time.
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
        returning (as with the ``wait`` argument). False by default.
    verbose : bool, optional
        Whether to print some information about each simulation as it is
        launched. True by default.
    overwrite : bool, optional
        Whether to overwrite existing files when creating configuration files.
        If False, a ``FileExistsError`` will be raised when a configuration
        filename coincides with an existing one in the same directory. True by
        default.
    save_mapping : bool, optional
        Whether to save a mapping between the parameters to the simulation
        IDs. The type of mapping will depend on the type of sweep (set with
        the ``sweep`` argument). The filename will be of the form
        ``sim_ids_{sweep_id}``, with an extension depending on the mapping
        type. True by default.

    Examples
    --------
    Many examples are provided in :doc:`examples`.

    """
    if isinstance(configs, str) or isinstance(templates, str):
        raise TypeError('`configs` and `templates` must be a list.')

    if not sweep_id:
        current_time = datetime.datetime.now()
        sweep_id = current_time.strftime('%Y-%m-%dT%H_%M_%S')

    template_engine.load(paths=templates)

    namer.start(length=len(sweep))

    sim_ids = []
    config_filenames = []

    dispatcher.initialize_session()

    for param_set in sweep.elements():
        sim_id = namer.generate_id(param_set, sweep_id)
        sim_ids.append(sim_id)

        rendered = template_engine.render(param_set)
        for config_rendered, config_path in zip(rendered, configs):
            config_filename = config_path.format(sim_id=sim_id)
            config_filenames.append(config_filename)
            if not overwrite:
                if os.path.isfile(config_filename):
                    raise FileExistsError(f'{config_filename} exists, set '
                                          '`overwrite` to True to overwrite.')
            with open(config_filename, 'wb') as config_file:
                config_file.write(config_rendered.encode('utf-8', 'replace'))

        if verbose:
            print(f'Running simulation {sim_id} with parameters:')
            print('\n'.join(f'{key}: {param}' for key, param
                            in param_set.items()))

        dispatcher.dispatch(command.format(sim_id=sim_id), serial)

    if wait:
        dispatcher.wait_all()

    if cleanup:
        dispatcher.wait_all()
        for config_filename in config_filenames:
            os.remove(config_filename)

    return sweep.mapping(sim_ids, sweep_id, save_mapping)
