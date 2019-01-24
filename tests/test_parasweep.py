"""
Test suite.

Tests will only work on UNIX-like systems. Some tests rely on drmaa, Mako, or
xarray being installed.
"""
from parasweep import run_sweep
from parasweep.namers import SequentialNamer
from parasweep.templates import PythonFormatTemplate

import unittest


class TestSweep(unittest.TestCase):
    def test_basic(self):
        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello {x:.2f}\n'],
                  sweep_parameters={'x': [1/3, 2/3, 3/3]})
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(),
                             'Hello 0.33\nHello 0.67\nHello 1.00\n')

    def test_single(self):
        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello {x}, {y}\n'],
                  sweep_parameters={'x': [1], 'y': [2]})
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 1, 2\n')

    def test_multiple_templates(self):
        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}_1.txt {sim_id}_2.txt >> out_test',
                  ['{sim_id}_1.txt', '{sim_id}_2.txt'],
                  template_texts=['Hello {x:.2f}\n', 'Hello again {y}\n'],
                  sweep_parameters={'x': [1/3, 2/3, 3/3], 'y': [4]})
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(),
                             'Hello 0.33\nHello again 4\nHello 0.67\n'
                             'Hello again 4\nHello 1.00\nHello again 4\n')

    def test_mako(self):
        from parasweep.templates import MakoTemplate
        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello ${x*10}\n'],
                  sweep_parameters={'x': [1, 2, 3]},
                  template_engine=MakoTemplate)
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(),
                             'Hello 10\nHello 20\nHello 30\n')

    def test_drmaa(self):
        from parasweep.dispatchers import DRMAADispatcher

        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 1, 1]}, wait=True,
                  dispatcher=DRMAADispatcher())
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')

    def test_delay(self):
        import time

        start_time = time.time()
        run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 2]}, delay=2)

        self.assertGreater(time.time() - start_time, 4)

    def test_serial(self):
        import time
        from parasweep.dispatchers import DRMAADispatcher

        start_time = time.time()
        run_sweep('sleep 2', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 2]}, serial=True)

        self.assertGreater(time.time() - start_time, 4)

        start_time = time.time()
        run_sweep('sleep 2', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 2]}, dispatcher=DRMAADispatcher(),
                  serial=True)

        self.assertGreater(time.time() - start_time, 4)

    def test_wait(self):
        out = open('out_test', 'w')
        out.close()
        run_sweep('sleep 3; cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 1, 1]}, wait=True)
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')

    def test_errors(self):
        with self.assertRaises(TypeError) as context:
            run_sweep('cat {sim_id}.txt', '{sim_id}.txt',
                      template_texts='Hello {x} {z}\n',
                      sweep_parameters={'x': [1, 2, 3]})

        self.assertEqual('`config_paths` and `template_paths` or'
                         '`template_texts` must be a list.',
                         str(context.exception))

        with self.assertRaises(ValueError) as context:
            run_sweep('cat {sim_id}.txt', '{sim_id}.txt',
                      sweep_parameters={'x': [1, 2, 3]})

        self.assertEqual('Exactly one of `template_paths` or `template_texts` '
                         'must be provided.', str(context.exception))

    def test_param_mapping(self):
        param_array = run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                                template_texts=['Hello {x} {y} {z}\n'],
                                sweep_parameters={'x': [1, 2], 'y': [3, 4, 5],
                                                  'z': [6, 7, 8, 9]})
        self.assertEqual(param_array.coords.dims, ('x', 'y', 'z'))
        self.assertEqual(param_array.shape, (2, 3, 4))

    def test_parameter_sets(self):
        out = open('out_test', 'w')
        out.close()
        param_mapping = run_sweep('cat {sim_id}.txt >> out_test',
                                  ['{sim_id}.txt'],
                                  template_texts=['Hello {x}, {y}, {z}\n'],
                                  parameter_sets=[{'x': 2, 'y': 8, 'z': 5},
                                                  {'x': 1, 'y': -4, 'z': 9}],
                                  wait=True)
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 2, 8, 5\nHello 1, -4, 9\n')
        self.assertEqual(param_mapping, {'0': {'x': 2, 'y': 8, 'z': 5},
                                         '1': {'x': 1, 'y': -4, 'z': 9}})


class TestPythonTemplates(unittest.TestCase):
    def test_errors(self):
        with self.assertRaises(NameError) as context:
            run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                      template_texts=['Hello {x} {z}\n'],
                      sweep_parameters={'x': [1, 2, 3]})

        self.assertEqual("The name 'z' is used in the template but not "
                         "provided.",
                         str(context.exception))

        with self.assertRaises(NameError) as context:
            run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                      template_texts=['Hello {x}\n'],
                      sweep_parameters={'x': [1, 2, 3], 'y': [4]})

        self.assertEqual("The names {'y'} are not used in the template.",
                         str(context.exception))

        with self.assertRaises(ValueError) as context:
            PythonFormatTemplate()

        self.assertEqual('Exactly one of `paths` or `texts` must be '
                         'provided.', str(context.exception))

    def test_paths(self):
        out = open('out_test', 'w')
        out.close()

        with open('template_test.txt', 'w') as template_file:
            template_file.write('Hello {x}\n')

        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_paths=['template_test.txt'],
                  sweep_parameters={'x': [1, 2, 3]})

        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 1\nHello 2\nHello 3\n')


class TestMakoTemplates(unittest.TestCase):
    def test_errors(self):
        from parasweep.templates import MakoTemplate

        with self.assertRaises(NameError) as context:
            run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                      template_texts=['Hello ${x*10} ${z}\n'],
                      sweep_parameters={'x': [1, 2, 3]},
                      template_engine=MakoTemplate)

        self.assertEqual("'z' is not defined", str(context.exception))

        with self.assertRaises(NameError) as context:
            run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                      template_texts=['Hello ${x*10}\n'],
                      sweep_parameters={'x': [1, 2, 3], 'y': [4]},
                      template_engine=MakoTemplate)

        self.assertEqual("The names {'y'} are not used in the template.",
                         str(context.exception))

    def test_paths(self):
        from parasweep.templates import MakoTemplate

        out = open('out_test', 'w')
        out.close()

        with open('template_test.txt', 'w') as template_file:
            template_file.write('Hello ${x}\n')

        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_paths=['template_test.txt'],
                  sweep_parameters={'x': [1, 2, 3]},
                  template_engine=MakoTemplate)

        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 1\nHello 2\nHello 3\n')


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


if __name__ == '__main__':
    unittest.main()
