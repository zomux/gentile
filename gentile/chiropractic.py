"""
Chiropractic Decoder

If you are involved in some bad stuffs,

you will find the world is so cold,

that will not let you have some good motion to feel you self be any.

huh, good that would be all the same, the world is just it ought to be.

Remember this, do not do the foolish thing again,

do things your self in your own world.

To say something, this chiropractic decoder is a forest decoder for hierarchical phrase trees.
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

class ChiropracticDecoder:
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
    #self.ruletable = GentileRuleTable()
    #self.model = GentileModel()

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
  
  def translateNBestOLD(self,data_tree,data_dep):
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
      if cur_level == 1:
        self.model.smode = True
      else:
        self.model.smode = False
      for node in nodes_cur_level:
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

  def translateNBest(self, data_tree, data_dep):
    """
    Translate in forest
    @param data_tree:
    @param data_dep:
    @return:
    """
    # Get pare tree.
    #self.model.cacheMode = False
    setting.load(["nbest"])
    tree = SenseTree(data_tree,data_dep)
    tree.rebuildTopNode()
    tree.appendXToTree()
    tree.upMergeAllConjNodes()
    tree.rebuildCommaNodes()
    tree.convertTags()
    tree.separateContiniousNonTerminals()
    # Prepare for chiropractic process.
    treeForest = [tree]
    resultStack = []
    for tree in treeForest:
      resultStack.append(self.chiropracticTranslation(tree))

  def buildPhraseBorders(self, sense):
    """
    Build a map saving borders for each phrase, each phrase is identified by its ID
    @type sense: SenseTree
    @return: map node id - > (leftBorder, rightBorder)
    """
    borders = {}
    for node in sense.tree.nodes:
      nodeTokens = sense.tree.nodes[node]
      terminals = [t for t in nodeTokens if t > 0]
      borders[node] = (min(terminals), max(terminals))
    return borders

  def buildPhraseDependencies(self, sense, borders):
    """
    Generate phrase dependencies for a given parse tree.
    These special phrase dependencies are yield by a internal X in a phrase.

    @param tree: parse tree
    @type tree: SenseTree
    @return: map node id -> [ area, ... ]
    """
    phraseDependencies = {}
    for node, nodeTokens in sense.tree.nodes.items():
      firstTerminal, lastTerminal = borders[node]
      firstTerminalPos, lastTerminalPos = nodeTokens.index(firstTerminal), nodeTokens.index(lastTerminal)
      tokensFilledWithTerminals = nodeTokens[firstTerminalPos : lastTerminalPos+1]
      internalNonTerminals = [t for t in tokensFilledWithTerminals if t < 0]
      if internalNonTerminals:
        phraseDependencies[node] = []
        for nonTerminal in internalNonTerminals:
          pos = nodeTokens.index(nonTerminal)
          previousTerminal = nodeTokens[pos - 1]
          nextTerminal = nodeTokens[pos + 1]
          area = (previousTerminal + 1, nextTerminal - 1)
          phraseDependencies[node].append(area)
    return phraseDependencies

  def buildPhraseDerivations(self, borders, dependencies):
    """
    Build a map indicates phrase derivation relationships.
    For each phrase, it generates all derivations (may be derivation of derivation).

    @param sense:
    @param borders:
    @param dependencies:
    @return: [ (phrase, derivation), ... ]
    """
    phraseDerivations = []
    for node, dependentAreas in dependencies.items():
      for area in dependentAreas:
        leftAreaBorder, rightAreaBorder = area
        for childNode, childNodeBorder in borders.items():
          leftBorder, rightBorder = childNodeBorder
          if leftBorder >= leftAreaBorder and rightBorder <= rightAreaBorder:
            phraseDerivations.append((childNode, node))
    return phraseDerivations

  def chiropracticTranslation(self, sense):
    """
    Do chiropractic translation for a given phrase combination
    @param sense:
    @return:
    """
    phraseBorders = self.buildPhraseBorders(sense)
    phraseDependencies = self.buildPhraseDependencies(sense, phraseBorders)
    phraseDerivations = self.buildPhraseDerivations(sense, phraseBorders, phraseDependencies)
    # For each area from short to long do forest decoding
    areas = set()
    map(areas.update, phraseDependencies.values())
    fullArea = (1, len(sense.tokens))
    areas.add(fullArea)
    # Sort areas by length
    # area's border begins with 1
    areas = list(areas)
    areas.sort(key = lambda x : x[1] - x[0])
    hypStacks = {}
    maxTokenId = len(sense.tokens)
    for area in areas:
      self.disableInpossibleCells(hypStacks, area, maxTokenId)
      self.buildHypothesisesForArea(hypStacks, area, phraseDerivations)

  def disableInpossibleCells(self, hypStacks, area, maxTokenId):
    """
    As the area is going to be decoded separately, any upper cell includes only part of this area
    should be disabled.
    -----------            -----------
    | | | | | |            | |x|x| | |
    -----------            -----------
      |o|o|o| |              |o|o|o| |
      ---------    =>        ---------
        |o|o| |                |o|o|x|
        -------                -------
          |o| |                  |o|x|
          -----                  -----
            | |                    | |
            ---                    ---
    @param hypStack:
    @param area:
    @return:
    """
    leftBorder, rightBorder = area
    # If length is 1, do nothing
    if leftBorder == rightBorder:
      return
    for right in range(leftBorder, rightBorder):
      for left in range(1, leftBorder):
        hypStacks[(left, right)] = []
    for left in range(leftBorder + 1, rightBorder + 1):
      for right in range(rightBorder + 1, maxTokenId + 1):
        hypStacks[(left, right)] = []

  def enumerateBasePhrasesForArea(self, area, phraseBorders, phraseDerivations):
    """

    @param area:
    @param phraseBorders:
    @param phraseDerivations:
    @return:
    """

  def buildHypothesisesForArea(self, hypStacks, area, phraseBorders, phraseDerivations):
    """
    Build Hypothesis stacks in given area.

    @param hypStacks: hypothesis stack
    @param area: (low token id, high token id)
    @param phraseBorders: map node -> (left border, right border)
    @param phraseDerivations: list (child node, yielded node)
    @return: None
    """







