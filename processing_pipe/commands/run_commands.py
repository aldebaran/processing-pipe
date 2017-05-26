# -*- coding: utf-8 -*-

# Third-party libraries
import argparse

# Local modules
from processing_pipe.graph import Graph
from processing_pipe.utils import loadJSONFile

DESCRIPTION = "Run given processing graph"

def runAlgorithm(args):
	graph = Graph.createFromDict(loadJSONFile(args.GRAPH))
	graph.run()

# ──────
# Parser

def make_command_parser(parent_parser=argparse.ArgumentParser(description=DESCRIPTION)):

	parent_parser.add_argument("GRAPH",
	                                default="", type=str,
	                                help="File describing the graph to process")
	parent_parser.set_defaults(func=runAlgorithm)

	return parent_parser
