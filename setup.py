#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard libraries
import sys
import os

# Third-party libraries
try:
	import setuptools
except ImportError:
	from ez_setup import use_setuptools
	use_setuptools()

from setuptools import setup, find_packages

# Local modules
CONTAINING_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
try:
	from utils import get_version_from_tag
	__version__ = get_version_from_tag()
	open(os.path.join(CONTAINING_DIRECTORY,"processing_pipe/VERSION"), "w").write(__version__)
except ImportError:
	from processing_pipe import VERSION as __version__

package_list = find_packages(where=os.path.join(CONTAINING_DIRECTORY))

setup(
    name = "processing-pipe",
    version = __version__,
    description = ("Benchmark tool in Python and C++"),
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
    ],
    keywords = 'qidata test benchmark',
    author = 'Surya AMBROSE <sambrose@softbankrobotics.com>, Arnaud DUHAMEL <arnaud.duhamel@external.softbankrobotics.com>',
    author_email = 'sambrose@softbankrobotics.com',
    packages = package_list,
    install_requires = [
        "python-ecto >= 1.0.1",
        "qidata >= 1.0.0a10"
    ],
    package_data={"processing_pipe":["VERSION"]},
    entry_points={
        'console_scripts': [
            'processing-pipe = processing_pipe.__main__:main'
        ],
        'processing.commands': [
            'eval = processing_pipe.commands.eval_command',
            'run = processing_pipe.commands.run_command',
        ],
    }
)
