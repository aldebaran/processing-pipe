# Standard library
import os
import pytest

# Third-party libraries
import argparse

@pytest.mark.parametrize("command_args",
	[
		[
			"tests/data/unknown_graph.json"
		],
	]
)
def test_failing_run_command(command_args, run_command_parser):
	parsed_arguments = run_command_parser.parse_args(command_args)
	with pytest.raises(SystemExit):
		parsed_arguments.func(parsed_arguments)

@pytest.mark.parametrize("command_args",
                          [
                            [
                              "tests/data/passthrough_image.json"
                            ],
                          ]
                        )
def test_run_command(command_args, run_command_parser):
	assert(not os.path.exists("/tmp/processing_pipe/ryan.jpg"))

	parsed_arguments = run_command_parser.parse_args(command_args)
	parsed_arguments.func(parsed_arguments)

	assert(os.path.exists("/tmp/processing_pipe/ryan.jpg"))
	os.remove("/tmp/processing_pipe/ryan.jpg")
