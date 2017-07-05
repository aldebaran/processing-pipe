# -*- coding: utf-8 -*-

# Standard libraries
import os
import glob

# Third-party libraries
import argparse
from qidata import qidataset, qidatafile, DataType
from ecto.opencv import highgui

# Local modules
from processing_pipe.graph import Graph
from processing_pipe.utils import loadJSONFile

DESCRIPTION = "Evaluate a given processing graph"

class OutputDescription:
	is_list = False
	metadata_type = None
	property_name_to_test = None

	def __init__(self, name):
		self.name = name
		self.reset()

	def reset(self):
		self.can_be_evaluated_by = []
		self.fp_enabled_on = []
		self.tn_enabled = False

def evalAlgorithm(args):
	# Test data has been given in arguments
	input_datasets = glob.glob(args.input_dataset)
	input_datafiles = glob.glob(args.input_datafile)
	if len(input_datasets) == 0 and len(input_datafiles) == 0:
		raise IOError("The given pattern does not match any folder nor file name")

	# Create result storing maps
	true_positives = dict()
	false_negatives = dict()
	false_positives = dict()
	true_negatives = dict()

	# Read graph description (will raise if file is not a proper JSON file)
	graph_description = loadJSONFile(args.GRAPH)

	# Retrieve outputs to evaluate
	outputs_evaluation_parameters = []
	output_can_be_evaluated_by = dict()
	output_has_fp_enabled_on = dict()
	for graph_output in graph_description["outputs"]:
		if not graph_output.has_key("qidata_type"):
			# This output does not need to be evaluated
			outputs_evaluation_parameters.append(None)
		else:
			_output_name = "%s.%s"%(graph_output["cell_id"], graph_output["port_name"])
			# Create an entry for that name in each result map
			true_positives[_output_name] = dict()
			false_negatives[_output_name] = dict()
			false_positives[_output_name] = dict()
			true_negatives[_output_name] = dict()

			_output_description = OutputDescription(_output_name)
			if graph_output["qidata_type"][0] == "<" and graph_output["qidata_type"][-1] == ">":
				# Output is a list
				_output_description.is_list = True
				graph_output = graph_output["qidata_type"][1:-1]

			# Get output type
			_output_description.metadata_type = graph_output.split(".")[0]

			# if len(graph_output.split("."))>1:
			# 	_output_description.propertyNameToTest = graph_output.split(".")[1]

			outputs_evaluation_parameters.append(_output_description)
			output_can_be_evaluated_by[_output_description] = dict()
			output_has_fp_enabled_on[_output_description] = dict()

	# Filter out datasets and datafiles that can't be used for evaluation
	valid_input_datasets = []
	valid_input_datafiles = []
	try:
		while 1:
			input_dataset = input_datasets.pop(0)

			# Is it a dataset ?
			if not qidataset.isDataset(input_dataset):
				print "%s is not a valid QiDataSet"%input_dataset
				continue

			# Check if dataset provides annotations for outputs
			with qidataset.QiDataSet(input_dataset, "r") as _ds:
				_c=_ds.content
				_something_can_be_evaluated = False
				for output_to_eval in outputs_evaluation_parameters:
					if output_to_eval is None: continue

					output_can_be_evaluated_by[output_to_eval][input_dataset] = []
					output_has_fp_enabled_on[output_to_eval][input_dataset] = []

					for k, annotation_totality in _c._data.iteritems():
						if k[1] != output_to_eval.metadata_type:
							continue
						annotator = k[0]
						output_can_be_evaluated_by[output_to_eval][input_dataset].append(annotator)
						_something_can_be_evaluated = True
						if annotation_totality:
							output_has_fp_enabled_on[output_to_eval][input_dataset].append(annotator)

			if not _something_can_be_evaluated:
				print "Annotations in %s dataset don't match the ooutput you want to evaluate"%input_dataset
				continue
			else:
				valid_input_datasets.append(input_dataset)
	except IndexError:
		pass

	try:
		while 1:
			input_qidatafile = input_datafiles.pop(0)
			# Check if file contains annotation for outputs #
			try:
				with qidatafile.open(input_qidatafile, "r") as _f:
					metadata = _f.metadata
					file_qidatatype = _f.type
			except TypeError:
				# File is not supported by QiData. Skip !
				print "%s is not a valid QiDataFile"%input_datafile
				continue

			_something_can_be_evaluated = False
			for output_to_eval in outputs_evaluation_parameters:
				if output_to_eval is None: continue

				output_can_be_evaluated_by[output_to_eval][input_qidatafile] = []
				output_has_fp_enabled_on[output_to_eval][input_qidatafile] = []

				for annotator, annotations in metadata.iteritems():
					if not output_to_eval.metadata_type in annotations.keys():
						continue
					output_can_be_evaluated_by[output_to_eval][input_qidatafile].append(annotator)
					_something_can_be_evaluated = True
					output_has_fp_enabled_on[output_to_eval][input_qidatafile].append(annotator)

			if not _something_can_be_evaluated:
				print "Annotations is not complete enough in %s file to evaluate what you want"%input_datafile
				continue
			else:
				valid_input_datafiles.append(input_qidatafile)
	except IndexError:
		pass

	if len(valid_input_datasets) == 0 and len(valid_input_datafiles) == 0:
		raise Exception("None of the given data can be used to evaluate the given graph")

	# Create graph based on JSON
	graph = Graph.createFromDict(graph_description)

	# Unset the graph inputs (input will be fed by newly added cells)
	graph.clearGraphInputs()

	# Create cells to feed inputs
	input_provider_index = 0
	for graph_input in graph_description["inputs"]:

		if graph_input["qidata_type"] in ["IMAGE", "IMG_2D", "IMG_3D", "IMG_STEREO"]:
			# Add image opening cell
			graph.addCell(
				highgui.imread(
					"input_provider_%d"%input_provider_index,
					mode=highgui.ImageMode.GRAYSCALE
				)
			)

			graph.connect(
				"input_provider_%d"%input_provider_index,
				"image",
				graph_input["cell_id"],
				graph_input["port_name"]
			)
		else:
			raise Exception("Input datatype %s is not yet supported"%graph_input["qidata_type"])

		input_provider_index += 1

	for input_dataset in valid_input_datasets:

		# Check if dataset provides the required types for the graph inputs
		input_provider_index = 0
		for graph_input in graph_description["inputs"]:
			with qidataset.QiDataSet(input_dataset, "r") as _ds:
				input_files_from_dataset = _ds.getAllFilesOfType(graph_input["qidata_type"])

			if len(input_files_from_dataset)==0:
				print "%s dataset has no data compatible with the given graph"%input_dataset
				break

			graph.setSwitchingParameters(
				"input_provider_%d"%input_provider_index,
				"image_file",
				map(lambda x: os.path.join(input_dataset,str(x)), input_files_from_dataset)
			)

			input_provider_index += 1

		if input_provider_index == len(graph_description["inputs"]):
			graph.run()

			for output_to_eval in outputs_evaluation_parameters:
				for brave_annotator in output_can_be_evaluated_by[output_to_eval][input_dataset]:
					if not true_positives[output_to_eval.name].has_key(brave_annotator):
						true_positives[output_to_eval.name][brave_annotator] = 0
						false_negatives[output_to_eval.name][brave_annotator] = 0
						if brave_annotator in output_has_fp_enabled_on[output_to_eval][input_dataset]:
							false_positives[output_to_eval.name][brave_annotator] = 0

			for result in graph.result:
				# Retrieve annotations corresponding to the parameter set
				annotations = dict()
				for output_to_eval in outputs_evaluation_parameters:
					annotations[output_to_eval.metadata_type] = dict()
					# for brave_annotator in output_can_be_evaluated_by[output_to_eval][input_dataset]:
					# 	annotations[output_to_eval.metadata_type][brave_annotator] = list()

				for (param_name, param_value) in result["params"].iteritems():
					if not "image_file" in param_name:
						continue
					with qidatafile.open(param_value, "r") as annot_file:
						for output_to_eval in outputs_evaluation_parameters:
							# for annotator in set(annot_file.annotators).intersection(set(output_can_be_evaluated_by[output_to_eval][input_dataset])):
							annotations[output_to_eval.metadata_type][annotator]=annot_file.metadata[annotator][output_to_eval.metadata_type]

				outputs = []
				for (out_description, processing_output) in zip(outputs_evaluation_parameters, result["outputs"]):
					if out_description.is_list:
						for (annotator, annotation_list) in annotations[out_description.metadata_type].items():
							false_negatives[out_description.name][annotator] += max(len(annotation_list) - len(processing_output),0)
							true_positives[out_description.name][annotator] += min(len(annotation_list),len(processing_output))
							if annotator in output_has_fp_enabled_on[out_description][input_dataset]:
								false_positives[out_description.name][annotator] += max(len(processing_output) - len(annotation_list),0)

		else:
			continue

	for input_qidatafile in valid_input_datafiles:

		# Check if dataset provides the required types for the graph inputs
		graph_input = graph_description["inputs"][0]
		if file_qidatatype == DataType.IMAGE:
			graph.setSwitchingParameters(
				"input_provider_0",
				"image_file",
				[str(input_qidatafile)]
			)

		else:
			print "Input datatype %s is not yet supported or does not match file type"%graph_input["qidata_type"]
			break

		graph.run()

		for brave_annotator in output_can_be_evaluated_by[output_to_eval][input_qidatafile]:
			if not true_positives[output_to_eval.name].has_key(brave_annotator):
				true_positives[output_to_eval.name][brave_annotator] = 0
				false_negatives[output_to_eval.name][brave_annotator] = 0
				if brave_annotator in output_has_fp_enabled_on[output_to_eval][input_qidatafile]:
					false_positives[output_to_eval.name][brave_annotator] = 0

		for result in graph.result:
			# Retrieve annotations corresponding to the parameter set
			annotations = dict()
			for output_to_eval in outputs_evaluation_parameters:
				annotations[output_to_eval.metadata_type] = dict()
				for brave_annotator in output_can_be_evaluated_by[output_to_eval][input_qidatafile]:
					annotations[output_to_eval.metadata_type][brave_annotator] = list()

			for (param_name, param_value) in result["params"].iteritems():
				if not "image_file" in param_name:
					continue
				with qidatafile.open(param_value, "r") as annot_file:
					for output_to_eval in outputs_evaluation_parameters:
						for annotator in set(annot_file.annotators).intersection(set(output_can_be_evaluated_by[output_to_eval][input_qidatafile])):
							annotations[output_to_eval.metadata_type][annotator].extend(
								annot_file.metadata[annotator][output_to_eval.metadata_type]
							)
			outputs = []
			for (out_description, processing_output) in zip(outputs_evaluation_parameters, result["outputs"]):
				if out_description.is_list:
					for (annotator, annotation_list) in annotations[out_description.metadata_type].items():
						false_negatives[output_to_eval.name][annotator] += max(len(annotation_list) - len(processing_output),0)
						true_positives[output_to_eval.name][annotator] += min(len(annotation_list),len(processing_output))
						if annotator in output_has_fp_enabled_on[out_description][input_qidatafile]:
							false_positives[output_to_eval.name][annotator] += max(len(processing_output) - len(annotation_list),0)

	if len(true_positives[output_to_eval.name].keys()) == 0:
		# the graph has never run !!!
		raise IOError("No given dataset could be used to run the graph")


	evaluation_output = dict()

	for output_to_eval in outputs_evaluation_parameters:
		evaluation_output[output_to_eval.name] = dict()
		print "Output: %s"%(output_to_eval.name)
		for brave_annotator in true_positives[output_to_eval.name].keys():
			print "Annotator: %s"%brave_annotator
			evaluation_output[output_to_eval.name][brave_annotator] = dict(
				sensitivity=(true_positives[output_to_eval.name][brave_annotator], true_positives[output_to_eval.name][brave_annotator]+false_negatives[output_to_eval.name][brave_annotator])
			)
			try:
				print "Sensitivity: %f%% (%d/%d)"%(
					100*float(true_positives[output_to_eval.name][brave_annotator])/float(true_positives[output_to_eval.name][brave_annotator]+false_negatives[output_to_eval.name][brave_annotator]),
					true_positives[output_to_eval.name][brave_annotator],
					true_positives[output_to_eval.name][brave_annotator]+false_negatives[output_to_eval.name][brave_annotator]
				)
			except ZeroDivisionError:
				print "Sensitivity: N/A"

			if annotator in false_positives[output_to_eval.name].keys():
				evaluation_output[output_to_eval.name][brave_annotator]["fdr"] = (false_positives[output_to_eval.name][brave_annotator], true_positives[output_to_eval.name][brave_annotator]+false_positives[output_to_eval.name][brave_annotator])
				print "False Discovery Rate: %f%% (%d/%d)"%(
					100*float(false_positives[output_to_eval.name][brave_annotator])/float(false_positives[output_to_eval.name][brave_annotator]+true_positives[output_to_eval.name][brave_annotator]),
					false_positives[output_to_eval.name][brave_annotator],
					false_positives[output_to_eval.name][brave_annotator]+true_positives[output_to_eval.name][brave_annotator]
				)

	return evaluation_output

# ──────
# Parser

def make_command_parser(parent_parser=argparse.ArgumentParser(description=DESCRIPTION)):

	parent_parser.add_argument("--input-datafile",
	                                default="", type=str,
	                                help="QiDataFile to use (can only be used if a unique input is needed)")

	parent_parser.add_argument("--input-dataset",
	                                default="", type=str,
	                                help="QiDataSet to use")

	parent_parser.add_argument("GRAPH",
	                                default="", type=str,
	                                help="File describing the graph to process")
	parent_parser.set_defaults(func=evalAlgorithm)

	return parent_parser
