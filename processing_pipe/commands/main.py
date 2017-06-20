# -*- coding: utf-8 -*-

# Third-party libraries
import argparse

# Local modules
import processing_pipe.version

TOOLS_DESCRIPTION = "Tool to design and run processing graphs. Very useful for testing and prototyping"
TOOLS_SUBCOMMANDS = []

import run_commands
TOOLS_SUBCOMMANDS.append([run_commands, "run"])

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

	parser.add_argument("-v", "--version", action=processing_pipe.version.VersionAction, nargs=0,
	                    help="print your package release version number")
	return parser

tools_main_parser = toolsParser()