# -*- coding: utf-8 -*-

# Third-party libraries
import argparse

# Local modules
from processing_pipe import VERSION

TOOLS_DESCRIPTION = "Tool to design and run processing graphs. Very useful for testing and prototyping"
TOOLS_SUBCOMMANDS = []

import run_commands
TOOLS_SUBCOMMANDS.append([run_commands, "run"])

class VersionAction(argparse.Action):
	def __init__(self, option_strings, dest, nargs, **kwargs):
		super(VersionAction, self).__init__(option_strings, dest, nargs=0, **kwargs)
	def __call__(self, parser, namespace, values, option_string):
		version_string = VERSION + "\n"
		parser.exit(message=version_string)
import eval_commands
TOOLS_SUBCOMMANDS.append([eval_commands, "eval"])

def toolsParser():
	parser = argparse.ArgumentParser(description=TOOLS_DESCRIPTION)
	subparsers = parser.add_subparsers()
	for sc in TOOLS_SUBCOMMANDS:
		sub_parser = subparsers.add_parser(sc[1],
		                                      description=sc[0].DESCRIPTION,
		                                      help=sc[0].DESCRIPTION)
		sc[0].make_command_parser(sub_parser)

	parser.add_argument("-v", "--version", action=VersionAction, nargs=0,
	                    help="print processing_pipe release version number")
	return parser

tools_main_parser = toolsParser()