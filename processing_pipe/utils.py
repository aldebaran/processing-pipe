"""
The utils module provide some ecto cell manipulation, and graph generation
"""

# Standard libraries
import json

def loadJSONFile(filename):
	"""
	Load a json file.
	:param filename: Name of the file containing the JSON description graph
	:return: A json object
	"""
	with open(filename, 'r') as f:
		return json.loads(f.read())

def createEctoCell(module, cell_type, name, params=list()):
	"""
	Create an ecto cell
	:param module: Python module containing the cell definition
	:param cell_type: Type of the cell to instanciate
	:param name: Name to give to the cell
	:param params: List of dict containing possible values for the cell parameters
	:return: Created ecto cell
	"""
	mod = __import__(module, globals(), locals(), [cell_type], 0)
	cell_builder = getattr(
	  mod,
	  cell_type
	)
	init_params = dict()
	for param in params:
		if len(param["values"])>0:
			# If value is a str and start with the module name, interpret it
			# as a global value
			for i in range(len(param["values"])):
				if isinstance(param["values"][i], basestring)\
				   and param["values"][i].startswith(module+'.'):
					attrs = param["values"][i][len(module)+1:].split('.')
					param_val = mod
					while len(attrs)>0:
						param_val = getattr(param_val, attrs.pop(0))
					param["values"][i] = param_val
			v = param["values"][0]
			if isinstance(v, unicode):
				v = str(v)
			init_params[param["param_name"]] = v
	return cell_builder(str(name),**init_params)
