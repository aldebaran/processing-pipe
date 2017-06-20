# Standard library
import pytest

# Third-party libraries
import argparse

# Local modules
import fixtures
from processing_pipe.commands import (
	eval_commands,
)

@pytest.mark.parametrize("command_args",
	[
		[
			"--input-dataset",
			"nothing",
			"tests/data/face_detection_image_stereo.json"
		],
		[
			"tests/data/face_detection_image_stereo.json"
		],
		[
				"--input-dataset",
				"tests/data/kenzo_qidataset",
				"tests/data/face_detection_image_3d.json"
		],
	]
)
def test_failing_eval_command(command_args):
	parser = eval_commands.make_command_parser(argparse.ArgumentParser())
	parsed_arguments = parser.parse_args(command_args)
	with pytest.raises(IOError):
		parsed_arguments.func(parsed_arguments)

@pytest.mark.parametrize("command_args,expected",
	[
		(
			[
				"--input-dataset",
				"tests/data/kenzo_qidataset",
				"tests/data/face_detection_image_stereo.json"
			],
			{
				"fd.faces":dict(aduhamel=dict(fdr=(0,22), sensitivity=(22,38)))
			}
		),
		(
			[
				"--input-dataset",
				"tests/data/kenzo_qidataset",
				"tests/data/face_detection_with_person_output.json"
			],
			{
				"fd.faces":dict(mdjabri=dict(sensitivity=(12,19)))
			}
		),
		(
			[
				"--input-dataset",
				"tests/data/guillaume_qidataset",
				"tests/data/face_detection_image_stereo.json"
			],
			{
				"fd.faces":dict(aduhamel=dict(fdr=(0,46), sensitivity=(46,46)))
			}
		),
		(
			[
				"--input-dataset",
				"tests/data/*_qidataset",
				"tests/data/face_detection_image_stereo.json"
			],
			{
				"fd.faces":dict(aduhamel=dict(fdr=(0,68), sensitivity=(68,84)))
			}
		),
		(
			[
				"--input-datafile",
				"tests/data/kenzo_qidataset/stereo_017.png",
				"tests/data/face_detection_image_stereo.json"
			],
			{
				"fd.faces":dict(aduhamel=dict(fdr=(0,2), sensitivity=(2,2)))
			}
		),
		(
			[
				"--input-datafile",
				"tests/data/kenzo_qidataset/stereo_*.png",
				"tests/data/face_detection_image_stereo.json"
			],
			{
				"fd.faces":dict(aduhamel=dict(fdr=(0,22), sensitivity=(22,38)))
			}
		),
		(
			[
				"--input-dataset",
				"tests/data/kenzo_qidataset",
				"tests/data/double_face_detection_image_stereo.json"
			],
			{
				"fd1.faces":dict(aduhamel=dict(fdr=(0,22), sensitivity=(22,38))),
				"fd2.faces":dict(aduhamel=dict(fdr=(0,22), sensitivity=(22,38))),
			}
		),
	]
)
def test_eval_command(command_args, expected):
	parser = eval_commands.make_command_parser(argparse.ArgumentParser())
	parsed_arguments = parser.parse_args(command_args)
	res = parsed_arguments.func(parsed_arguments)
	assert(expected == res)