"""Setup script for processing pipe"""

# Standard libraries
try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
from setuptools import setup
import sys

# Local modules
from processing_pipe import VERSION as __version__

# make sure that setup.py is run with an allowed python version
def check_allowed_python_version():
    import re
    pattern = "'Programming Language :: Python :: (\d+)\.(\d+)'"
    supported = []
    with open(__file__) as setup:
        for line in setup.readlines():
            found = re.search(pattern, line)
            if found:
                major = int(found.group(1))
                minor = int(found.group(2))
                supported.append( (major, minor) )
    this_py = sys.version_info[:2]
    if this_py not in supported:
        print("only these python versions are supported:", supported)
        sys.exit(1)

check_allowed_python_version()

setup(
    name = "processing-pipe",
    version = __version__,
    description = ("Benchmark tool in Python and C++"),
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
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
    packages = [
        'processing_pipe',
        'processing_pipe.commands',
    ],
    install_requires = [
        "python-ecto >= 1.0a2",
        "qidata >= 0.3.3"
    ],
    package_data={"processing_pipe":["VERSION"]},
    scripts=['bin/processing_pipe'],
)
