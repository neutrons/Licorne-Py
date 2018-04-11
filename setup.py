#!/usr/bin/env python
import sys
import os
from setuptools import setup
package_data = {"licorne": ["UI/*.ui",]}

_scripts = ["bin/Licorne"]
if "bdist_rpm" in sys.argv and os.path.isdir("/SNS/software/miniconda2/envs/licorne"):
    _scripts =["bin/licorne"]

setup(
    name='licorne-py',
    version='0.1.0',
    description='',
    author='Steven Hahn, Andrei Savici',
    author_email='hahnse@ornl.gov, saviciat@ornl.gov',
    url='https://github.com/neutrons/licorne-py',
    license='GPLv3+',
    scripts=_scripts,
    packages=['licorne'],
    package_data=package_data,
)
