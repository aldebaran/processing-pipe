import SBRtools as tools
import app
import gui
import ecto

class ApiEctoGraph:
  def __init__(self):
    self.cellList = dict()
    self.cellParams = dict()
    self.plasm = ecto.Plasm()
    
  def addCell(self, cellName, cellId, dictOfValue):
    l = cellName.split(".")
    cell = l[len(l)-1]
    p = l[:-1]
    package = str()
    for s in p:
      package = package+s+"."
    package = package[:-1]
    cell = tools.getCell(package, cell)
    values = dict()
    
    for v in dictOfValue:
      values[v] = dictOfValue[v][0]
     
    self.cellList[cellId] = (cell(cellId, **values))
    self.cellParams[cellId] = dictOfValue
    
  def connectCells(self, cellA, outputName, cellB, inputName):
    self.plasm.connect(cellA[outputName] >> cellB[inputName])
  
  def disconnectCells(self, cellA, outputName, cellB, inputName):
    self.plasm.disconnect(cellA, outputName, cellB, inputName)
    
  def exec_(self):
    d = app.Struct(self.plasm, self.cellList, self.cellParams)
    a = app.Model(data = d)
    a.exec_()