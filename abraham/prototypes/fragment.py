from abraham.treestruct import DepTreeStruct

class Fragment:
  """
  Class for present a tree fragment

  """
  tree = None
  """@type: DepTreeStruct"""
  headNodeId = None
  nodes = None
  listInterNodes = None
  """@type: list of number"""
  listLeafNodes = None
  """@type: list of number"""
  listInterLeafBuilt = False

  # external informations
  expandedNodes = None


  def __init__(self,tree,head,nodes):
    """
    @type tree: DepTreeStruct
    @param head: head node id
    @type head: number
    @param nodes: list of node id
    @type nodes: list of number
    """
    self.tree = tree

    self.headNodeId = head
    self.nodes = nodes

  def printStruct(self):
    """
    print out this tree struct
    """
    stack_to_print = [(self.headNodeId,0)]
    while len(stack_to_print):
      nodeid,level = stack_to_print.pop()
      print "   "*level+"|--"+"/".join(self.tree.getNodeById(nodeid))
      for childid in self.tree.getChildNodes(nodeid):
        if childid in self.nodes:
          stack_to_print.append((childid,level+1))
    print ""

  def headNode(self):
    """
    ( HEAD )
    """
    return self.headNodeId

  def buildInterLeafNodes(self):
    """
    Build list of inter and leaf nodes for after use
    """
    self.listInterLeafBuilt = True
    self.listInterNodes = []
    self.listLeafNodes = []
    for node in self.nodes:
      parent = self.tree.getParentNode(node)
      if parent in self.nodes and parent not in self.listInterNodes:
        self.listInterNodes.append(parent)
    self.listLeafNodes = list(set(self.nodes)-set(self.listInterNodes))

  def interNodes(self):
    """
    ( INTER )
    """
    if not self.listInterLeafBuilt:
      self.buildInterLeafNodes()
    return self.listInterNodes

  def leafNodes(self):
    """
    ( LEAF )
    """
    if not self.listInterLeafBuilt:
      self.buildInterLeafNodes()
    return self.listLeafNodes







