#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['xarray>=0.9', 'numpy', 'scipy']

setup_requirements = []

test_requirements = []

setup(
    author="Eviatar Bach",
    author_email='eviatarbach@protonmail.com',
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    description="Utility for facilitating parallel parameter sweeps.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='parasweep',
    name='parasweep',
    packages=find_packages(include=['parasweep']),
    setup_requires=setup_requirements,
    python_requires='>=3.6',
    test_suite='tests',
    tests_require=test_requirements,
    extras_require={'DRMAA support': ['drmaa'], 'Mako templates': ['mako']},
    url='https://github.com/eviatarbach/parasweep',
    version='2020.09',
    zip_safe=False,
)
