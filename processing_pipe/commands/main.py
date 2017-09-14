# -*- coding: utf-8 -*-

# Standard libraries
import pkg_resources as _pkg

# Third-party libraries
import argparse

# Local modules
from processing_pipe import VERSION

DESCRIPTION = "Tool to design and run processing graphs. Very useful for testing and prototyping"
SUBCOMMANDS = []

for _ep in _pkg.iter_entry_points(group="processing.commands"):
	_name = _pkg.EntryPoint.pattern.match(str(_ep)).groupdict()["name"]
	SUBCOMMANDS.append([_ep.load(), _name])

class VersionAction(argparse.Action):
	def __init__(self, option_strings, dest, nargs, **kwargs):
		super(VersionAction, self).__init__(option_strings, dest, nargs=0, **kwargs)
	def __call__(self, parser, namespace, values, option_string):
		version_string = VERSION + "\n"
		parser.exit(message=version_string)

def parser():
	parser = argparse.ArgumentParser(description=DESCRIPTION)
	subparsers = parser.add_subparsers()
	for sc in SUBCOMMANDS:
		sub_parser = subparsers.add_parser(sc[1],
		                                      description=sc[0].DESCRIPTION,
		                                      help=sc[0].DESCRIPTION)
		sc[0].make_command_parser(sub_parser)

	parser.add_argument("-v", "--version", action=VersionAction, nargs=0,
	                    help="print processing_pipe release version number")
	return parser
