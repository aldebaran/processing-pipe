#!/usr/bin/env python
# -*- coding: utf-8 -*-
#==============================================================================
#                            SOFTBANK  ROBOTICS
#==============================================================================
# PROJECT : Processing Pipe
# FILE : conftest.py
# DESCRIPTION :
"""
Prepare the conditions for proper unit testing
"""
#[MODULES IMPORTS]-------------------------------------------------------------
import errno
import os
import pytest
import shutil

import processing_pipe
from processing_pipe.utils import loadJSONFile

#[MODULE INFO]-----------------------------------------------------------------
__author__ = "sambrose"
__date__ = "2017-09-14"
__copyright__ = "Copyright 2017, Softbank Robotics (c)"
__version__ = "1.0.0"
__maintainer__ = "sambrose"
__email__ = "sambrose@softbankrobotics.com"

#[MODULE GLOBALS]--------------------------------------------------------------

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/")
SANDBOX_FOLDER = "/tmp/processing_pipe/"

GRAPH         = "simple_graph.json"
COPY_GRAPH    = "passthrough_image.json"
PARAM_GRAPH   = "parametrized_graph.json"
IMAGE         = "ryan.jpg"

#[MODULE CONTENT]--------------------------------------------------------------

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

@pytest.fixture(autouse=True, scope="function")
def begin(request):
	"""
	Add a finalizer to clean tmp folder after each test
	"""
	def fin():
		if os.path.exists(SANDBOX_FOLDER):
			shutil.rmtree(SANDBOX_FOLDER)

	request.addfinalizer(fin)

@pytest.fixture(scope="session")
def simple_graph():
	return loadJSONFile(os.path.join(DATA_FOLDER,GRAPH))

@pytest.fixture(scope="session")
def parametrized_graph():
	return loadJSONFile(os.path.join(DATA_FOLDER,PARAM_GRAPH))

@pytest.fixture(scope="session")
def copy_image_graph():
	return loadJSONFile(os.path.join(DATA_FOLDER,COPY_GRAPH))
