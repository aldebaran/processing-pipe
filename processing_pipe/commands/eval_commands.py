# -*- coding: utf-8 -*-

# Standard libraries
import os
import glob

# Third-party libraries
import argparse
from qidata import qidataset, qidatafile, DataType
from ecto import highgui

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
	tp = dict()
	fn = dict()
	fp = dict()
	tn = dict()
	output_can_be_evaluated_by = dict()
	output_has_fp_enabled_on = dict()

	input_datasets = glob.glob(args.input_dataset)
	input_datafiles = glob.glob(args.input_datafile)
	if len(input_datasets) == 0 and len(input_datafiles) == 0:
		raise IOError("The given pattern does not match any folder nor file name")

	# Create graph based on JSON
	graph_description = loadJSONFile(args.GRAPH)
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

	# Retrieve outputs to evaluate
	outputs_to_eval = []
	for graph_output in graph_description["outputs"]:
		if not graph_output.has_key("qidata_type"):
			# This output does not need to be evaluated
			_output_description = None
		else:
			_output_description = OutputDescription("%s.%s"%(graph_output["cell_id"], graph_output["port_name"]))
			tp[_output_description.name] = dict()
			fn[_output_description.name] = dict()
			fp[_output_description.name] = dict()
			tn[_output_description.name] = dict()
			if graph_output["qidata_type"][0] == "<" and graph_output["qidata_type"][-1] == ">":
				# Output is a list
				_output_description.is_list = True
				graph_output = graph_output["qidata_type"][1:-1]

			# Get output type
			_output_description.metadata_type = graph_output.split(".")[0]

			# if len(graph_output.split("."))>1:
			# 	_output_description.propertyNameToTest = graph_output.split(".")[1]

		outputs_to_eval.append(_output_description)

	for input_dataset in input_datasets:
		## Check if dataset is suitable for evaluation ##

		# Is it a dataset ?
		if not qidataset.isDataset(input_dataset):
			print "%s is not a valid QiDataSet"%input_dataset
			continue

		# Check if dataset provides annotations for outputs
		with qidataset.QiDataSet(input_dataset, "r") as _ds:
			_c=_ds.content
			_something_can_be_evaluated = False
			for output_to_eval in outputs_to_eval:
				if output_to_eval is None: continue

				output_can_be_evaluated_by[output_to_eval] = []
				output_has_fp_enabled_on[output_to_eval] = []

				for k, annotation_totality in _c._data.iteritems():
					if k[1] != output_to_eval.metadata_type:
						continue
					annotator = k[0]
					output_can_be_evaluated_by[output_to_eval].append(annotator)
					_something_can_be_evaluated = True
					if annotation_totality:
						output_has_fp_enabled_on[output_to_eval].append(annotator)

		if not _something_can_be_evaluated:
			print "Annotations is not complete enough in %s dataset to evaluate what you want"%input_dataset
			continue

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

			for output_to_eval in outputs_to_eval:
				for brave_annotator in output_can_be_evaluated_by[output_to_eval]:
					if not tp[output_to_eval.name].has_key(brave_annotator):
						tp[output_to_eval.name][brave_annotator] = 0
						fn[output_to_eval.name][brave_annotator] = 0
						if brave_annotator in output_has_fp_enabled_on[output_to_eval]:
							fp[output_to_eval.name][brave_annotator] = 0
						# tn[brave_annotator] = 0

			for result in graph.result:
				# Retrieve annotations corresponding to the parameter set
				annotations = dict()
				for output_to_eval in outputs_to_eval:
					annotations[output_to_eval.metadata_type] = dict()
					# for brave_annotator in output_can_be_evaluated_by[output_to_eval]:
					# 	annotations[output_to_eval.metadata_type][brave_annotator] = list()

				for (param_name, param_value) in result["params"].iteritems():
					if not "image_file" in param_name:
						continue
					with qidatafile.open(param_value, "r") as annot_file:
						for output_to_eval in outputs_to_eval:
							# for annotator in set(annot_file.annotators).intersection(set(output_can_be_evaluated_by[output_to_eval])):
							annotations[output_to_eval.metadata_type][annotator]=annot_file.metadata[annotator][output_to_eval.metadata_type]

				outputs = []
				for (out_description, processing_output) in zip(outputs_to_eval, result["outputs"]):
					if out_description.is_list:
						for (annotator, annotation_list) in annotations[out_description.metadata_type].items():
							fn[out_description.name][annotator] += max(len(annotation_list) - len(processing_output),0)
							tp[out_description.name][annotator] += min(len(annotation_list),len(processing_output))
							if annotator in output_has_fp_enabled_on[out_description]:
								fp[out_description.name][annotator] += max(len(processing_output) - len(annotation_list),0)

		else:
			continue

	for input_qidatafile in input_datafiles:
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
		for output_to_eval in outputs_to_eval:
			if output_to_eval is None: continue

			output_can_be_evaluated_by[output_to_eval] = []
			output_has_fp_enabled_on[output_to_eval] = []

			for annotator, annotations in metadata.iteritems():
				if not output_to_eval.metadata_type in annotations.keys():
					continue
				output_can_be_evaluated_by[output_to_eval].append(annotator)
				_something_can_be_evaluated = True
				output_has_fp_enabled_on[output_to_eval].append(annotator)

		if not _something_can_be_evaluated:
			print "Annotations is not complete enough in %s file to evaluate what you want"%input_datafile
			continue

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

		for brave_annotator in output_can_be_evaluated_by[output_to_eval]:
			if not tp[output_to_eval.name].has_key(brave_annotator):
				tp[output_to_eval.name][brave_annotator] = 0
				fn[output_to_eval.name][brave_annotator] = 0
				if brave_annotator in output_has_fp_enabled_on[output_to_eval]:
					fp[output_to_eval.name][brave_annotator] = 0
				# tn[brave_annotator] = 0

		for result in graph.result:
			# Retrieve annotations corresponding to the parameter set
			annotations = dict()
			for output_to_eval in outputs_to_eval:
				annotations[output_to_eval.metadata_type] = dict()
				for brave_annotator in output_can_be_evaluated_by[output_to_eval]:
					annotations[output_to_eval.metadata_type][brave_annotator] = list()

			for (param_name, param_value) in result["params"].iteritems():
				if not "image_file" in param_name:
					continue
				with qidatafile.open(param_value, "r") as annot_file:
					for output_to_eval in outputs_to_eval:
						for annotator in set(annot_file.annotators).intersection(set(output_can_be_evaluated_by[output_to_eval])):
							annotations[output_to_eval.metadata_type][annotator].extend(
								annot_file.metadata[annotator][output_to_eval.metadata_type]
							)
			outputs = []
			for (out_description, processing_output) in zip(outputs_to_eval, result["outputs"]):
				if out_description.is_list:
					for (annotator, annotation_list) in annotations[out_description.metadata_type].items():
						fn[output_to_eval.name][annotator] += max(len(annotation_list) - len(processing_output),0)
						tp[output_to_eval.name][annotator] += min(len(annotation_list),len(processing_output))
						if annotator in output_has_fp_enabled_on[out_description]:
							fp[output_to_eval.name][annotator] += max(len(processing_output) - len(annotation_list),0)

	if len(tp[output_to_eval.name].keys()) == 0:
		# the graph has never run !!!
		raise IOError("No given dataset could be used to run the graph")


	evaluation_output = dict()

	for output_to_eval in outputs_to_eval:
		evaluation_output[output_to_eval.name] = dict()
		print "Output: %s"%(output_to_eval.name)
		for brave_annotator in tp[output_to_eval.name].keys():
			print "Annotator: %s"%brave_annotator
			evaluation_output[output_to_eval.name][brave_annotator] = dict(
				sensitivity=(tp[output_to_eval.name][brave_annotator], tp[output_to_eval.name][brave_annotator]+fn[output_to_eval.name][brave_annotator])
			)
			try:
				print "Sensitivity: %f%% (%d/%d)"%(
					100*float(tp[output_to_eval.name][brave_annotator])/float(tp[output_to_eval.name][brave_annotator]+fn[output_to_eval.name][brave_annotator]),
					tp[output_to_eval.name][brave_annotator],
					tp[output_to_eval.name][brave_annotator]+fn[output_to_eval.name][brave_annotator]
				)
			except ZeroDivisionError:
				print "Sensitivity: N/A"

			if annotator in fp[output_to_eval.name].keys():
				evaluation_output[output_to_eval.name][brave_annotator]["fdr"] = (fp[output_to_eval.name][brave_annotator], tp[output_to_eval.name][brave_annotator]+fp[output_to_eval.name][brave_annotator])
				print "False Discovery Rate: %f%% (%d/%d)"%(
					100*float(fp[output_to_eval.name][brave_annotator])/float(fp[output_to_eval.name][brave_annotator]+tp[output_to_eval.name][brave_annotator]),
					fp[output_to_eval.name][brave_annotator],
					fp[output_to_eval.name][brave_annotator]+tp[output_to_eval.name][brave_annotator]
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
