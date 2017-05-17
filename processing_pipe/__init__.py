# Standard libraries
import os as _os

# Convenience version variable
VERSION = open(_os.path.join(_os.path.dirname(_os.path.realpath(__file__)), "VERSION")).read().split()[0]