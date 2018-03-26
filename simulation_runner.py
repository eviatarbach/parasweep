import os
import subprocess
import itertools
import glob

from mako.template import Template


def run_simulation(command, config_path, template_path, single_parameters={},
                   sweep_parameters={}, build=False, run=True):
    params = single_parameters.copy()

    if build:
        pass

    sim_ids = []
    keys = sweep_parameters.keys()
    values = [sweep_parameters[key] for key in keys]

    if sweep_parameters:
        product = itertools.product(*values)
    else:
        product = [params]

    config = Template(filename=template_path, input_encoding='utf-8')

    processes = []
    for param_set in product:
        sweep_params = params.copy()
        if keys:
            for index, value in enumerate(param_set):
                sweep_params[keys[index]] = value
        #TODO: use something better
        sim_id = abs(sum(map(hash, sweep_params.values()))) % 65535
        sim_ids.append(sim_id)

        config_rendered = config.render(**sweep_params)
        config_file = open(config_path.format(sim_id=sim_id), 'w')
        config_file.write(config_rendered)
        config_file.close()

        if run:
            print("Running simulation {sim_id} with parameters:".format(sim_id=sim_id))
            print(zip(keys, param_set))
            proc = subprocess.Popen([command.format(simulation=simulation, sim_id=sim_id)])
            processes.append(proc)

    # Wait until all processes are finished
    for process in processes:
        process.wait()

    print(sim_ids)
