"""
Decoder class
the overall translation task is completed in the class

the translation process is detailed as following.
first , we build lexical translation hypothesis list for each node
then , for all nodes but beside leaf nodes in bottom-up style order
we use cube pruning to produce translation hypothesis lists
then the translation hypothesis list of the root node is N-best results
In cube pruning,
rules corresponding to this head-dependent fragment and hypothesis list for each X
( lexical hypothesis for leaf nodes and head nodes, and normal hypothesis for internal nodes )
is put together to perform a bug-crawl style cube pruning

so , if a fragment has  n nodes , the dimension of cube pruning should be n+1

a rule dimension and hypothesises for each node
(lexical for leaf and head , normal for internal nodes)


praise the lord ! voice of Libera !

- Raphael Shu  2012,2
"""

import os,sys
from abraham.treestruct import DepTreeStruct
from abraham.setting import setting
from gentile.ruletable import GentileRuleTable
from gentile.rulefetcher import GentileRuleFetcher
from gentile.hypothesis import GentileHypothesis
from gentile.model import GentileModel
from gentile.cubepruner import GentileCubePruner, separately_prune
from gentile.reconstructor import Reconstructor
from gentile.sense import SenseTree

import __builtin__

from abraham.logger import log_error,log

class GentileDecoder:
  """
  Class that actually do the translation job.
  present the translation model described in Gentile Model.
  """
  ruletable = None
  model = None
  """@type: GentileModel"""
  lexicalTable = None
  
  def __init__(self):
    """
    Load rule table and language model once !!!
    """
    self.ruletable = GentileRuleTable()
    self.model = GentileModel()

  def translate(self,data_tree,data_dep):
    """
    translate the data in format of stanford parser (tag,basicDependency)
    @type data_tag: string
    @type data_dep: string
    @rtype: string
    """
    return self.translateNBest(data_tree,data_dep)[0].getTranslation()

  def prepareRulesForTranslation(self,tree):
    """
    Decide joint node for pruning, and fetch rules
    for each joint node.

    @type tree: SenseTree
    @rtype: GentileRuleFetcher
    """
    fetcher = GentileRuleFetcher(tree, self.ruletable, self.model)
    fetcher.fetch()
    return fetcher

  def buildLexicalStack(self,fetcher):
    """
    For each joint nodes, create lexical hypothesises for it
    iff lexical rules for these nodes exist.

    @type fetcher: GentileRuleFetcher
    """
    stack_lex = {}
    for node in fetcher.joints:
      lexrules = fetcher.mapJointRules[node][1]
      if lexrules:
        # create hypothesises using these lexical rules
        hyps = [GentileHypothesis(self.model,lexrule,{}) for lexrule in lexrules]
        hyps = self.model.sortHypothesises(hyps)
        stack_lex[node] = hyps
    return stack_lex

  def traceFirstTokenId(self, sense, nodeId):
    """
    Trace first node id in the source span.
    """
    while True:
      node = sense.tree.nodes[nodeId]
      if node[0] > 0:
        return node[0]
      else:
        nodeId = -node[0]

  def traceLastTokenId(self, sense, nodeId):
    """
    Trace last node id in the source span.
    """
    while True:
      node = sense.tree.nodes[nodeId]
      if node[-1] > 0:
        return node[-1]
      else:
        nodeId = -node[-1]

  
  def translateNBest(self,data_tree,data_dep):
    """
    Translate and return a N-best list
    @type data_tag: string
    @type data_dep: string
    @rtype: list of GentileHypothesis
    """
    # first, we need get the tree of input
    self.model.cacheMode = False
    setting.load(["nbest"])
    tree = SenseTree(data_tree,data_dep)
    tree.rebuildTopNode()
    tree.appendXToTree()
    tree.upMergeAllConjNodes()
    tree.rebuildCommaNodes()
    tree.forceUsingDepCrystals()
    tree.convertTags()
    tree.separateContiniousNonTerminals()
    # tree.mergeContinuousNTs()
    fetcher = self.prepareRulesForTranslation(tree)
    # build lexical hypothesis stack
    # { id->[lexical hyp,] }
    # stack_lex = self.buildLexicalStack(fetcher)
    # { id->[lexical hyp,] }
    hypStacks = {}
    # for each fragment ( head node is not leaf ) at bottom-up style
    # use corresponding rules and basic hypothesis(lex or normal) to build normal hyp for this fragment
    tree.buildLevelMap()
    cur_level = tree.getMaxLevel()
    # A dirty trick: save current sense tree to cross-module global variable.
    __builtin__.currentSenseTree = tree
    # start pruning
    self.model.cacheMode = True
    while cur_level > 0:
      # [head id,]
      nodes_cur_level = tree.getNodesByLevel(cur_level)
      for node in nodes_cur_level:
        # Set smode for model
        self.model.smode = 0
        if self.traceFirstTokenId(tree, node) == 1:
          self.model.smode += 1
        if self.traceLastTokenId(tree, node) == len(tree.tokens):
          self.model.smode += 2
        print node, "-smode-", self.model.smode

        if node not in fetcher.joints:
          # only prune for joint nodes
          continue
        # get rules
        rules, sitesInvolved = fetcher.mapJointRules[node]
        # okay available could in random order
        # we dont need sort it
        if not rules:
          # No rules found, force to use CYK.
          rc = Reconstructor(self.ruletable, self.model,
                             tree, hypStacks, node)
          hyps = rc.parse()
        else:
          # Rules found then cube prunning.
          # sort rules
          rules = self.model.sortRules(rules)
          # now run the cube pruning and get normal hypothesises for current node
          hyps = separately_prune(self.model, node, rules, sitesInvolved, hypStacks)
        hypStacks[node] = hyps
        self.model.clearCache()
      # end of current node
      cur_level -= 1

    rootNode = tree.getRootNode()
    if rootNode not in hypStacks or len(hypStacks[rootNode])==0:
      # failed
      print "[GentileDecoder]","Translation Failed!!!"
      return []

    # end building normal hypothesis stack
    # hypStacks[rootNode][0].trace()

    return hypStacks[rootNode][:setting.nbest]
