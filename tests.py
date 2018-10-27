"""
Tests will only work on UNIX-like systems.
"""
from simulation_runner import run_sweep

import unittest

class TestSweep(unittest.TestCase):
    def test_basic(self):
        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello {x:.2f}\n'],
                  sweep_parameters={'x': [1/3, 2/3, 3/3]})
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 0.33\nHello 0.67\nHello 1.00\n')

    def test_multiple_templates(self):
        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}_1.txt {sim_id}_2.txt >> out_test',
                  ['{sim_id}_1.txt', '{sim_id}_2.txt'],
                  template_texts=['Hello {x:.2f}\n', 'Hello again {y}\n'],
                  sweep_parameters={'x': [1/3, 2/3, 3/3], 'y': [4]})
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(),
                             'Hello 0.33\nHello again 4\nHello 0.67\nHello again 4\nHello 1.00\nHello again 4\n')

    def test_mako(self):
        from templates import MakoTemplate
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
        from dispatchers import DRMAADispatcher

        out = open('out_test', 'w')
        out.close()
        run_sweep('cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 1, 1]}, wait=True,
                  dispatcher=DRMAADispatcher)
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')

    def test_delay(self):
        import time

        start_time = time.time()
        run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 2]}, delay=2)

        self.assertGreater(time.time() - start_time, 4)

    def test_wait(self):
        out = open('out_test', 'w')
        out.close()
        run_sweep('sleep 3; cat {sim_id}.txt >> out_test', ['{sim_id}.txt'],
                  template_texts=['Hello {x}\n'],
                  sweep_parameters={'x': [1, 1, 1]}, wait=True)
        with open('out_test', 'r') as out:
            self.assertEqual(out.read(), 'Hello 1\nHello 1\nHello 1\n')


class TestPythonTemplates(unittest.TestCase):
    def test_errors(self):
        with self.assertRaises(NameError) as context:
            run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                      template_texts=['Hello {x} {z}\n'],
                      sweep_parameters={'x': [1, 2, 3]})

        self.assertEqual("The name 'z' is used in the template but not provided.",
                         str(context.exception))

        with self.assertRaises(NameError) as context:
            run_sweep('cat {sim_id}.txt', ['{sim_id}.txt'],
                      template_texts=['Hello {x}\n'],
                      sweep_parameters={'x': [1, 2, 3], 'y': [4]})

        self.assertEqual("The names {'y'} are not used in the template.",
                         str(context.exception))


class TestMakoTemplates(unittest.TestCase):
    def test_errors(self):
        from templates import MakoTemplate

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


if __name__ == '__main__':
    unittest.main()
