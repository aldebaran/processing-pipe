import sys
import utils as tools
import ecto

def write_only_property(func):
  return property(fset=func)

class Graph(object):
  """
  Represents a processing graph, wrapping ecto library
  """

  class _ParamIterator:
    """
    A ParamIterator iterates on all combination of parameters value.

    ids: list of tuple {cell, str} (cell an ecto cell, str a param name)
    index: list of currents value index.
    params: list of values
    lastMod: list cell's ID, who store the id of all modify cell
    """
    def __init__(self,
      cellList
    ):
      """
      Constructor
      :param cellList: List of all cell
      """
      self.cell_list = cellList

      # Storage for possible values
      # Key is (cell, parameter name)
      # Values are (list of possible values, index of currently selected value)
      self.parameter_storage = dict()

      # Keep keys of parameter storage in an ordered fashion
      # (most downstream in graph comes first)
      self.ordered_cells = list()

      # m = self.maxDepth(depthDict)

      # for d in range(m+1, 0, -1):
      #   l = self.takeDepth(depthDict, d-1)
      #   for c in l:
      #     for p in cellList[c].params.items():
      #       self.ids.append((cellList[c],p[0]))
      #       self.index.append(0)
      #       self.params.append(list())

    # def maxDepth(self, depthDict):
    #   """
    #   Get the max depth value
    #   :param depthDict: the association between cell's ID and there depth
    #   :return: Max depth value
    #   """
    #   ret = 0
    #   for n in depthDict:
    #     ret = max(ret, depthDict[n])

    #   return ret

    # def takeDepth(self, depthDict, d):
    #   """
    #   Return all cell from the graph for the given depth
    #   :param depthDict: the association between cell's ID and there depth
    #   :param d: The wanted depth
    #   :return: List of cell's ID
    #   """
    #   ret = list()

    #   for n in depthDict:
    #     if d == depthDict[n]:
    #       ret.append(n)

    #   return ret

    def initParamIteration(self, graph_depth_map):
      """
      Initializes the iterators necessary to switch parameters upon the run

      :param depthDict: the association between cell's ID and there depth in the graph
      """
      self.ordered_cells = sorted(
        self.parameter_storage.keys(),
        key=lambda x:graph_depth_map[x[0].name()],
        reverse = False
      )

    def setParameterPossibleValues(self, cell_id, param_name, values):
      """
      Set the list for a parameters
      :param cell_id: A valide ecto cell
      :param param_name: The param name
      :param values: The list of value
      """
      cell = self.cell_list[cell_id]
      self.parameter_storage[(cell, param_name)] = [values, 0]
      setattr(cell.params, param_name, values[0])

    def increment(self, reparametrized_cells, i=0):
      """
      Set the next combination of parameters values
      :param reparametrized_cells: In/out parameter, all modify cell
      :param i: current Parameters index
      """

      if len(self.parameter_storage) == i:
        raise StopIteration

      param_key = self.ordered_cells[i]
      param_value = self.parameter_storage[param_key]

      param_value[1] = param_value[1] + 1

      if param_value[1] == len(param_value[0]):
        param_value[1] = 0
        self.increment(reparametrized_cells, i+1)

      setattr(param_key[0].params, param_key[1], param_value[0][param_value[1]])
      reparametrized_cells.append(param_key[0].name())

    def setNextParamCombination(self):
      """
      Receive the cell's ID who were modified and return it

      :return: Cell's ID
      """
      reparametrized_cells = list()
      self.increment(reparametrized_cells)
      return reparametrized_cells

    def reset(self):
      """
      Reset the iterator to the begining
      """
      for (param_adress, param_value) in self.parameter_storage.iteritems():
        param_value[1] = 0
        cell, param_name = param_adress
        setattr(cell.params, param_name, param_value[0][0])

    def getCurrentParamCombination(self):
      out=dict()
      for (param_adress, param_value) in self.parameter_storage.iteritems():
        param_value = param_value[0][param_value[1]]
        cell, param_name = param_adress
        out[cell.name()+"."+param_name] = param_value
      return out

  class _InputHandler(object):
    """
    Stores and manages the inputs of a graph

    :param graph_cell_list: Dict referencing the cells in the graph
    """
    def __init__(self, graph_cell_list):
      self._cell_list = graph_cell_list
      self._input_port_list = []
      self._input_combinations = []

    def addInput(self, cell_id, port_name):
      self._input_port_list.append((cell_id, port_name))

    def __setitem__(self, item, value):
      setattr(
        self._cell_list[self._input_port_list[item][0]].inputs,
        self._input_port_list[item][1],
        value
      )

    @write_only_property
    def input_combinations(self, value):
      self._input_combinations = []
      if not isinstance(value, list):
        if not isinstance(value, tuple):
          value = (value,)
        value = [value]
      self._input_combinations.extend(value)
      self.setNextInputCombination()

    def getCurrentInputCombination(self):
      out = []
      for i in range(len(self._input_port_list)):
        out.append(
          getattr(
            self._cell_list[self._input_port_list[i][0]].inputs,
            self._input_port_list[i][1]
          )
        )
      return out

    def setNextInputCombination(self):
      input_combinations = self._input_combinations.pop(0)
      for i in range(len(input_combinations)):
        self[i] = input_combinations[i]

    def __len__(self):
      return len(self._input_port_list)

  def __init__(self):
    self.cellList = dict()
    self.plasm = ecto.Plasm()
    self._inputs_handler = Graph._InputHandler(self.cellList)
    self._params_handler = Graph._ParamIterator(self.cellList)
    self._outputs = []
    self._graph_output_buffer = [] #: contains all computed outputs
    self._graph_result_buffer = [] #: contains all outputs with corresponding inputs and parameters

  @staticmethod
  def createFromDict(graph_description):
    """
    Instanciates a new graph from a dictionnary

    :param graph_description: Dictionnary describing the graph to create
    """
    g=Graph()
    if not graph_description.has_key("cells"):
      raise Exception("No cell was declared. Use 'cells' field to declare cells")
    for cell_description in graph_description["cells"]:
      g.addCell(tools.createEctoCell(**cell_description))
      if cell_description.has_key("params"):
        for param_setting in cell_description["params"]:
          g.setSwitchingParameters(cell_description["name"], **param_setting)

    if graph_description.has_key("inputs"):
      for graph_input_port in graph_description["inputs"]:
        g.setPortAsGraphInput(**graph_input_port)

    if graph_description.has_key("outputs"):
      for graph_output_port in graph_description["outputs"]:
        g.setPortAsGraphOutput(**graph_output_port)

    if graph_description.has_key("connections"):
      for graph_connection in graph_description["connections"]:
        g.connect(
          upstream_cell_name=graph_connection["from"].split(".")[0],
          output_port=graph_connection["from"].split(".")[1],
          downstream_cell_name=graph_connection["to"].split(".")[0],
          input_port=graph_connection["to"].split(".")[1]
        )

    return g

  def addCell(self, cell):
    """
    Adds a cell to the graph

    :param cell: An ecto cell
    """
    self.cellList[cell.name()] = cell

  def connect(self, upstream_cell_name, output_port, downstream_cell_name, input_port):
    """
    Connects ports from two different cells

    :param upstream_cell_name: Name of the upstream cell to connect
    :param output_port: Port of the upstream cell to connect
    :param downstream_cell_name: Name of the downstream cell to connect
    :param input_port: Port of the downstream cell to connect
    """
    self.plasm.connect(
      self.cellList[str(upstream_cell_name)][str(output_port)] >> self.cellList[str(downstream_cell_name)][str(input_port)]
    )

  def run(self):
    """
    Runs the graph with all parameter and input values given
    """
    self._graph_output_buffer = []
    if len(self.plasm.cells())>0:
      self.sched = ecto.CustomSchedulerSBR(self.plasm)
      runner = self.sched.execute
      self._params_handler.initParamIteration(self.sched.getDepthMap())
    elif len(self.cellList)>0:
      _lonely_cell = self.cellList.values()[0]
      runner = (lambda x: [cell.process() for cell in self.cellList.values()])
      self._params_handler.initParamIteration({_lonely_cell.name():0})
    else:
      return
    cells_to_rerun = list()

    while True:
      runner(cells_to_rerun if len(cells_to_rerun)>0 else 1)
      computation_result = dict(
        outputs=[
          self.cellList[self._outputs[i][0]].outputs[self._outputs[i][1]] for i in range(len(self._outputs))
        ],
        inputs=self._inputs_handler.getCurrentInputCombination(),
        params=self._params_handler.getCurrentParamCombination(),
      )
      if len(self._outputs)>1:
        self._graph_output_buffer.append(
          tuple(computation_result["outputs"])
        )
      elif len(self._outputs)==1:
        self._graph_output_buffer.append(
          computation_result["outputs"][0]
        )

      self._graph_result_buffer.append(computation_result)
      try:
        cells_to_rerun = self._params_handler.setNextParamCombination()
      except StopIteration:
        self._params_handler.reset()
        cells_to_rerun = list()
        try:
          self._inputs_handler.setNextInputCombination()
        except IndexError:
          break

  def setPortAsGraphOutput(self, cell_id, port_name, *args, **kwargs):
    """
    Sets an output of the graph

    :param cell_id: Id of the output cell
    :param port_name: Name of the port used as output
    :param args: Other arguments (ignored)
    :param kwargs: Other arguments (ignored)
    """
    self._outputs.append(
      (cell_id, str(port_name))
    )

  def setPortAsGraphInput(self, cell_id, port_name, *args, **kwargs):
    """
    Sets an input of the graph

    :param cell_id: Id of the input cell
    :param port_name: Name of the port used as input
    :param args: Other arguments (ignored)
    :param kwargs: Other arguments (ignored)
    """
    self._inputs_handler.addInput(
      cell_id,
      str(port_name)
    )

  def getGraphInputs(self):
    """
    Returns the list of all ports which are inputs of the graph
    """
    return self._inputs_handler._input_port_list

  def clearGraphInputs(self):
    """
    Reset input ports to an empty list
    """
    self._inputs_handler = Graph._InputHandler(self.cellList)

  def setSwitchingParameters(self, cell_id, param_name, values):
    """
    Set different possible values for a parameter

    :param cell_id: Name of the cell whose parameter is variable
    :param param_name: Name of the variable parameter
    :param values: List of values the parameter can take
    """
    self._params_handler.setParameterPossibleValues(
      cell_id,
      param_name,
      values
    )

  @write_only_property
  def input(self, value):
    """
    An alternative way to set graph input values when there is only one input
    port.
    """
    if len(self._inputs_handler) != 1:
      raise IndexError(
        "`input` can only be used if exactly 1 input port is defined"
      )
    if isinstance(value, list):
      self.inputs = [(i,) for i in value]
    else:
      self.inputs[0] = value

  @property
  def inputs(self):
    return self._inputs_handler

  @inputs.setter
  def inputs(self, values):
    if len(self._inputs_handler) == 0:
      raise IndexError("No input was set for graph")
    self._inputs_handler.input_combinations = values

  @property
  def output(self):
    if len(self._outputs) == 0:
      raise Exception("No output was set for graph")
    if len(self._graph_output_buffer)==0:
      return None
    if len(self._graph_output_buffer)==1:
      return self._graph_output_buffer[0]
    return self._graph_output_buffer

  @property
  def result(self):
    return self._graph_result_buffer

  def size(self):
    return len(self.cellList)
