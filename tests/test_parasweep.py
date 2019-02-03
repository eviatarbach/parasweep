"""
Test suite.

Some tests rely on drmaa, Mako, or xarray being installed.
"""
from parasweep import run_sweep, CartesianSweep, SetSweep
from parasweep.namers import SequentialNamer

import unittest
import tempfile
import time
import warnings
import os

# Use a Python "cat" and "sleep" command to make it more cross-platform
cat = ' '.join(['python', os.path.join(os.path.dirname(__file__), 'cat')])
sleep = ' '.join(['python',
                  os.path.join(os.path.dirname(__file__), 'sleep')])
sleepcat = ' '.join(['python',
                     os.path.join(os.path.dirname(__file__), 'sleepcat')])


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
                      ['{sim_id}.txt'], template_paths=[template.name],
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
                      ['{sim_id}.txt'], template_paths=[template.name],
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
                      template_paths=[template1.name, template2.name],
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
                      ['{sim_id}.txt'], template_paths=[template.name],
                      sweep=CartesianSweep({'x': [1, 2, 3]}),
                      template_engine=MakoTemplate, verbose=False,
                      cleanup=True, save_mapping=False)

            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello 10\nHello 20\n'
                                  'Hello 30\n').splitlines()))

    def test_drmaa(self):
        from parasweep.dispatchers import DRMAADispatcher

        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                      ['{sim_id}.txt'], template_paths=[template.name],
                      sweep=CartesianSweep({'x': [1, 1, 1]}), wait=True,
                      dispatcher=DRMAADispatcher(), verbose=False,
                      cleanup=True, save_mapping=False)

            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')

    def test_delay(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            start_time = time.time()
            run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                      template_paths=[template.name],
                      sweep=CartesianSweep({'x': [1, 2]}), delay=2,
                      verbose=False, cleanup=True, save_mapping=False)

            self.assertGreater(time.time() - start_time, 4)

    def test_serial(self):
        from parasweep.dispatchers import DRMAADispatcher

        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            start_time = time.time()
            run_sweep(' '.join([sleep, str(2)]), ['{sim_id}.txt'],
                      template_paths=[template.name],
                      sweep=CartesianSweep({'x': [1, 2]}), serial=True,
                      verbose=False, cleanup=True, save_mapping=False)

            self.assertGreater(time.time() - start_time, 4)

            start_time = time.time()
            run_sweep(' '.join([sleep, str(2)]), ['{sim_id}.txt'],
                      template_paths=[template.name],
                      sweep=CartesianSweep({'x': [1, 2]}),
                      dispatcher=DRMAADispatcher(), serial=True, verbose=False,
                      cleanup=True, save_mapping=False)

            self.assertGreater(time.time() - start_time, 4)

    def test_wait(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}\n')
            template.seek(0)

            run_sweep(' '.join([sleepcat, str(3), '{sim_id}.txt', out.name]),
                      ['{sim_id}.txt'], template_paths=[template.name],
                      sweep=CartesianSweep({'x': [1, 1, 1]}), wait=True,
                      verbose=False, cleanup=True, save_mapping=False)

            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')

    def test_errors(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x} {z}\n')
            template.seek(0)

            with self.assertRaises(TypeError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), '{sim_id}.txt',
                          template_paths=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3]}),
                          verbose=False, cleanup=True, save_mapping=False)

                self.assertEqual('`config_paths` and `template_paths` must be '
                                 'a list.', str(context.exception))

    def test_param_mapping(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x} {y} {z}\n')
            template.seek(0)

            param_array = run_sweep(' '.join([cat, '{sim_id}.txt']),
                                    ['{sim_id}.txt'],
                                    template_paths=[template.name],
                                    sweep=CartesianSweep({'x': [1, 2],
                                                          'y': [3, 4, 5],
                                                          'z': [6, 7, 8, 9]}),
                                    verbose=False, cleanup=True,
                                    save_mapping=False)

            self.assertEqual(param_array.coords.dims, ('x', 'y', 'z'))
            self.assertEqual(param_array.shape, (2, 3, 4))

    def test_parameter_sets(self):
        with tempfile.NamedTemporaryFile('r') as out, \
                tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x}, {y}, {z}\n')
            template.seek(0)

            mapping = run_sweep(' '.join([cat, '{sim_id}.txt', out.name]),
                                ['{sim_id}.txt'],
                                template_paths=[template.name],
                                sweep=SetSweep([{'x': 2, 'y': 8, 'z': 5},
                                                {'x': 1, 'y': -4, 'z': 9}]),
                                verbose=False, cleanup=True,
                                save_mapping=False)

            self.assertEqual(set(out.read().splitlines()),
                             set(('Hello 2, 8, 5\n'
                                  'Hello 1, -4, 9\n').splitlines()))
            self.assertEqual(mapping, {'0': {'x': 2, 'y': 8, 'z': 5},
                                       '1': {'x': 1, 'y': -4, 'z': 9}})


class TestPythonTemplates(unittest.TestCase):
    def test_errors(self):
        with tempfile.NamedTemporaryFile('w') as template:
            template.write('Hello {x} {z}\n')
            template.seek(0)

            with self.assertRaises(NameError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                          template_paths=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3]}),
                          verbose=False, cleanup=True, save_mapping=False)

                self.assertEqual("The name 'z' is used in the template but "
                                 "not provided.", str(context.exception))

            template.seek(0)
            template.write('Hello {x}\n')
            template.seek(0)

            with self.assertRaises(NameError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                          template_paths=[template.name],
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
                          template_paths=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3]}),
                          template_engine=MakoTemplate, verbose=False,
                          cleanup=True, save_mapping=False)

                self.assertEqual("'z' is not defined", str(context.exception))

            template.seek(0)
            template.write('Hello ${x*10}\n')
            template.seek(0)

            with self.assertRaises(NameError) as context:
                run_sweep(' '.join([cat, '{sim_id}.txt']), ['{sim_id}.txt'],
                          template_paths=[template.name],
                          sweep=CartesianSweep({'x': [1, 2, 3], 'y': [4]}),
                          template_engine=MakoTemplate, verbose=False,
                          cleanup=True, save_mapping=False)

                self.assertEqual("The names {'y'} are not used in the "
                                 "template.", str(context.exception))


class TestNamers(unittest.TestCase):
    def test_sequential(self):
        counter = SequentialNamer()
        counter.start(length=11)

        self.assertEqual(counter.next(['key1'], [['key_value1']]), '00')
        self.assertEqual(counter.next(['key2'], [['key_value2']]), '01')

        counter = SequentialNamer(zfill=3, start_at=3)
        counter.start(length=2)

        self.assertEqual(counter.next(['key1'], [['key_value1']]), '003')

        counter.next(['key2'], [['key_value2']])

        with self.assertRaises(StopIteration):
            counter.next(['key3'], [['key_value3']])
