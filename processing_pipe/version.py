# -*- coding: utf-8 -*-

# Third-party libraries
from argparse import Action

# Local modules
from processing_pipe import VERSION

class VersionAction(Action):
	def __init__(self, option_strings, dest, nargs, **kwargs):
		super(VersionAction, self).__init__(option_strings, dest, nargs=0, **kwargs)
	def __call__(self, parser, namespace, values, option_string):
		version_string = VERSION + "\n"
		parser.exit(message=version_string)
