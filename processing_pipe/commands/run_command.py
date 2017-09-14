# -*- coding: utf-8 -*-

# Standard libraries
import os
import sys

# Third-party libraries
import argparse

# Local modules
from processing_pipe.graph import Graph
from processing_pipe.utils import loadJSONFile

DESCRIPTION = """Run given processing graph. The graph should be auto-sufficient
and any declared input or output is ignored.
"""

def runAlgorithm(args):
	throwIfAbsent(args.GRAPH)
	graph = Graph.createFromDict(loadJSONFile(args.GRAPH))
	graph.run()

# ───────
# Helpers

def throwIfAbsent(path):
	if not os.path.exists(path):
		sys.exit(path+" doesn't exist")

# ──────
# Parser

def make_command_parser(parent_parser=argparse.ArgumentParser(description=DESCRIPTION)):

	parent_parser.add_argument("GRAPH",
	                                default="", type=str,
	                                help="File describing the graph to process")
	parent_parser.set_defaults(func=runAlgorithm)

	return parent_parser
