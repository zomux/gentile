"""
Cube Pruner , you knows
"""
import heapq
from abraham.treestruct import DepTreeStruct
from abraham.ruletable import NovelDepStrRuleTable
from abraham.model import NovelDepStrModel
from abraham.hypothesis import NovelDepStrHypothesis

from abraham.logger import log_error,log

class CubePruner:
  """
  Just a typical cube pruner
  """
  def __init__(self,model,fragment,stack_rules,stack_hyps,size):
    """

    """
    pass
  
class AllInOneCubePruner:
  """
  Class for running cube pruning for dep-to-str models
  prune all hypothesises in one cube

  """
  # [ (rule,cost) , ... ]
  stackRules = None
  # [ [hyp,...], ...]
  stacksHyps = None
  size = None
  fragment = None
  # position [idx,...]
  # first dimension should be rules
  bestPosition = None
  # [(score,pasted position),...]
  heapEdges = None
  # [(pasted position,hyp),...]
  mapPositionHyp = None
  dimensionSize = 0
  needStop = False
  # expanded positions
  positionExpanded = None
  model = None
  def __init__(self,model,fragment,stack_rules,stacks_hyps,size):
    """
    Initial the cube pruner
    @type fragment: (number,DepStrTreeStruct)
    @type stack_rules: list of (string,float)
    @type stack_hyps: list of list of NovelDepStrHypothesis
    @type size: number
    """
    self.model = model
    self.stackRules = stack_rules
    self.stacksHyps = stacks_hyps
    self.size = size
    self.fragment = fragment
    self.dimensionSize = len(stacks_hyps) + 1
    self.bestPosition=[0]*self.dimensionSize
    self.heapEdges = []
    self.mapPositionHyp = {}
    self.positionExpanded = []
    self.lastBestScore = None
    # reorder basic hypothesis stacks by order in sentence( head word id )
    self.stacksHyps.sort(key=lambda l:l[0].headWordId)

  def getHypothesisByPosition(self,position):
    """
    Get Hypothesis by given position of cube
    @type position: list of number
    @rtype: NovelDepStrHypothesis
    """
    stack_basic_hyps = []
    rule = None
    for i,n in enumerate(position):
      if i==0:
        # rule dimension
        rule = self.stackRules[n]
      else:
        # hyp dimension
        stack_basic_hyps.append(self.stacksHyps[i-1][n])
    return NovelDepStrHypothesis(self.model,self.fragment,rule,stack_basic_hyps)

  def pastePosition(self,position):
    """
    return a fully number of a list of positions
    @type position: list of int
    @rtype: string
    """
    return ','.join('%d' % num for num in position)
  
  def unpastePosition(self,pastedpos):
    """
    return a fully number of a list of positions
    @type pastedpos: string
    @rtype: list of int
    """
    ret = [int(i) for i in pastedpos.split(",")]
    return ret
  def expandEdges(self):
    """
    expand edge lattices of cube
    save new hypothesises to self.heapEdges
    -------------
    Expand could be done by add each dimension by 1 , of course , if it can be
    """

    # first get all positions to expand
    # [pos,...]
    newedges = []
    for idx_dimension in range(self.dimensionSize):
      cur_index = self.bestPosition[idx_dimension]
      if idx_dimension == 0:
        # rule dimension
        if cur_index+1 < len(self.stackRules):
          newedge = self.bestPosition[:]
          newedge[0] = cur_index+1
          newedges.append( newedge )
      else:
        # hyp dimensions
        if cur_index+1 < len(self.stacksHyps[idx_dimension-1]):
          newedge = self.bestPosition[:]
          newedge[idx_dimension] = cur_index+1
          newedges.append( newedge )
    # for each new edge lattice , build hypothesis
    for position in newedges:
      pastedpos = self.pastePosition(position)
      if pastedpos in self.positionExpanded : continue
      #print position
      hyp = self.getHypothesisByPosition(position)
      if hyp.failed:
        log_error("[AllInOneCubePruner] failed to build a hyp.")
      else:
        # !!! to prevent one direction expanding
        if hyp.getScore() == self.lastBestScore : continue
        self.mapPositionHyp[pastedpos] = hyp
        self.heapEdges.append( (0-hyp.getScore(),pastedpos) )
        self.positionExpanded.append(pastedpos)
    if len(self.heapEdges) == 0:
      # no new hyp could be found
      self.needStop = True
      
  def popBestHypothesis(self):
    """
    pop the best hypothesis from self.heapEdges and return it
    @rtype: NovelDepStrHypothesis
    """
    heapq.heapify(self.heapEdges)
    score,pastedpos_of_best = heapq.heappop(self.heapEdges)
    self.bestPosition = self.unpastePosition(pastedpos_of_best)
    return self.mapPositionHyp[pastedpos_of_best]

  def prune(self):
    """
    Function actually do the pruning process
    return a sorted hypothesis list of this fragment
    @rtype: list of NovelDepStrHypothesis
    """
    hypBest = self.getHypothesisByPosition(self.bestPosition)
    if hypBest.failed:
      log_error("[AllInOneCubePruner] failed to build 0,0,0 hyp !!!")
      stack_output = []
      self.lastBestScore = 0
    else:
      stack_output = [hypBest]
      self.lastBestScore = hypBest.getScore()

    while len(stack_output) < self.size:
      # expand currently best lattice
      self.expandEdges()

      if self.needStop : break

      # pop the best hyp of edges to output
      hypBest = self.popBestHypothesis()
      self.lastBestScore = hypBest.getScore()
      stack_output.append( hypBest )

    stack_output.sort( key=lambda x:x.getScore() , reverse=True )
    return stack_output