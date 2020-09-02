"""
Test suite.

Some tests rely on drmaa, Mako, or xarray being installed.
"""
import unittest
import tempfile
import time
import warnings
import os
import json
import contextlib
import io

from parasweep import run_sweep
from parasweep import CartesianSweep, FilteredCartesianSweep, SetSweep, \
                      RandomSweep
from parasweep.namers import SequentialNamer, HashNamer, SetNamer
from parasweep.dispatchers import SubprocessDispatcher

# Use a Python "cat" and "sleep" command to make it more cross-platform
cat = ' '.join(['python', os.path.join(os.path.dirname(__file__), 'cat')])
sleep = ' '.join(['python',
                  os.path.join(os.path.dirname(__file__), 'sleep')])
sleepcat = ' '.join(['python',
                     os.path.join(os.path.dirname(__file__), 'sleepcat')])
err = ' '.join(['python', os.path.join(os.path.dirname(__file__), 'err')])


class TestSweep(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)
        warnings.simplefilter('ignore', ImportWarning)

    def test_basic(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x:.2f}\n')
            template.seek(0)

            run_sweep(' '.join([cat, ' {sim_id}.txt', out.name]),
                      ['{sim_id}.txt'], templates=[template.name],
                      sweep=CartesianSweep({'x': [1/3, 2/3, 3/3]}),
                      verbose=False, cleanup=True, save_mapping=False)

            # Check unordered, because we can't guarantee order
            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello 0.33\nHello 0.67\n'
                                  'Hello 1.00\n').splitlines()))

    def test_single(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}, {y}\n')
            template.seek(0)

            run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                      ['{sim_id}.txt'], templates=[template.name],
                      sweep=CartesianSweep({'x': [1], 'y': [2]}),
                      verbose=False, cleanup=True, save_mapping=False)

            self.assertEqual(out.read(), 'Hello 1, 2\n')

    def test_multiple_templates(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template1, \
                tempfile.NamedTemporaryFile('w') as template2:
            template1.write('Hello {x:.2f}, ')
            template1.seek(0)

            template2.write('hello again {y}\n')
            template2.seek(0)

            run_sweep(' '.join([cat, '{sim_id}_1.txt', '{sim_id}_2.txt',
                                out.name]),
                      ['{sim_id}_1.txt', '{sim_id}_2.txt'],
                      templates=[template1.name, template2.name],
                      sweep=CartesianSweep({'x': [1/3, 2/3, 3/3], 'y': [4]}),
                      verbose=False, cleanup=True, save_mapping=False)

            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello 0.33, hello again 4\nHello 0.67, '
                                  'hello again 4\nHello 1.00, '
                                  'hello again 4\n').splitlines()))

    def test_mako(self):
        from parasweep.templates import MakoTemplate

        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello ${x*10}\n')
            template.seek(0)

            run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                      ['{sim_id}.txt'], templates=[template.name],
                      sweep=CartesianSweep({'x': [1, 2, 3]}),
                      template_engine=MakoTemplate(), verbose=False,
                      cleanup=True, save_mapping=False)

            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello 10\nHello 20\n'
                                  'Hello 30\n').splitlines()))

    def test_drmaa(self):
        from parasweep.dispatchers import DRMAADispatcher
        from drmaa import JobTemplate

        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                      ['{sim_id}.txt'], templates=[template.name],
                      sweep=CartesianSweep({'x': [1, 1, 1]}), wait=True,
                      dispatcher=DRMAADispatcher(), verbose=False,
                      cleanup=True, save_mapping=False)

            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')

            jt = JobTemplate(errorPath=':err_test.txt')
            run_sweep(' '.join([err, '{sim_id}']),
                      ['{sim_id}.txt'], templates=[template.name],
                      sweep=CartesianSweep({'x': [1]}), wait=True,
                      dispatcher=DRMAADispatcher(jt), verbose=False,
                      cleanup=True, save_mapping=False)

            with open('err_test.txt', 'r') as error_file:
                self.assertEqual('Error, simulation ID: 0\n',
                                 error_file.read())

            os.remove('err_test.txt')

    def test_serial(self):
        from parasweep.dispatchers import DRMAADispatcher

        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            start_time = time.time()
            run_sweep(' '.join([sleep, str(2)]), ['{sim_id}.txt'],
                      templates=[template.name],
                      sweep=CartesianSweep({'x': [1, 2]}), serial=True,
                      verbose=False, save_mapping=False)

            self.assertGreater(time.time() - start_time, 4)

            start_time = time.time()
            run_sweep(' '.join([sleep, str(2)]), ['{sim_id}.txt'],
                      templates=[template.name],
                      sweep=CartesianSweep({'x': [1, 2]}),
                      dispatcher=DRMAADispatcher(), serial=True, verbose=False,
                      save_mapping=False)

            self.assertGreater(time.time() - start_time, 4)

        os.remove('0.txt')
        os.remove('1.txt')

    def test_wait(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            run_sweep(' '.join([sleepcat, str(3), '{sim_id}.txt', out.name]),
                      ['{sim_id}.txt'], templates=[template.name],
                      sweep=CartesianSweep({'x': [1, 1, 1]}), wait=True,
                      verbose=False, save_mapping=False)

            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')

        os.remove('0.txt')
        os.remove('1.txt')
        os.remove('2.txt')

    def test_errors(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x} {z}\n')
            template.seek(0)

            with self.assertRaises(TypeError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), '{sim_id}.txt',
                          templates=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3]}),
                          verbose=False, cleanup=True, save_mapping=False)

            self.assertEqual('`configs` and `templates` must be a list.',
                             str(context.exception))

    def test_param_mapping(self):
        import xarray

        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x} {y} {z}\n')
            template.seek(0)

            param_array = run_sweep(' '.join([cat, '{sim_id}.txt']),
                                    ['{sim_id}.txt'],
                                    templates=[template.name],
                                    sweep=CartesianSweep({'x': [1, 2],
                                                          'y': [3, 4, 5],
                                                          'z': [6, 7, 8, 9]}),
                                    verbose=False, cleanup=True,
                                    sweep_id='test', save_mapping=True)

            self.assertEqual(param_array.coords.dims, ('x', 'y', 'z'))
            self.assertEqual(param_array.shape, (2, 3, 4))

            self.assertTrue(os.path.isfile('sim_ids_test.nc'))

            all_equal = (param_array
                         == xarray.open_dataarray('sim_ids_test.nc')).all()
            self.assertTrue(all_equal)

            os.remove('sim_ids_test.nc')

    def test_parameter_sets(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}, {y}, {z}\n')
            template.seek(0)

            mapping = run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                                ['{sim_id}.txt'],
                                templates=[template.name],
                                sweep=SetSweep([{'x': 2, 'y': 8, 'z': 5},
                                                {'x': 1, 'y': -4, 'z': 9}]),
                                verbose=False, cleanup=True,
                                sweep_id='test1', save_mapping=True)

            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello 2, 8, 5\n'
                                  'Hello 1, -4, 9\n').splitlines()))
            self.assertEqual(mapping, {'0': {'x': 2, 'y': 8, 'z': 5},
                                       '1': {'x': 1, 'y': -4, 'z': 9}})

            self.assertTrue(os.path.isfile('sim_ids_test1.json'))

            with open('sim_ids_test1.json', 'r') as json_file:
                self.assertEqual(mapping, json.load(json_file))

            os.remove('sim_ids_test1.json')

    def test_filtered_cartesian(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}, {y}\n')
            template.seek(0)

            sweep = FilteredCartesianSweep({'x': [1, 2, 3], 'y': [1, 2, 3]},
                                           filter_func=lambda x, y: x > y)
            mapping = run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                                ['{sim_id}.txt'], templates=[template.name],
                                sweep=sweep, verbose=False, cleanup=True,
                                sweep_id='test2', save_mapping=True)

            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello 2, 1\nHello 3, 1\n'
                                  'Hello 3, 2').splitlines()))

            self.assertTrue(os.path.isfile('sim_ids_test2.json'))

            with open('sim_ids_test2.json', 'r') as json_file:
                self.assertEqual(mapping, json.load(json_file))

            os.remove('sim_ids_test2.json')

    def test_random(self):
        import scipy.stats
        import numpy.random

        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x:.2f}, {y:.2f}\n')
            template.seek(0)

            sweep = RandomSweep({'x': scipy.stats.norm(),
                                 'y': scipy.stats.uniform(loc=0, scale=3)},
                                random_state=numpy.random.RandomState(30),
                                length=3)
            mapping = run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                                ['{sim_id}.txt'], templates=[template.name],
                                sweep=sweep, verbose=False, cleanup=True,
                                sweep_id='test3', save_mapping=True)

            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello -1.26, 2.89\nHello 1.53, 1.04\n'
                                  'Hello -0.97, 2.98').splitlines()))

            self.assertTrue(os.path.isfile('sim_ids_test3.json'))

            with open('sim_ids_test3.json', 'r') as json_file:
                self.assertEqual(mapping, json.load(json_file))

            os.remove('sim_ids_test3.json')

    def test_overwrite(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            run_sweep(' '.join([cat, ' {sim_id}.txt']),
                      ['{sim_id}.txt'], templates=[template.name],
                      sweep=CartesianSweep({'x': [1]}),
                      verbose=False, cleanup=False, save_mapping=False)

            with self.assertRaises(FileExistsError) as context:
                run_sweep(' '.join([cat, ' {sim_id}.txt']),
                          ['{sim_id}.txt'], templates=[template.name],
                          sweep=CartesianSweep({'x': [1]}),
                          verbose=False, cleanup=False, save_mapping=False,
                          overwrite=False)

            self.assertEqual('0.txt exists, set `overwrite` to True to '
                             'overwrite.', str(context.exception))

            os.remove('0.txt')

    def test_verbose(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            temp_stdout = io.StringIO()
            with contextlib.redirect_stdout(temp_stdout):
                run_sweep(' '.join([cat, ' {sim_id}.txt']),
                          ['{sim_id}.txt'], templates=[template.name],
                          sweep=CartesianSweep({'x': [1]}),
                          verbose=True, cleanup=True, save_mapping=False)

            self.assertEqual(temp_stdout.getvalue(),
                             'Running simulation 0 with parameters:\nx: 1\n')

    def test_max_procs(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            dispatcher = SubprocessDispatcher(max_procs=1)

            start_time = time.time()
            run_sweep(' '.join([sleep, str(2)]), ['{sim_id}.txt'],
                      templates=[template.name],
                      sweep=CartesianSweep({'x': [1, 2]}),
                      dispatcher=dispatcher, verbose=False, save_mapping=False,
                      cleanup=True)

            self.assertGreater(time.time() - start_time, 4)


class TestPythonTemplates(unittest.TestCase):
    def test_errors(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x} {z}\n')
            template.seek(0)

            with self.assertRaises(NameError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                          templates=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3]}),
                          verbose=False, cleanup=True, save_mapping=False)

            self.assertEqual("The name 'z' is used in the template but not "
                             "provided.", str(context.exception))

            template.truncate(0)
            template.write('Hello {x}\n')
            template.seek(0)

            with self.assertRaises(NameError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                          templates=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3], 'y': [4]}),
                          verbose=False, cleanup=True, save_mapping=False)

            self.assertEqual("The names {'y'} are not used in the "
                             "template.", str(context.exception))


class TestMakoTemplates(unittest.TestCase):
    def test_errors(self):
        from parasweep.templates import MakoTemplate

        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello ${x*10} ${z}\n')
            template.seek(0)

            with self.assertRaises(NameError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                          templates=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3]}),
                          template_engine=MakoTemplate(), verbose=False,
                          cleanup=True, save_mapping=False)

            self.assertEqual("'z' is not defined", str(context.exception))

            template.truncate(0)
            template.write('Hello ${x*10}\n')
            template.seek(0)

            with self.assertRaises(NameError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                          templates=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3], 'y': [4]}),
                          template_engine=MakoTemplate(), verbose=False,
                          cleanup=True, save_mapping=False)

            self.assertEqual("The names {'y'} are not used in the "
                             "template.", str(context.exception))


class TestNamers(unittest.TestCase):
    def test_sequential(self):
        counter = SequentialNamer()
        counter.start(length=11)

        self.assertEqual(counter.generate_id({'key1': 'value1'}, ''), '00')
        self.assertEqual(counter.generate_id({'key2': 'value2'}, ''), '01')

        counter = SequentialNamer(zfill=3, start_at=3)
        counter.start(length=2)

        self.assertEqual(counter.generate_id({'key1': 'value1'}, ''), '003')

        counter.generate_id({'key2': 'value2'}, '')

        with self.assertRaises(StopIteration):
            counter.generate_id({'key3': 'key_value3'}, '')

        counter = SequentialNamer()
        counter.start(length=1)

        self.assertEqual(counter.generate_id({'key1': 'value1'}, 'sweep_id'), 'sweep_id_0')

    def test_hash(self):
        counter = HashNamer()

        self.assertEqual(counter.generate_id({'key1': 'value1'}, ''),
                         '31fc462e')
        self.assertEqual(counter.generate_id({'key2': 'value2'}, ''),
                         '9970c8f5')

    def test_set(self):
        counter = SetNamer(['name1', 'name2'])

        self.assertEqual(counter.generate_id({'key1': 'value1'}, ''),
                         'name1')
        self.assertEqual(counter.generate_id({'key2': 'value2'}, ''),
                         'name2')
