# Standard library
import os
import pytest

# Third-party libraries
import argparse

# Local modules
from processing_pipe.__main__ import main

def test_main_call():
	with pytest.raises(SystemExit) as _s:
		main(["-v"])
	assert(0 == _s.value.code)
	with pytest.raises(SystemExit) as _s:
		main(["-h"])
	assert(0 == _s.value.code)
	with pytest.raises(SystemExit) as _s:
		main(["run", "-h"])
	assert(0 == _s.value.code)
	with pytest.raises(SystemExit) as _s:
		main(["eval", "-h"])
	assert(0 == _s.value.code)

def test_main_parser(main_command_parser):
	with pytest.raises(SystemExit) as _s:
		parsed_arguments = main_command_parser.parse_args(["-h"])
	assert(0 == _s.value.code)

@pytest.mark.parametrize("command_args",
	[
		[
			"tests/data/unknown_graph.json"
		],
	]
)
def test_failing_run_command(command_args, run_command_parser):
	parsed_arguments = run_command_parser.parse_args(command_args)
	with pytest.raises(SystemExit) as _s:
		parsed_arguments.func(parsed_arguments)
	assert(0 != _s.value.code)

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


@pytest.mark.parametrize("command_args,expected",
  [
    (
      [
        "tests/data/dummy_graph_for_eval.json"
      ],
      {
        "type":IOError,
        "message":"The given pattern does not match any folder nor file name"
      }
    ),
    (
      [
        "--input-datafile",
        "tests/data/non_existing.*.jpg",
        "tests/data/dummy_graph_for_eval.json"
      ],
      {
        "type":IOError,
        "message":"The given pattern does not match any folder nor file name"
      }
    ),
    (
      [
        "--input-datafile",
        "tests/data/ryan.jpg",
        "tests/data/dummy_graph_for_eval.json"
      ],
      {
        "type":Exception,
        "message":"None of the given data can be used to evaluate the given graph"
      }
    ),
  ]
)
def test_eval_command_fail(command_args, expected, eval_command_parser):
	parsed_arguments = eval_command_parser.parse_args(command_args)
	with pytest.raises(expected["type"]) as _e:
		parsed_arguments.func(parsed_arguments)
	assert(expected["message"] == _e.value.message)


@pytest.mark.parametrize("command_args,expected",
  [
    (
      [
        "--input-datafile",
        "tests/data/*.jpg",
        "tests/data/dummy_graph_for_eval.json"
      ],
      {
        "pt.out":dict(
          jdoe=[
            dict(fdr=(1,2), sensitivity=(1,1)),
            dict(fdr=(0,1), sensitivity=(1,1))
          ],
          jsmith=[
            dict(fdr=(1,2), sensitivity=(1,1)),
            dict(fdr=(0,1), sensitivity=(1,1)),
          ]
        ),
        "pt.out.age":dict(
          jdoe=[
            dict(fdr=(1,2), sensitivity=(1,1)),
            dict(fdr=(0,1), sensitivity=(1,1))
          ],
          jsmith=[
            dict(fdr=(1,2), sensitivity=(1,1)),
            dict(fdr=(0,1), sensitivity=(1,1)),
          ]
        ),
        "count.count":dict(
          jdoe=[
            dict(fdr=(0,1), sensitivity=(1,1)),
            dict(fdr=(0,1), sensitivity=(1,1))
          ],
          jsmith=[
            dict(fdr=(0,1), sensitivity=(1,1)),
            dict(fdr=(0,1), sensitivity=(1,1))
          ]
        )
      }
    ),
  ]
)
def test_eval_command(command_args, expected, eval_command_parser):
	parsed_arguments = eval_command_parser.parse_args(command_args)
	res = parsed_arguments.func(parsed_arguments)
	assert(res.has_key("_time_"))
	t = res.pop("_time_")
	assert(isinstance(t, float))
	assert(0 < t)
	assert(expected == res)
