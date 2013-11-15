#!/usr/bin/env python

import sys, os

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, Extension, find_packages

# jump through some hoops to get access to versionstring()
from os.path import abspath, dirname
sys.path.insert(0, abspath(dirname(__file__)))
from terane import versionstring

setup(
    # package description
    name = "terane-toolbox",
    version = versionstring(),
    description="Distributed event indexing and search",
    author="Michael Frank",
    author_email="msfrank@syntaxockey.com",
    # installation dependencies
    install_requires=[
        "Twisted >= 13.1.0",
        "pyparsing",
        "python-dateutil",
        "loggerglue",
        "urwid",
        "zope.interface",
        "zope.component",
        ],
    # package classifiers for PyPI
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment "" No Input/Output (Daemon)",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: System :: Logging",
        "Topic :: Text Processing :: Indexing",
        ],
    # package contents
    packages=[
        'terane',
        'terane.api',
        'terane.sinks',
        'terane.sources',
        'terane.toolbox',
        'terane.toolbox.etl',
        'terane.toolbox.search',
        ],
    entry_points={
        'console_scripts': [
            #'terane=terane.toolbox.console:console_main',
            'terane-etl=terane.toolbox.etl:etl_main',
            'terane-search=terane.toolbox.search:search_main',
            ],
        },
    test_suite="tests",
    tests_require=["setuptools_trial"]
)
