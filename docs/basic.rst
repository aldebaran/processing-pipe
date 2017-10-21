Basic usage
===========

Create your first graph
-----------------------

In the most basic version, a graph is a set of ecto cells connected to each
other. In the described graph, sources and sinks must be included, as none will
be added by processing pipe.

At first, your graph is simply a JSON file containing two items:

::

	{
		cells:[],
		connections:[]
	}

As you would guess, ``cells`` contains the list of your cells, and 
``connections``, the list of connections between your cells. 

The description of a cell looks like this:

::

	{
		"name":"MY_CELL_NAME",
		"module": "my_cells",
		"cell_type": "cell_class_name",
		"params": [
			{
				"param_name":"cell_param",
				"values": ["values"]
			}
		]
	}

Let's explain this in details:

name
	In Ecto framework, every cell must have a unique name. So here, you define
	your cell's name. It can be anything, as long as it is unique.

module
	The python module in which your cell is defined.

cell_type
	The name of the class representing your cell

params
	Contains the parameters to give to your cell.

.. warning::

	``values`` always expects a list of values. This way, you can easilly run
	your graph with different settings (more on that later). If you only need to
	set your parameter to a single value, just put a one-element list.


In order to run a graph, you need to have at least two cells. Let's image we
defined two cells called ``a`` and ``b``, both with an ``input`` and an
``output`` port. Then the connections between those two cells can be described
like this::

	"connections":[
		{"from":"a.output", "to":"b.input"}
	]

And that's it.

To finish this section, here is a more complete example of a graph::

	{
		"cells": [
			{
				"name": "opening",
				"module": "ecto_opencv.highgui",
				"cell_type": "imread",
				"params": [
					{
						"param_name":"image_file",
						"values": ["cat.jpg"]
					}
				]
			},
			{
				"name": "cvt",
				"module": "ecto_opencv.imgproc",
				"cell_type": "cvtColor",
				"params": [
					{
						"param_name":"flag",
						"values": [
							"ecto_opencv.imgproc.BGR2GRAY",
							"ecto_opencv.imgproc.BGR2RGB",
							"ecto_opencv.imgproc.RGB2GRAY"
						]
					}
				]
			},
			{
				"name": "save",
				"module": "ecto_opencv.highgui",
				"cell_type": "ImageSaver",
				"params": [
					{
						"param_name":"filename_format",
						"values": ["cat%d.jpg"]
					}
				]
			}
		],
		"connections":[
			{"from":"opening.image", "to":"cvt.image"},
			{"from":"cvt.image","to":"save.image"}
		]
	}

This graph will create three cells imported from the ``ecto_opencv.highgui``
package and connect them together. The first cell opens an image called
``cat.jpg``, the second cell performs three different color conversions on that
image and the last cell saves the resulting images under ``cat0.jpg``,
``cat1.jpg`` and ``cat2.jpg``.

To test this graph, you can copy-paste this code into a file that you can call,
let's say ``graph.json``, then find an image you can rename ``cat.jpg`` that you
will place next to your graph. Then run::

	processing-pipe run graph.json

And you can now watch the newly created images. Congratulations, you just ran
your first graph !
can rename into cat.jpg

.. insert an example here