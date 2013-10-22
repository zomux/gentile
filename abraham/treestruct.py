"""
class of normal tree structure
child class of TreeStruct need to implement
- load(sent)
- getMaxLevel() => max level
- getNodesByLevel( level ) => [nodeid,...]
- getNodeById( id ) => [nodeid,]
- getAllNodes() => {id:{node},...}
- getChildNodes( id ) => [nodeid,]
- getParentNode( id ) => id
"""
import os,sys,re

from setting import setting

class TreeStruct:
  """
  A virtual class for present the normal tree structure
  """
  def parse(self,sent):
    return None
  def getMaxLevel(self):
    return None
  def getNodesByLevel(self,level):
    return None
  def getNodeById(self,id):
    return None
  def getAllNodes(self):
    return None
  def getChildNodes(self,id):
    return None
  def getParentNode(self,id):
    return None

class DepTreeStruct(TreeStruct):
  """
  present dependency tree struct
  """
 
  def __init__(self,data_tag,data_dep):
    """
    Build tree structure from data
    @type data_tag: string
    @type data_dep: string
    """
    # id -> (word,tag)
    self.nodes = {}
    # id -> id
    self.mapParent = {}
    self.mapModifier = {}
    # id -> [ id, ]
    self.mapChilds = {}
    # level -> [node,]
    self.mapLevels = {}
    # number of max level
    self.maxLevel = -1
    self.headNodeId = 0

    self.nodes[0] = ('ROOT','ROOT')
    # build nodes
    xastag = setting.x_as_tag
    for i,pair in enumerate(data_tag.split(" ")):
      if not pair:
        self.nodes[i+1] = ("","")
        continue
      word,tag = pair.rsplit("/",1)
      self.nodes[i+1] = (word,tag) if not xastag else (word,"X")
    # set default values for parent and childs map
    for id in self.nodes:
      self.mapParent[id] = -1
      self.mapChilds[id] = []
    # build parent and childs map
    list_deps = re.findall(r"(.+?)\(.+\-(\d+?), .+\-(\d+?)\)",data_dep)
    for pair in list_deps:
      modifier, iParent,iChild = pair
      iParent = int(iParent)
      iChild = int(iChild)
      self.mapModifier[iChild] = modifier
      self.mapParent[iChild] = iParent
      self.mapChilds[iParent].append(iChild)
      if iParent == 0 : self.headNodeId = iChild
    
    # build level map recursively
    # start with the root node with id 0 and level 0
    self.appendToLevel(0,0)

  def appendToLevel(self,id,level):
    """
    append id recursively to level map
    @type level: number
    """
    if level > self.maxLevel:
      self.mapLevels[level] = []
      self.maxLevel = level
    self.mapLevels[level].append(id)
    for iChild in self.mapChilds[id]:
      self.appendToLevel(iChild,level+1)
  def getMaxLevel(self):
    """
    @rtype: number
    """
    return self.maxLevel
  def getNodesByLevel(self,level):
    """
    Get all nodes of a level
    @type level: number
    @return: a list of node id
    @rtype: list of number
    """
    return self.mapLevels[level]
  def getNodeById(self,id):
    """
    Get node in format of (word,tag) by id
    @type id: number
    @return: node , if not found , then None
    @rtype: (string,string)
    """
    return id in self.nodes and self.nodes[id] or None
  def getWordById(self,id):
    """
    Get word in node id
    @type id: number
    @return: word
    @rtype: string
    """
    return id in self.nodes and self.nodes[id][0] or None
  def getAllNodes(self):
    """
    @return: all nodes
    @rtype: object
    """
    return self.nodes
  def getChildNodes(self,id):
    """
    @type id:number
    @return: child nodes of id
    @rtype: list of (string,string)
    """
    return self.mapChilds[id]
  def getParentNode(self,id):
    """
    @type id:number
    @return: parent node of id
    @rtype: number
    """
    return self.mapParent[id] if id in self.mapParent else -1
  def hasNode(self,id):
    """
    tell if a id in this tree
    @type id: number
    @rtype : bool
    """
    return id in self.nodes
  def getWords(self):
    """
    return all tokens , ok or just words for this sentence in a list
    @rtype: list of string
    """
    return [node[0] for node in self.nodes.values()]
  def isLeafNode(self,id):
    """
    determine if node with id is a leaf node
    @type id:number
    @rtype: bool
    """
    return len(self.mapChilds[id])==0
