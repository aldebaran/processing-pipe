# -*- coding: utf-8 -*-

# Standard Library
import errno
import os
import shutil

# Local modules
import processing_pipe

# ──────────
# Parameters

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/")
SANDBOX_FOLDER = "/tmp/processing_pipe/"

# ──────────
# Data files

GRAPH         = "simple_graph.json"
FD_GRAPH      = "facedetection_graph.json"
PARAM_GRAPH   = "parametrized_graph.json"
IMAGE         = "ryan.jpg"

# ─────────
# Utilities

def sandboxed(path):
	"""
	Makes a copy of the given path in /tmp and returns its path.
	"""
	source_path = os.path.join(DATA_FOLDER,    path)
	tmp_path    = os.path.join(SANDBOX_FOLDER, path)

	try:
		os.mkdir(SANDBOX_FOLDER)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise

	if os.path.isdir(source_path):
		if os.path.exists(tmp_path):
			shutil.rmtree(tmp_path)
		shutil.copytree(source_path, tmp_path)
	else:
		shutil.copyfile(source_path, tmp_path)

	return tmp_path

def sha1(file_path):
	import hashlib
	hasher = hashlib.sha1()
	with open(file_path,'rb') as file:
		file_data = file.read()
	hasher.update(file_data)
	return hasher.hexdigest()

def cleanData():
	if os.path.exists(SANDBOX_FOLDER):
		shutil.rmtree(SANDBOX_FOLDER)