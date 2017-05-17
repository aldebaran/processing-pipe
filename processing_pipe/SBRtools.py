import json
import ecto
import types
"""
The SBRtools module provide some ecto cell manipulation, and graph generation

"""
def fileToJson(filename):
  """
    Load a json file.
    :param filename: A filename
    :return: A json object
  """
  f = open(filename, 'r')
  t = f.read()
  j = json.loads(t)
  return j

def getCell(package, name):
  
  ml = package.split(".")[1:]
  m = map(__import__, [package])[0]
  print m
  for ms in ml:
    print ms
    m = getattr(m, ms)
    
  return getattr(m, name)
  
  
def createCell(jsonObject):
  """
    Create an ecto cell from a JSON object
    :return: ecto cell
    :param jsonObject: a json node
  """
  ml = jsonObject["module"].split(".")[1:]
  
  m = map(__import__, [jsonObject["module"]])[0]
  
  for ms in ml:
    m = getattr(m, str(ms))
  
  c = getattr(m, jsonObject["type"])
  
  pl = jsonObject["params"]
  
  params = dict()
  for po in pl:
    
    if len(po["value"]) is not 0:
      v = po["value"][0]
      #print "Load"
      #print v
      if type(v) is types.UnicodeType:
	v = str(po["value"])
      params[po["name"]] = v
      
    #print "PARAMS:"
    #print params
  return c(str(jsonObject["name"]), **params)


def createGraph(jsonObject):
  """
  Create an ecto graph from an jsonObject.
  :param jsonObject: A fully load json object
  :return: An ecto plasm, and the complete cell list indexed by cell's ID
  """
  cellList = dict()
  plasm = ecto.Plasm()
  
  jsonList = jsonObject["graph"]
  
  for o in jsonList:
    c = createCell(o)
    cellList[c.name()] = c
  
  for o in jsonList:
      n = str(o["name"])
      for e in o["edge"]:
	plasm.connect(cellList[n][str(e["output"])] >> cellList[str(e["id"])][str(e["input"])])
	
  return (plasm, cellList)

def getAllParams(jsonObject):
  ret = dict()
  jsonList = jsonObject["graph"]
  for o in jsonList:
    ps = o["params"]
    for p in ps:
      l = p["value"]
      ret[(str(o["name"]),str(p["name"]))] = l
      
  
  return ret


def setInput(obj, name, value):
  """
    Set an input for an ecto cell.
    :param obj: An valide ecto cell object
    :param name: The string name for the input
    :param value: A valide value for the input
  """
  inp = getattr(obj, "inputs")
  
  if type(value) is types.UnicodeType:
    v = str(value)
  else:
    v = value
 
  setattr(inp, name, v)
  
def getOutput(obj, name):
  """
    Get an output value from an ecto cell
    :param obj: A valide ecto cell object
    :param name:  The string name for the output
    :return: The output value
  """
  out = getattr(obj, "outputs")
  return getattr(out, name)
    