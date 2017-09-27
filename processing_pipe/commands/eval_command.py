# -*- coding: utf-8 -*-

# Standard libraries
import bisect
import copy
import glob
import os
import time
from warnings import warn

# Third-party libraries
import argparse
import qidata
from qidata import QiDataSet, isDataset, DataType
from ecto_opencv import highgui
from ecto_qidata import qidata_image

# Local modules
from processing_pipe.graph import Graph
from processing_pipe.utils import loadJSONFile

DESCRIPTION = "Evaluate a given processing graph"

def createValueComparator(comparison_rule):
	# Create comparator
	if "" == comparison_rule[0]:
		default_comparison = "True"
		def get_annotation(x):
			return x
	else:
		annotation_prop_type, annotation_prop_name=comparison_rule[0].split(":")
		default_comparison = "Strict"
		if "attr" == annotation_prop_type:
			def get_annotation(x):
				return getattr(x,annotation_prop_name)
		elif "key" == annotation_prop_type:
			def get_annotation(x):
				return x[annotation_prop_name]
		elif "item" == annotation_prop_type:
			def get_annotation(x):
				return x[int(annotation_prop_name)]

	if "" == comparison_rule[1]:
		def get_output(y):
			return y
	else:
		output_prop_type, output_prop_name=comparison_rule[1].split(":")
		if "attr" == output_prop_type:
			def get_output(y):
				return getattr(y,output_prop_name)

		elif "key" == output_prop_type:
			def get_output(y):
				return y[output_prop_name]

		elif "item" == output_prop_type:
			def get_output(y):
				return y[int(output_prop_name)]

	comparison_details = (default_comparison\
	                         if "" == comparison_rule[2]\
	                         else comparison_rule[2]).split(":")


	if "True" == comparison_details[0]:
		return lambda x,y: True

	elif "Strict" == comparison_details[0]:
		return lambda x,y: get_annotation(x) == get_output(y)

	elif "Loose" == comparison_details[0]:
		try:
			comparison_param = float(comparison_details[1])
		except KeyError:
			warn("An additional parameter is necessary when using \"Loose\" comparison")
			raise
		except ValueError:
			warn("Only numbers can be used as parameters for \"Loose\" comparison")
			raise
		return lambda x,y: get_annotation(x) >= get_output(y)-comparison_param\
		                   and get_annotation(x) <= get_output(y)+comparison_param
	else:
		raise Exception("Unsupported comparison mode %s"%comparison_type)

def createLocationComparator(annot_location):
	# Create comparator
	if "None" == annot_location:
		def loc_compare(x,y):return True
	else:
		if "" == annot_location:
			def get_output_location(x):
				return x
		else:
			functions = []
			def get_output_location(x):
				for location_address in annot_location.split(","):
					location_prop_type, location_prop_name=location_address.split(":")
					if "attr" == location_prop_type:
						x = getattr(x,location_prop_name)
					elif "key" == location_prop_type:
						x = x[location_prop_name]
					elif "item" == location_prop_type:
						x = x[int(location_prop_name)]
					else:
						raise RuntimeError("Invalid location value: %s"%location_address)
				return x

		def loc_compare(x,y):
			if x is None:
				return True
			output_location = get_output_location(y)

			# Annotation is a bounding box defined by the two extremal points
			bbox_dimension = len(x[0])

			# Output must be a list representing a point or a bounding box
			if len(output_location) != 2:
				# output location is a point
				out_loc_is_point = True
				out_loc_dimension = len(output_location)
			else:
				if isinstance(output_location[0], list):
					# output location is roi
					out_loc_is_point = False
					out_loc_dimension = len(output_location[0])
				else:
					# output location is a 2D point
					out_loc_is_point = True
					out_loc_dimension = 2

			if out_loc_dimension == bbox_dimension:
				# Output location has the same dimension as annotation location
				pass
			else:
				# TODO: projection needed
				# Return false for now
				return False

			if out_loc_is_point:
				# Output location is a point, make sure it is included in the
				# annotation box
				for i in range(bbox_dimension):
					if output_location[i] < x[0][i]\
					   or output_location[i] > x[1][i]:
						return False
			else:
				# Output location is a roi
				intersection_box = [None]*bbox_dimension
				common_hyper_volume = 1
				annot_hyper_volume = 1
				out_hyper_volume = 1
				for i in range(bbox_dimension):
					if output_location[1][i] < x[0][i]\
					   or x[1][i] < output_location[0][i]:
						# No intersection between locations
						return False

					common_hyper_volume *= (
					    min(x[1][i], output_location[1][i])\
					    - max(x[0][i], output_location[0][i])
					)
					annot_hyper_volume *= (x[1][i]-x[0][i])
					out_hyper_volume *= (output_location[1][i]-output_location[0][i])
				return common_hyper_volume == out_hyper_volume\
				       or (2*common_hyper_volume>annot_hyper_volume\
				           and 2*common_hyper_volume>out_hyper_volume)
			return True

	return loc_compare

def specifyName(basetype, comparison_rule):
	if "" == comparison_rule[0]:
		return ""
	else:
		a, b=comparison_rule[0].split(":")
		if "attr" == a:
			return "%s.%s"%(basetype,b)
		elif "key" == a:
			return "%s[%s]"%(basetype,b)
		elif "item" == a:
			return "%s[%d])"%(basetype,int(b))

class OutputDescription:
	is_list = False
	metadata_type = None
	property_name_to_test = None
	comparison_function = None

	def __init__(self, description, comparison_rules):
		self.true_positives = dict()
		self.false_negatives = dict()
		self.false_positives = dict()
		self.can_be_evaluated_by = list()

		# Check if output is a list
		if description["qidata_type"][0] == "<" and description["qidata_type"][-1] == ">":
			# Output is a list
			self.is_list = True
			description["qidata_type"] = description["qidata_type"][1:-1]

		# Generate name
		self.name = "%s.%s(%s"%(description["cell_id"],
		                        description["port_name"],
		                        description["qidata_type"])

		self.name += specifyName(description["qidata_type"], comparison_rules[0])
		for i in comparison_rules[1:]:
			self.name += "&"+specifyName(description["qidata_type"], i)
		self.name += ")"

		# Get output type
		self.metadata_type = description["qidata_type"]

		self.comparators = [createValueComparator(x) for x in comparison_rules]

		def value_compare(x,y):
			for comparator in self.comparators:
				if not comparator(x,y):
					return False
			return True
		self.value_match = value_compare

		# Get annotation location property
		self.location_match = createLocationComparator(description.get("location", "None"))

def compare(annotations, outputs, output_desc):
	annotations = copy.deepcopy(annotations)
	res = [0,0,0,0]

	for output in outputs:
		for i in range(len(annotations)):
			annot = annotations[i]
			if output_desc.location_match(annot[1], output)\
			   and output_desc.value_match(annot[0], output):
				res[0] += 1
				break
		else:
			# If none was found, mark it and continue to iterate immediately
			res[1] += 1
			continue
		annotations.pop(i)
	res[2] += len(annotations)

	return res

def parseOutputDescription(outputs_description):
	res = []
	for graph_output in outputs_description:
		if not graph_output.has_key("qidata_type"):
			# This output does not need to be evaluated
			res.append(None)
		else:
			res.append(OutputDescription(graph_output, graph_output.get("compare", [["","",""]])))
	return res

def validateInputSets(input_datasets, inputs_description, outputs_description):
	out = []
	try:
		while 1:
			input_qidataset = input_datasets.pop(0)

			# Check if folder is a qidataset:
			if not isDataset(input_qidataset):
				print "%s is not a valid QiDataSet"%input_qidataset
				continue

			# Check if dataset provides annotations for outputs
			# and required input datatypes
			with qidata.QiDataSet(input_qidataset, "r") as _ds:

				inputs_required_by_type = dict()

				for input_desc in inputs_description:
					if not inputs_required_by_type.has_key(input_desc["qidata_type"]):
						inputs_required_by_type[input_desc["qidata_type"]] = 1
					else:
						inputs_required_by_type[input_desc["qidata_type"]] += 1

				_all_required_data_available = True
				for required_input_type, n in inputs_required_by_type.iteritems():
					if len(_ds.getStreamsOfType(qidata.DataType[required_input_type])) < n:
						_all_required_data_available = False

				if not _all_required_data_available:
					print "%s dataset does not have all required data to run the given graph"%input_qidataset
					continue

				_something_can_be_evaluated = False
				for output_to_eval in outputs_description:
					if output_to_eval is None: continue

					for k, v in _ds.annotations_available.iteritems():
						if not output_to_eval.metadata_type == k[1]:
							continue
						output_to_eval.can_be_evaluated_by.append((input_qidataset,k[0]))
						_something_can_be_evaluated = True

			if not _something_can_be_evaluated:
				print "Annotations is not complete enough in %s dataset to evaluate what you want"%input_qidataset
				continue
			else:
				out.append(input_qidataset)
	except IndexError:
		# We arrive here when there is no more file to test
		pass

	return out

def validateInputFiles(input_datafiles, input_description, outputs_description):
	out = []
	try:
		while 1:
			input_qidatafile = input_datafiles.pop(0)
			# Check if file contains annotation for outputs
			# and required input datatype
			try:
				with qidata.open(input_qidatafile, "r") as _f:
					metadata = _f.annotations
					file_qidatatype = _f.type
			except TypeError:
				# File is not supported by QiData. Skip !
				print "%s is not a valid QiDataFile"%input_qidatafile
				continue

			if str(file_qidatatype) != input_description[0]["qidata_type"]:
				continue

			_something_can_be_evaluated = False
			for output_to_eval in outputs_description:
				if output_to_eval is None: continue

				# output_to_eval.can_be_evaluated_by[input_qidatafile] = []
				# output_has_fp_enabled_on[output_to_eval][input_qidatafile] = []

				for annotator, annotations in metadata.iteritems():
					if not output_to_eval.metadata_type in annotations.keys():
						continue
					output_to_eval.can_be_evaluated_by.append((input_qidatafile,annotator))
					_something_can_be_evaluated = True
					# output_has_fp_enabled_on[output_to_eval][input_qidatafile].append(annotator)

			if not _something_can_be_evaluated:
				print "Annotations is not complete enough in %s file to evaluate what you want"%input_qidatafile
				continue
			else:
				out.append(input_qidatafile)
	except IndexError:
		# We arrive here when there is no more file to test
		pass

	return out

def initEvaluationGraph(graph_description):
	# Create graph based on JSON
	graph = Graph.createFromDict(graph_description)

	# Unset the graph inputs (input will be fed by newly added cells)
	graph.clearGraphInputs()

	# Create cells to feed inputs
	input_provider_index = 0
	for graph_input in graph_description["inputs"]:

		if graph_input["qidata_type"].startswith("IMAGE"):
			# Add image opening cell
			graph.addCell(
				highgui.imread(
					"input_provider_%d"%input_provider_index,
					mode=getattr(highgui,graph_input.get("mode", "UNCHANGED"))
				)
			)

			graph.connect(
				"input_provider_%d"%input_provider_index,
				"image",
				graph_input["cell_id"],
				graph_input["port_name"]
			)

		elif graph_input["qidata_type"].startswith("CAMERA"):
			# Add image opening cell
			graph.addCell(
				qidata_image.imread(
					"input_provider_%d"%input_provider_index,
					mode=graph_input.get("mode", "UNCHANGED")
				)
			)

			graph.connect(
				"input_provider_%d"%input_provider_index,
				"qidata_image",
				graph_input["cell_id"],
				graph_input["port_name"]
			)
			graph_input["qidata_type"] = graph_input["qidata_type"].replace("CAMERA","IMAGE")
		else:
			raise Exception("Input datatype %s is not yet supported"%graph_input["qidata_type"])

		input_provider_index += 1

	return graph

def runOnFiles(graph, input_files):
	# Set graph inputs
	graph.setSwitchingParameters(
	    "input_provider_0",
	    "image_file",
	    input_files
	)

	# Run !
	start = time.time()
	graph.run()
	return time.time() - start

def runOnStreams(graph, streams, starting_ts):

	# Init situation
	while streams[0][0] <= starting_ts:
		change = streams.pop(0)
		input_to_set = change[1]
		file_to_set = change[2]
		graph.setSwitchingParameters(
		    "input_provider_%d"%input_to_set,
		    "image_file",
		    [file_to_set]
		)

	# Run !
	processing_time = 0
	current_ts = starting_ts
	results = []
	try:
		while True:
			before_run = time.time()
			graph.run()
			processing_time += time.time()-before_run
			results.extend(graph.result)
			change = streams.pop(0)
			next_ts = change[0]
			input_to_set = change[1]
			file_to_set = change[2]
			graph.setSwitchingParameters(
			    "input_provider_%d"%input_to_set,
			    "image_file",
			    [file_to_set]
			)
			current_ts = next_ts
	except IndexError:
		# Files have all been used
		pass
	return results, processing_time

def evaluateOnFiles(output_descriptions, results, inputs, proc_time):

	run_per_file = len(results) / len(inputs)
	mean_execution_time = proc_time / len(results)
	evaluation = dict()
	evaluation["_time_"]=mean_execution_time

	for output_desc in output_descriptions:
		if output_desc is None: continue
		for _,brave_annotator in output_desc.can_be_evaluated_by:
			if not output_desc.true_positives.has_key(brave_annotator):
				output_desc.true_positives[brave_annotator] = [0]*run_per_file
				output_desc.false_negatives[brave_annotator] = [0]*run_per_file
				output_desc.false_positives[brave_annotator] = [0]*run_per_file

	for file_index in range(len(inputs)):
		input_qidatafile = inputs[file_index]
		with qidata.open(input_qidatafile, "r") as _f:
			annotations = _f.annotations

		# Retrieve annotators of this file that annotates the type we want
		annotators = dict()
		for output_desc in output_descriptions:
			if output_desc is None: continue
			annotators[output_desc] = [x[1] for x in output_desc.can_be_evaluated_by if x[0]==input_qidatafile]
			# for _f, brave_annotator in output_to_eval.can_be_evaluated_by:
			# 	if _f == input_qidatafile:
			# 		annotators[output_desc].append(brave_annotator)

		for i in range(run_per_file):
			result = results[run_per_file*file_index + i]

			outputs = []
			for (out_description, graph_output) in zip(output_descriptions, result["outputs"]):
				if out_description is None: continue
				if not out_description.is_list:
					graph_output = [graph_output]

				for annotator in annotators[out_description]:
					try:
						annotation_list = annotations[annotator][out_description.metadata_type]
					except KeyError:
						annotation_list = []
					res = compare(annotation_list, graph_output, out_description)
					out_description.true_positives[annotator][i] += res[0]
					out_description.false_positives[annotator][i] += res[1]
					out_description.false_negatives[annotator][i] += res[2]

	print "Mean execution time: %f s"%evaluation["_time_"]
	for output_desc in output_descriptions:
		if output_desc is None: continue
		evaluation[output_desc.name] = dict()
		print "Output: %s"%(output_desc.name)
		for brave_annotator in output_desc.true_positives.keys():
			print "Annotator: %s"%brave_annotator
			evaluation[output_desc.name][brave_annotator] = list()
			for i in range(run_per_file):
				print "Configuration: %d"%(i+1)
				evaluation[output_desc.name][brave_annotator].append(
				  dict(
				    sensitivity=(
				      output_desc.true_positives[brave_annotator][i],
				      output_desc.true_positives[brave_annotator][i]\
				       + output_desc.false_negatives[brave_annotator][i]
				    ),
				    fdr=(
				      output_desc.false_positives[brave_annotator][i],
				      output_desc.true_positives[brave_annotator][i]\
				       + output_desc.false_positives[brave_annotator][i]
				    )
				  )
				)
				try:
					print "Sensitivity: %f%% (%d/%d)"%(
						100*float(output_desc.true_positives[brave_annotator][i])/float(output_desc.true_positives[brave_annotator][i]+output_desc.false_negatives[brave_annotator][i]),
						output_desc.true_positives[brave_annotator][i],
						output_desc.true_positives[brave_annotator][i]+output_desc.false_negatives[brave_annotator][i]
					)
				except ZeroDivisionError:
					print "Sensitivity: N/A"

				try:
					print "False Discovery Rate: %f%% (%d/%d)"%(
						100*float(output_desc.false_positives[brave_annotator][i])/float(output_desc.false_positives[brave_annotator][i]+output_desc.true_positives[brave_annotator][i]),
						output_desc.false_positives[brave_annotator][i],
						output_desc.false_positives[brave_annotator][i]+output_desc.true_positives[brave_annotator][i]
					)
				except ZeroDivisionError:
					print "False Discovery Rate: N/A"

	return evaluation

def evaluateOnStreams(output_descriptions, results, qidataset, streams, start_ts, proc_time):

	streams = streams[bisect.bisect_right([x[0] for x in streams], start_ts)-1:]
	run_per_file = len(results) / len(streams)
	mean_execution_time = proc_time / len(results)
	evaluation = dict()
	evaluation["_time_"] = mean_execution_time

	for output_desc in output_descriptions:
		if output_desc is None: continue
		for _,brave_annotator in output_desc.can_be_evaluated_by:
			if not output_desc.true_positives.has_key(brave_annotator):
				output_desc.true_positives[brave_annotator] = [0]*run_per_file
				output_desc.false_negatives[brave_annotator] = [0]*run_per_file
				output_desc.false_positives[brave_annotator] = [0]*run_per_file

	for file_index in range(len(streams)):
		input_qidatafile = streams[file_index][2]
		with qidata.open(input_qidatafile, "r") as _f:
			annotations = _f.annotations

		# Retrieve annotators of this file that annotates the type we want
		annotators = dict()
		for output_desc in output_descriptions:
			if output_desc is None: continue
			annotators[output_desc] = [x[1] for x in output_desc.can_be_evaluated_by if x[0]==qidataset]

		for i in range(run_per_file):
			result = results[run_per_file*file_index + i]

			outputs = []
			for (out_description, graph_output) in zip(output_descriptions, result["outputs"]):
				if out_description is None: continue
				if not out_description.is_list:
					graph_output = [graph_output]

				for annotator in annotators[out_description]:
					try:
						annotation_list = annotations[annotator][out_description.metadata_type]
					except KeyError:
						annotation_list = []
					res = compare(annotation_list, graph_output, out_description)
					out_description.true_positives[annotator][i] += res[0]
					out_description.false_positives[annotator][i] += res[1]
					out_description.false_negatives[annotator][i] += res[2]

	print "Mean execution time: %f s"%evaluation["_time_"]
	for output_desc in output_descriptions:
		if output_desc is None: continue
		evaluation[output_desc.name] = dict()
		print "Output: %s"%(output_desc.name)
		for brave_annotator in output_desc.true_positives.keys():
			print "Annotator: %s"%brave_annotator
			evaluation[output_desc.name][brave_annotator] = list()
			for i in range(run_per_file):
				print "Configuration: %d"%(i+1)
				evaluation[output_desc.name][brave_annotator].append(
				  dict(
				    sensitivity=(
				      output_desc.true_positives[brave_annotator][i],
				      output_desc.true_positives[brave_annotator][i]\
				       + output_desc.false_negatives[brave_annotator][i]
				    ),
				    fdr=(
				      output_desc.false_positives[brave_annotator][i],
				      output_desc.true_positives[brave_annotator][i]\
				       + output_desc.false_positives[brave_annotator][i]
				    )
				  )
				)
				try:
					print "Sensitivity: %f%% (%d/%d)"%(
						100*float(output_desc.true_positives[brave_annotator][i])/float(output_desc.true_positives[brave_annotator][i]+output_desc.false_negatives[brave_annotator][i]),
						output_desc.true_positives[brave_annotator][i],
						output_desc.true_positives[brave_annotator][i]+output_desc.false_negatives[brave_annotator][i]
					)
				except ZeroDivisionError:
					print "Sensitivity: N/A"

				try:
					print "False Discovery Rate: %f%% (%d/%d)"%(
						100*float(output_desc.false_positives[brave_annotator][i])/float(output_desc.false_positives[brave_annotator][i]+output_desc.true_positives[brave_annotator][i]),
						output_desc.false_positives[brave_annotator][i],
						output_desc.false_positives[brave_annotator][i]+output_desc.true_positives[brave_annotator][i]
					)
				except ZeroDivisionError:
					print "False Discovery Rate: N/A"

	return evaluation

def evalAlgorithm(args):
	# Prepare resulting evaluation dictionnary
	eval_res = dict()

	# Test data has been given in arguments
	input_datasets = glob.glob(args.input_dataset)
	input_datafiles = glob.glob(args.input_datafile)
	if len(input_datasets) == 0 and len(input_datafiles) == 0:
		raise IOError("The given pattern does not match any folder nor file name")

	# Read graph description (will raise if file is not a proper JSON file)
	graph_description = loadJSONFile(args.GRAPH)

	# If there is more than one input, do not use given files
	if len(graph_description["inputs"])>1 and len(input_datafiles)>0:
		warn("Files cannot be used to feed a graph with more than one input")
		input_datafiles = []

	# Retrieve outputs to evaluate
	outputs_description = parseOutputDescription(graph_description["outputs"])

	# Create graph based on JSON and adapt it to evaluation
	graph = initEvaluationGraph(graph_description)

	# Filter out datasets that can't be used for evaluation
	valid_input_datasets = validateInputSets(input_datasets,
	                                         graph_description["inputs"],
	                                         outputs_description)

	# Filter out datafiles that can't be used for evaluation
	valid_input_datafiles = validateInputFiles(input_datafiles,
	                                           graph_description["inputs"],
	                                           outputs_description)

	if len(valid_input_datasets) == 0 and len(valid_input_datafiles) == 0:
		raise Exception(
		    "None of the given data can be used to evaluate the given graph"
		)

	# Run the graph
	for input_dataset in valid_input_datasets:
		input_types_index = dict()
		input_to_stream_map = list()
		for graph_input in graph_description["inputs"]:
			input_data_type = qidata.DataType[graph_input["qidata_type"]]
			if not input_types_index.has_key(input_data_type):
				input_types_index[input_data_type] = 0
			else:
				input_types_index[input_data_type] += 1

			with QiDataSet(input_dataset, "r") as _ds:
				input_to_stream_map.append(
				    _ds.getStreamsOfType(
				        input_data_type
				    ).values()[input_types_index[input_data_type]]
				)

		streams = [
		  (
		    float(ts[0])+float(ts[1])/1000000000,
		    input_index,
		    os.path.join(input_dataset, filename)
		  ) for input_index in range(len(input_to_stream_map))\
		      for ts,filename in input_to_stream_map[input_index].iteritems()
		]
		streams = sorted(streams)
		start_ts = max([sorted(x.keys())[0] for x in input_to_stream_map])
		start_ts = float(start_ts[0])+float(start_ts[1])/1000000000

		results, processing_time = runOnStreams(graph, sorted(streams), start_ts)

		eval_res[input_dataset] = evaluateOnStreams(outputs_description,
		                                            results,
		                                            input_dataset,
		                                            streams,
		                                            start_ts,
		                                            processing_time)

	if len(valid_input_datafiles) > 0:
		processing_time = runOnFiles(graph, valid_input_datafiles)

		# Evaluate results
		eval_res["_free_files_"] = evaluateOnFiles(outputs_description,
		                                           graph.result,
		                                           valid_input_datafiles,
		                                           processing_time)

	return eval_res

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
