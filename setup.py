#!/usr/bin/env python
import os
from setuptools import setup
package_data = {"licorne": ["UI/*.ui",]}

setup(
    name='licorne-py',
    version='0.1.3',
    description='',
    author='Steven Hahn, Andrei Savici',
    author_email='hahnse@ornl.gov, saviciat@ornl.gov',
    url='https://github.com/neutrons/licorne-py',
    license='GPLv3+',
    scripts=["bin/licorne"],
    packages=['licorne'],
    package_data=package_data,
)
