from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import SBRtools as t
import ecto
import argumentPipe

class ParamIterator:
  """
  A ParamIterator iterat on all combination of parameters value.
  ids: list of tuple {cell, str} (cell an ecto cell, str a param name)
  index: list of currents value index.
  params: list of values
  stop: set to True when reach the end of the iterator
  lastMod: list cell's ID, who store the id of all modify cell
  """
  def __init__(self, cellList, depthDict):
    """
    Constructor
    :param cellList: List of all cell
    :param depthDict: the association between cell's ID and there depth
    """
    self.index = list() #List of int
    self.ids = list() #List of pair {cell, str}
    self.lastMod = list() #List of str
    self.params = list() #List of list of object
    self.stop = False
    
    m = self.maxDepth(depthDict)
    
    for d in range(m+1, 0, -1):
      l = self.takeDepth(depthDict, d-1)
      for c in l:
	for p in cellList[c].params.items():
	  self.ids.append((cellList[c],p[0]))
	  self.index.append(0)
	  self.params.append(list())

    #print self.ids
    #print self.index
    #print self.params
      
  def maxDepth(self, depthDict):
    """
    Get the max depth value
    :param depthDict: the association between cell's ID and there depth
    :return: Max depth value
    """
    ret = 0
    for n in depthDict:
      ret = max(ret, depthDict[n])
      
    return ret
  
  def takeDepth(self, depthDict, d):
    """
    Return all cell from the graph for the given depth
    :param depthDict: the association between cell's ID and there depth
    :param d: The wanted depth
    :return: List of cell's ID
    """
    ret = list()
    
    for n in depthDict:
      if d == depthDict[n]:
	ret.append(n)

    return ret
   
  def get(self, i):
    """
    Get the tuple {cell, param, value} 
    :param i: the common index between {cell, param} and list of values
    """
    ret = (self.ids[i], self.params[i][self.index[i]])
    return ret
  

  
  def setParamList(self, cell, param, l): 
    """
    Set the list for a parameters
    :param cell: A valide ecto cell
    :param param: The param name
    :param l: The list of value
    """
    ind = self.ids.index((cell, param))
    self.params[ind] = l
    if len(l) is not 0:
      t.setInput(cell, param, l[0])
  
  def increment(self, lastMod, i = 0):
    """
    Set the next combination of parameters values
    :param lastMod: In/out parameter, all modify cell
    :param i: current Parameters index
    """
    
    if len(self.params) == i:
      self.stop = True
      return
    
    self.index[i] = self.index[i] + 1
    
    if not self.stop:
      if self.index[i] == len(self.params[i]) :
	self.index[i] = 0
	self.increment(lastMod, i +1)
      
   
      if not len(self.params[i]) == 0:
	t.setInput(self.get(i)[0][0], self.get(i)[0][1], self.get(i)[1])
	lastMod.append(self.ids[i][0].name())
	
 

  def next(self):
    """
    Receive the cell's ID who were modified and return it
    
    :return: Cell's ID
    """
    lastMod = list()
    self.increment(lastMod, 0)
    
    return lastMod
  
  def reset(self):
    """
    Reset the iterator to the begining
    """
    self.stop = False
    for i in range(0, len(self.index), 1):
      self.index[i] = 0
      
      if len(self.params[i]) is not 0:
	t.setInput(self.ids[i][0], self.ids[i][1], self.params[i][0])
      
  
class Struct:
  def __init__(self, plasm, cellList, dictOfvalue):
    self.plasm = plasm
    self.cellList = cellList
    self.dictOfvalue = dictOfvalue
    
class Model:
  """
  The model provide workflow execution.
  Object attribute:
  cellList: the complete cell list indexed by cell's ID
  sched: The workflow scheduler
  params: A parameters iterator
  """
  def __init__(self, data = None, filename = None):
    
    if not filename is None:
      self.initFile(filename)
    elif not data is None:
      self.cellList = data.cellList
      self.sched = ecto.CustomSchedulerSBR(data.plasm)
      print "Sched"
      #self.sched.execute(1)
      #self.sched.prepare_jobs(1)
      print "DEPTH MAP"
      print self.sched.getDepthMap()
      self.params = ParamIterator(self.cellList, self.sched.getDepthMap())
      
      d = data.dictOfvalue
      for p in d:
	c = self.cellList[p]
	for pa in d[p]:
	  self.params.setParamList(c, pa, d[p][pa])
    
  def initFile(self, fileName = ""):
    """
      Constructor.
      :param fileName: The json filename
    """
    j = t.fileToJson(fileName)
    plasm, self.cellList = t.createGraph(j)
    self.sched = ecto.CustomSchedulerSBR(plasm)
    print "Sched"
    #self.sched.execute(1)
    #self.sched.prepare_jobs(1)
    print "DEPTH MAP"
    print self.sched.getDepthMap()
    self.params = ParamIterator(self.cellList, self.sched.getDepthMap())
    ps = t.getAllParams(j)
    
    for p in ps:
      self.params.setParamList(self.cellList[p[0]], p[1], ps[p])
      
   
    
    #self.exec_()
    
  def exec_(self):
    """
    Callback function
    Perform the workflow execution. An execution is perform from each parameters combination send by the ParamIterator
    """
    
    self.params.reset()

    print "New execution"
    v = list()
    while not self.params.stop:
      #print v
      if not self.params.stop:
	if len(v) == 0:
	  self.sched.execute(1)
	  #self.sched.execute_thread()
	else:
	  self.sched.execute(v)
      v = self.params.next()
      
  def setData(self, cell, param, listValue):
    """
    Callback function
    Set a parameters list for a cell in the ParamIterator
    :param cell: A valide ecto cell
    :param param: A param name
    :param listValue: A list of value
    """
    self.params.setParamList(cell, param, listValue)
  
    
   
    
if __name__ == "__main__":
  app = QApplication(sys.argv)
  print argumentPipe.f
  print argumentPipe.j
  
  model = Model(filename = argumentPipe.f)
  
  model.exec_()
  if argumentPipe.g is "True":
    import gui
    g = gui.Gui(model.cellList)
    g.execute.connect(model.exec_)
    g.setData.connect(model.setData)
  
  exit(app.exec_())