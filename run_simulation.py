import argparse

from simulation_runner import run_simulation

parser = argparse.ArgumentParser(description='Run simulation in parallel.')

parser.add_argument('--command', required=True)
parser.add_argument('--config_path', required=True)
