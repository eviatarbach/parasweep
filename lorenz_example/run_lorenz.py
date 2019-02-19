import numpy
import xarray

from parasweep import run_sweep, CartesianSweep

sweep_params = {'beta': numpy.linspace(2, 4, 3),
                'sigma': numpy.linspace(2, 20, 10),
                'rho': numpy.linspace(2, 30, 10)}

sweep = CartesianSweep(sweep_params)

mapping = run_sweep(command='./lorenz {sim_id}',
                    configs=['params_{sim_id}.nml'],
                    templates=['template.txt'],
                    sweep=sweep)


def get_output(sim_id):
    filename = f'results_{sim_id}.txt'
    return numpy.loadtxt(filename)


lyap = xarray.apply_ufunc(get_output, mapping,
                          vectorize=True)
lyap = lyap.rename('Largest Lyapunov exponent')

lyap.isel(beta=0).plot()
