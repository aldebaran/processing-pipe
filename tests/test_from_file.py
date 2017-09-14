# Standard library
import pytest

# Third-party libraries
from ecto import cells
from ecto.opencv import highgui

# Local modules
import fixtures
from processing_pipe.graph import (
	Graph,
)
from processing_pipe.utils import loadJSONFile

def test_create_graph_from_file():
	graph = Graph.createFromDict(
		loadJSONFile(
			fixtures.sandboxed(
				fixtures.GRAPH
			)
		)
	)
	assert(graph.size()==2)
	graph.input = 10
	graph.run()
	assert(10 == graph.output)

def test_create_parametrized_graph_from_file():
	graph = Graph.createFromDict(
		loadJSONFile(
			fixtures.sandboxed(
				fixtures.PARAM_GRAPH
			)
		)
	)
	# Graph parametrization
	graph.setSwitchingParameters("const1", "value", [True, False])
	graph.setSwitchingParameters("const2", "value", [True, False])
	graph.setSwitchingParameters("const3", "value", [True, False])
	graph.inputs = [
		(True, True),
		(True, False),
		(False, True),
		(False, False)
	]
	graph.run()

	assert(len(graph.result) == 32)
	for result in graph.result:
		assert(
			result["outputs"][0] == (
				result["params"]["const1.value"]
				and result["params"]["const2.value"]
				and result["params"]["const3.value"]
				and result["inputs"][0]
				and result["inputs"][1]
			)
		)


