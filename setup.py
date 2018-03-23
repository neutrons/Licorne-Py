#!/usr/bin/env python
from setuptools import setup
package_data = {"licorne": ["UI/*.ui",]}


setup(
    name='licorne-py',
    version='0.1.0',
    description='',
    author='Steven Hahn, Andrei Savici',
    author_email='hahnse@ornl.gov, saviciat@ornl.gov',
    url='https://github.com/neutrons/licorne-py',
    license='GPLv3+',
    scripts=["bin/Licorne"],
    packages=['licorne'],
    package_data=package_data,
)
