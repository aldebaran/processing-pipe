# Standard library
import pytest

# Third-party libraries
from ecto import cells

# Local modules
from processing_pipe.graph import (
	Graph,
)

def test_noop_graph():
	graph = Graph()
	graph.run() # does nothing

def test_cell_addition():
	graph = Graph()
	graph.addCell(cells.Passthrough("pt"))
	assert(graph.size()==1)

def test_set_graph_output():
	graph = Graph()
	graph.addCell(cells.Passthrough("pt"))
	graph.setPortAsGraphOutput("pt","out")
	graph.run() # does nothing
	assert(None == graph.output)

def test_addition_of_connected_cells():
	graph = Graph()
	graph.addCell(cells.Constant("const", value=2))
	graph.addCell(cells.Passthrough("pt"))
	graph.setPortAsGraphOutput("pt","out")
	graph.connect("const", "out", "pt", "in")
	graph.run()
	assert(2 == graph.output)

def test_raise_if_no_output_set():
	"""
	Getting output when none was set should raise
	"""
	graph = Graph()
	graph.addCell(cells.Constant("const", value=2))
	graph.addCell(cells.Passthrough("pt"))
	graph.connect("const", "out", "pt", "in")
	graph.run()
	with pytest.raises(Exception) as excinfo:
		assert(2 == graph.output)
	assert 'No output was set for graph' in str(excinfo.value)

def test_set_several_outputs():
	graph = Graph()
	graph.addCell(cells.Constant("const", value=2))
	graph.addCell(cells.Passthrough("pt"))
	graph.connect("const", "out", "pt", "in")
	graph.setPortAsGraphOutput("const", "out")
	graph.setPortAsGraphOutput("pt", "out")
	graph.run()
	assert(2 == graph.output[0])
	assert(2 == graph.output[1])

def test_set_graph_input():
	graph = Graph()
	graph.addCell(cells.Passthrough("pt"))
	graph.addCell(cells.Passthrough("pt2"))
	graph.setPortAsGraphOutput("pt2","out")
	graph.setPortAsGraphInput("pt","in")
	graph.connect("pt", "out", "pt2", "in")
	assert([("pt", "in")] == graph.getGraphInputs())
	graph.input = 10
	graph.run()
	assert(10 == graph.output)

def test_raise_if_no_input_set():
	"""
	Setting input when none was set should raise
	"""
	graph = Graph()
	graph.addCell(cells.Passthrough("pt"))
	graph.addCell(cells.Passthrough("pt2"))
	graph.setPortAsGraphOutput("pt2","out")
	graph.connect("pt", "out", "pt2", "in")
	with pytest.raises(IndexError) as excinfo:
		graph.input = 10
	assert "`input` can only be used if exactly 1 input port is defined"  in str(excinfo.value)

	with pytest.raises(IndexError) as excinfo:
		graph.inputs = (True, True)
	assert 'No input was set for graph' in str(excinfo.value)

def test_set_several_inputs():
	graph = Graph()
	graph.addCell(cells.And("and"))
	graph.addCell(cells.Passthrough("pt2"))
	graph.setPortAsGraphInput("and","in1")
	graph.setPortAsGraphInput("and","in2")
	assert([("and", "in1"), ("and", "in2")] == graph.getGraphInputs())
	graph.setPortAsGraphOutput("pt2","out")
	graph.connect("and", "out", "pt2", "in")
	graph.inputs[0] = False
	graph.inputs[1] = True
	graph.run()
	assert(False == graph.output)

	graph.inputs = (True, True)
	graph.run()
	assert(True == graph.output)

def test_roll_over_inputs():
	"""
	If we want to try several inputs combination, we
	want the graph to run on all possible combinations
	without having to set it manually like above.
	Then we want results to be return in outputs
	"""
	graph = Graph()
	graph.addCell(cells.And("and"))
	graph.addCell(cells.Passthrough("pt2"))
	graph.setPortAsGraphInput("and","in1")
	graph.setPortAsGraphInput("and","in2")
	graph.setPortAsGraphOutput("pt2","out")
	graph.connect("and", "out", "pt2", "in")
	graph.inputs = [
		(True, False),
		(True, True),
	]
	graph.run()
	assert(
		[False, True] == graph.output
	)

def test_roll_over_input():
	"""
	If we want to try several inputs combination, we
	want the graph to run on all possible combinations
	without having to set it manually like above.
	Then we want results to be return in outputs
	"""
	graph = Graph()
	graph.addCell(cells.Passthrough("pt"))
	graph.addCell(cells.Counter("cnt"))
	graph.setPortAsGraphInput("pt","in")
	graph.connect("pt", "out", "cnt", "input")
	graph.setPortAsGraphOutput("cnt","count")
	graph.input = [10, 20, 30, 40]
	graph.run()
	assert(
		[1, 2, 3, 4] == graph.output
	)

def test_use_cell_parameter():
	"""
	Any parameter set at the cell level is used during processing
	"""
	graph = Graph()
	graph.addCell(cells.Passthrough("pt"))
	graph.addCell(cells.Counter("cnt", count=10))
	graph.setPortAsGraphInput("pt","in")
	graph.connect("pt", "out", "cnt", "input")
	graph.setPortAsGraphOutput("cnt","count")
	graph.input = [10, 20, 30, 40]
	graph.run()
	assert(
		[11, 12, 13, 14] == graph.output
	)

def test_clear_inputs():
	"""
	Here we want to replace declared inputs by two cells
	"""
	graph = Graph()
	graph.addCell(cells.And("and"))
	graph.addCell(cells.Passthrough("pt2"))
	graph.setPortAsGraphInput("and","in1")
	graph.setPortAsGraphInput("and","in2")
	graph.setPortAsGraphOutput("pt2","out")
	graph.connect("and", "out", "pt2", "in")
	graph.inputs[0] = False
	graph.inputs[1] = True
	graph.run()
	assert(False == graph.output)


	graph.addCell(cells.Constant("const1", value=True))
	graph.addCell(cells.Constant("const2", value=True))
	graph.clearGraphInputs()
	with pytest.raises(IndexError) as excinfo:
		graph.inputs = (True, True)
	assert 'No input was set for graph' in str(excinfo.value)
	graph.connect("const1", "out", "and", "in1")
	graph.connect("const2", "out", "and", "in2")
	graph.run()
	assert(True == graph.output)

def test_roll_over_parameters():
	"""
	If we want to try several parameters, we
	want the graph to run on all possible combinations
	without having to set it manually like above.
	Then we want results to be return in outputs
	"""
	graph = Graph()
	graph.addCell(cells.Constant("const", value=True))
	graph.addCell(cells.And("and"))
	graph.setPortAsGraphInput("and","in1")
	graph.connect("const", "out", "and", "in2")
	graph.setPortAsGraphOutput("and","out")
	graph.setSwitchingParameters("const", "value", [True, False])
	graph.input = True
	graph.run()
	assert(
		[True, False] == graph.output
	)

def test_graph_results():
	"""
	Graph returns output, but it also must return a more complete information,
	containing inputs used, parameters applied, and obtained outputs.
	"""
	# Graph creation
	graph = Graph()
	graph.addCell(cells.Constant("const1", value=True))
	graph.addCell(cells.Constant("const2", value=True))
	graph.addCell(cells.Constant("const3", value=True))
	graph.addCell(cells.And("and1"))
	graph.addCell(cells.And("and2"))
	graph.addCell(cells.And("and3"))
	graph.addCell(cells.And("and4"))
	graph.setPortAsGraphInput("and1","in1")
	graph.setPortAsGraphInput("and2","in1")
	graph.connect("const1", "out", "and1", "in2")
	graph.connect("const2", "out", "and2", "in2")
	graph.connect("const3", "out", "and4", "in2")
	graph.connect("and1", "out", "and3", "in1")
	graph.connect("and2", "out", "and3", "in2")
	graph.connect("and3", "out", "and4", "in1")
	graph.setPortAsGraphOutput("and4","out")

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

# def test_roll_over_parameters_optimized():
# 	"""
# 	If we set different possible values for parameters on different cells, it
# 	is important to control the order in which the parameters are changed to
# 	avoid useless recomputation.
# 	"""
# 	# Graph creation
# 	graph = Graph()
# 	graph.addCell(cells.Constant("const1", value=True))
# 	graph.addCell(cells.Constant("const2", value=True))
# 	graph.addCell(cells.Constant("const3", value=True))
# 	graph.addCell(cells.And("and1"))
# 	graph.addCell(cells.And("and2"))
# 	graph.addCell(cells.And("and3"))
# 	graph.addCell(cells.And("and4"))
# 	graph.setPortAsGraphInput("and1","in1")
# 	graph.setPortAsGraphInput("and2","in1")
# 	graph.connect("const1", "out", "and1", "in2")
# 	graph.connect("const2", "out", "and2", "in2")
# 	graph.connect("const3", "out", "and4", "in2")
# 	graph.connect("and1", "out", "and3", "in1")
# 	graph.connect("and2", "out", "and3", "in2")
# 	graph.connect("and3", "out", "and4", "in1")
# 	graph.setPortAsGraphOutput("and4","out")


# 	# Add counters to make sure we did not pass more than
# 	# needed in each node
# 	graph.addCell(cells.Counter("count1"))
# 	graph.addCell(cells.Counter("count2"))
# 	graph.addCell(cells.Counter("count3"))
# 	graph.addCell(cells.Counter("count4"))
# 	graph.addCell(cells.Counter("count5"))
# 	graph.addCell(cells.Counter("count6"))
# 	graph.addCell(cells.Counter("count7"))
# 	graph.connect("const1", "out", "count1", "input")
# 	graph.connect("const2", "out", "count2", "input")
# 	graph.connect("const3", "out", "count3", "input")
# 	graph.connect("and1", "out", "count4", "input")
# 	graph.connect("and2", "out", "count5", "input")
# 	graph.connect("and3", "out", "count6", "input")
# 	graph.connect("and4", "out", "count7", "input")
# 	graph.setPortAsGraphOutput("count1","count")
# 	graph.setPortAsGraphOutput("count2","count")
# 	graph.setPortAsGraphOutput("count3","count")
# 	graph.setPortAsGraphOutput("count4","count")
# 	graph.setPortAsGraphOutput("count5","count")
# 	graph.setPortAsGraphOutput("count6","count")
# 	graph.setPortAsGraphOutput("count7","count")

# 	# Graph parametrization
# 	graph.setSwitchingParameters("const1", "value", [True, False])
# 	graph.setSwitchingParameters("const2", "value", [True, False])
# 	graph.setSwitchingParameters("const3", "value", [True, False])
# 	graph.inputs = (True, True)
# 	graph.run()

# 	assert(len(graph.result) == 8)
# 	print graph.output[-1]
# 	assert(graph.output[-1][1] == 2)
# 	assert(graph.output[-1][2] == 2)
# 	assert(graph.output[-1][3] == 2)
# 	assert(graph.output[-1][4] == 2)
# 	assert(graph.output[-1][5] == 2)
# 	assert(graph.output[-1][6] == 4)
# 	assert(graph.output[-1][7] == 8)

# def test_roll_over_parameters_and_inputs_optimized():
# 	"""
#	TO RE-EDIT
# 	If we set different possible values for parameters on different cells, it
# 	is important to control the order in which the parameters are changed to
# 	avoid useless recomputation. Because of this, the output orders is less
# 	reliable
# 	"""
# 	# Graph creation
# 	graph = Graph()
# 	graph.addCell(cells.Constant("const1", value=True))
# 	graph.addCell(cells.Constant("const2", value=True))
# 	graph.addCell(cells.Constant("const3", value=True))
# 	graph.addCell(cells.And("and1"))
# 	graph.addCell(cells.And("and2"))
# 	graph.addCell(cells.And("and3"))
# 	graph.addCell(cells.And("and4"))
# 	graph.setPortAsGraphInput("and1","in1")
# 	graph.setPortAsGraphInput("and2","in1")
# 	graph.connect("const1", "out", "and1", "in2")
# 	graph.connect("const2", "out", "and2", "in2")
# 	graph.connect("const3", "out", "and4", "in2")
# 	graph.connect("and1", "out", "and3", "in1")
# 	graph.connect("and2", "out", "and3", "in2")
# 	graph.connect("and3", "out", "and4", "in1")
# 	graph.setPortAsGraphOutput("and4","out")


# 	# Add counters to make sure we did not pass more than
# 	# needed in each node
# 	graph.addCell(cells.Counter("count1"))
# 	graph.addCell(cells.Counter("count2"))
# 	graph.addCell(cells.Counter("count3"))
# 	graph.addCell(cells.Counter("count4"))
# 	graph.addCell(cells.Counter("count5"))
# 	graph.addCell(cells.Counter("count6"))
# 	graph.addCell(cells.Counter("count7"))
# 	graph.connect("const1", "out", "count1", "input")
# 	graph.connect("const2", "out", "count2", "input")
# 	graph.connect("const3", "out", "count3", "input")
# 	graph.connect("and1", "out", "count4", "input")
# 	graph.connect("and2", "out", "count5", "input")
# 	graph.connect("and3", "out", "count6", "input")
# 	graph.connect("and4", "out", "count7", "input")
# 	graph.setPortAsGraphOutput("count1","count")
# 	graph.setPortAsGraphOutput("count2","count")
# 	graph.setPortAsGraphOutput("count3","count")
# 	graph.setPortAsGraphOutput("count4","count")
# 	graph.setPortAsGraphOutput("count5","count")
# 	graph.setPortAsGraphOutput("count6","count")
# 	graph.setPortAsGraphOutput("count7","count")

# 	# Graph parametrization
# 	graph.setSwitchingParameters("const1", "value", [True, False])
# 	graph.setSwitchingParameters("const2", "value", [True, False])
# 	graph.setSwitchingParameters("const3", "value", [True, False])
# 	graph.inputs = [
# 		(True, True),
# 		(True, False),
# 		(False, True),
# 		(False, False)
# 	]
# 	graph.run()

# 	assert(len(graph.result) == 32)
# 	print graph.output[-1]
# 	assert(graph.output[-1][1] == 2)
# 	assert(graph.output[-1][2] == 2)
# 	assert(graph.output[-1][3] == 2)
# 	assert(graph.output[-1][4] == 4)
# 	assert(graph.output[-1][5] == 4)
# 	assert(graph.output[-1][6] == 16)
# 	assert(graph.output[-1][7] == 32)