import os
import subprocess
import itertools
import glob

from jinja2 import Environment, FileSystemLoader

DEFAULTS = {}


def post_process(sim_id):
    pass


def run_simulation(simulation, params_file, single_parameters={},
                   sweep_parameters={}, build=False, run=True):
    params = DEFAULTS.copy()
    params.update(single_parameters)
    starting_dir = os.path.abspath('.')
    if build:
        pass
    os.chdir(starting_dir)

    sim_ids = []
    keys = sweep_parameters.keys()
    values = [sweep_parameters[key] for key in keys]

    if sweep_parameters:
        product = itertools.product(*values)
    else:
        product = [params]

    config = Environment(loader=FileSystemLoader(starting_dir),
                         trim_blocks=True).get_template(params_file)
    processes = []
    for param_set in product:
        sweep_params = params.copy()
        if keys:
            for index, value in enumerate(param_set):
                sweep_params[keys[index]] = value
        #TODO: use something better
        sim_id = abs(sum(map(hash, sweep_params.values()))) % 65535
        sim_ids.append(sim_id)

        config.render(**sweep_params)
        config_file = open('../test/config_{sim_id}'.format(sim_id=sim_id), 'w')
        config_file.write(config)
        config_file.close()

        if run:
            os.chdir(build_dir)
            print("Running simulation {sim_id} with parameters:".format(sim_id=sim_id))
            print(zip(keys, param_set))
            proc = subprocess.Popen(['./{simulation}'.format(simulation=simulation)])
            os.chdir(starting_dir)
            processes.append(proc)

    # Wait until all processes are finished
    for process in processes:
        process.wait()

    print(sim_ids)
    for index, sim_id in enumerate(sim_ids):
        post_process(sim_id)

        if not os.path.isdir(str(sim_id)):
            os.mkdir(str(sim_id))
