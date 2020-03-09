"""Packaging settings."""


from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from codecs import open

import os
import sys


NAME = 'aws_okta_processor'
WORKING_DIR = os.path.dirname(__file__)

if WORKING_DIR != '':
    os.chdir(WORKING_DIR)

ABS_PATH = os.path.abspath(WORKING_DIR)
PACKAGE_PATH = os.path.join(ABS_PATH, 'src', NAME)
VERSION_FILE = os.path.join(PACKAGE_PATH, '__init__.py')
README_FILE = os.path.join(ABS_PATH, 'README.rst')

REQUIRES = [
    'docopt>=0.6.2',
    'requests>=2.21.0',
    'boto3>=1.9.134',
    'bs4>=0.0.1',
    'contextlib2>=0.5.5',
    'six>=1.12.0'
]

TEST_REQUIREMENTS = [
    'pytest-cov',
    'pytest-mock',
    'pytest>=2.8.0',
    'responses'
]


def read_version():
    with open(VERSION_FILE, 'r') as open_file:
        for line in open_file:
            if line.startswith('__version__ = '):
                return line.split()[-1].strip().strip("'")


def read_file(file_name):
    with open(file_name, encoding='utf-8') as open_file:
        return open_file.read()


setup(
    name=NAME,
    version=read_version(),
    description='Resource for fetching AWS Role credentials from Okta',
    long_description=read_file(README_FILE),
    url='https://github.com/godaddy/aws-okta-processor',
    author='GoDaddy',
    author_email='oss@godaddy.com',
    license='MIT',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='aws cli okta saml',
    install_requires=REQUIRES,
    python_requires=">=3.6.0",
    tests_require=TEST_REQUIREMENTS,
    entry_points={
        'console_scripts': [
            'aws-okta-processor=aws_okta_processor.cli:main',
        ],
    }
)
