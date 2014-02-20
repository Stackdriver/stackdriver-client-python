import os
import sys

from pip.req import parse_requirements

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

packages = ['stackdriver']

install_reqs_objs = parse_requirements('requirements.txt')
requires = [str(ir.req) for ir in install_reqs_objs]

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='stackdriver',
    version='0.2',
    description='Stackdriver Client APIs for Python',
    long_description=readme + '\n\n', # TODO: add a history file
    author='John (J5) Palmieri',
    author_email='j5@stackdriver.com',
    url='http://github.com/Stackdriver/stackdriver-py',
    packages= packages,
    package_data={'': ['LICENSE']},
    package_dir={'stackdriver': 'stackdriver'},
    install_requires=requires,
    license=license,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ),
)

