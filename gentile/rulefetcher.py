# coding: utf-8
"""
Fetch rules for a tree in Gentile.

For illustration, if a token list "o x o" exists.
"x" stands for non-terminal tokens, and "o" stands
for terminal tokens.

• Exactly Matching
  The source side of rule exactly matches the tokens list of the node,
  "o x o"

• Merged Matching
  Try to merge N levels of child nodes into the token list of this node,
  get "o o o", then use it as source side to search for rules.

• Reconstruct Matching(old method)
  If all above methods are failed, then try reconstruct matching,
  just build a new subtree for this node, to get chance of match a rule.
  Then this could be "o x o" --> "x x o" or "o x o" or "x x x".

• Reconstruct Matching(new method)
  CKY

• Depraved Matching
  If and only if all above methods are failed.
  Move all terminal tokens to separate child nodes and
  construct a pseudo rule "[tag-of-o] x [tag-of-o]" -> "x x x".

"""
import os,sys
from gentile.ruletable import GentileRuleTable
from abraham.setting import setting
from gentile.reconstructor import Reconstructor
import math
import itertools


class GentileRuleFetcher:
  """
  Detemine pruning nodes of given tree
  Fetch all rules for each fragment derived by
  pruning nodes
  """
  sense = None
  tree = None

  ruletable = None
  model = None

  joints = None
  mapJointRules = None

  mapNodeDependentSites = {}

  def __init__(self, sense, ruletable, model):
    """
    Save the environment.

    @param sense: Sense Tree
    @type sense: SenseTree
    @param ruletable: ruletable object
    @type ruletable: GentileRuleTable
    """
    self.sense = sense
    self.tree = sense.tree
    self.ruletable = ruletable
    self.model = model
    self.joints = []
    self.mapJointRules = {}

  def initJoints(self):
    """
    In Gentile, all nodes are joint.
    """
    self.joints = list(self.tree.nodes)

  def convertTokensToSourceString(self, tokens):
    """
    Convert given token list to source side string of a rule.
    @param tokens: a list of tokens that corresponding to token ids saved in sense tree,
                   and -nodeId stands for a site linked to a child node
    """
    sense = self.sense
    return " ".join([sense.tokens[t-1][1]
                     if t > 0 else "[%s]" % sense.tokens[sense.mapNodeToMainToken[-t]-1][0]
                     for t in tokens])

  def getTagOfNode(self, nodeId):
    """
    Get tag(context) of given node's main token.
    """
    return self.sense.tokens[self.sense.mapNodeToMainToken[nodeId]-1][0]

  def recordDependentSitesForNode(self, nodeId, sites):
    """
    Record Dependent sites.
    """
    self.mapNodeDependentSites.setdefault(nodeId, set([])).update(sites)

  def findExactlyMatchingRules(self, nodeId):
    """
    Find exactly matching rules for given node.
    """
    tokens = self.tree.node(nodeId)
    sourceString = self.convertTokensToSourceString(tokens)
    sites = [-id for id in tokens if id < 0]
    tag = self.getTagOfNode(nodeId)
    rulesFound = self.ruletable.findBySource(sourceString, sites, tag)
    if rulesFound:
      self.recordDependentSitesForNode(nodeId, sites)
    return rulesFound

  def findMergedMatchingRules(self, nodeId):
    """
    Find rules by merged matching.
    """
    # if nodeId == self.tree.root and self.tree.nodes[nodeId][-1]>0 and self.sense.tokens[self.tree.nodes[nodeId][-1]-1][1] == ".":
    #   return []

    rules = []
    maxMergeNodes = setting.max_merge_nodes
    tokens = self.tree.node(nodeId)
    sites = [-id for id in tokens if id < 0]
    tag = self.getTagOfNode(nodeId)
    if not sites:
      return []
    for mergeNodes in range(1, maxMergeNodes+1):
      if mergeNodes > len(sites):
        break
      for sitesSelected in itertools.combinations(sites, mergeNodes):
        # Merge all child nodes.
        newTokens = tokens
        for linkedNodeId in sitesSelected:
          linkedTokens = self.tree.node(linkedNodeId)
          pos = newTokens.index(-linkedNodeId)
          newTokens = newTokens[:pos] + linkedTokens + newTokens[pos+1:]
        newSites = [-id for id in newTokens if id < 0]
        sourceString = self.convertTokensToSourceString(newTokens)
        rulesFound = self.ruletable.findBySource(sourceString, newSites, tag)
        if rulesFound:
          self.recordDependentSitesForNode(nodeId, newSites)
        rules.extend(rulesFound)

    return rules

  def findRecontructMatchingRulesOldMethod(self, nodeId):
    """
    !!! Deprecated
    Try to reconstruct tree and find rules for this node.
    (Old method used)
    This should be extra careful, cause the tree structure would be changed
    if such operations are done.
    So the important thing there is to maintain the tree structure and related maps,
    then tell the main loop there are some new nodes appended.

    Mechanism, given a token list "o o x o"
    1. Find all combinations
       Record all terminal position,
       and cumulatively generate combinations of this terminal token to
       be replaced by non-terminal tokens.
       replaced token id starts from -1000.
    3. For each level of map, try to find rules for all those tokens.
    4. Stop at the level if any rules found,
       then create child nodes for those replaced tokens, normalize rules.
    5. Fix the tree!
    """
    tokens = self.tree.node(nodeId)
    assert len(tokens) > 0
    if len(tokens) == 1:
      return []
    nodeTag = self.getTagOfNode(nodeId)
    terminalPositions = [n for n in range(len(tokens)) if tokens[n] > 0]
    rules = []
    mapPositionToNewNode = {}

    for replacedCount in range(1, len(terminalPositions) + 1):
      replacedCombinations = itertools.combinations(terminalPositions, replacedCount)
      for replacedPositions in replacedCombinations:
        sourceWords = []
        for idx in range(len(tokens)):
          token = tokens[idx]
          if idx in replacedPositions:
            sourceWords.append("[%s]" % self.sense.tokens[token-1][0])
          elif tokens[idx] < 0:
            sourceWords.append("[%s]" % self.getTagOfNode(-tokens[idx]))
          else:
            sourceWords.append(self.sense.tokens[token-1][1])
        sourceString = " ".join(sourceWords)
        rulesFound = self.ruletable.findBySource(sourceString, None, nodeTag)
        if not rulesFound:
          continue
        # Create new nodes for terminal tokens.
        for pos in replacedPositions:
          if pos in mapPositionToNewNode:
            continue
          tokenId = tokens[pos]
          newNodeId = max(self.tree.nodes) + 1
          mapPositionToNewNode[pos] = newNodeId
          self.tree.nodes[newNodeId] = [tokenId]
          self.tree.mapParent[newNodeId] = nodeId
          self.tree.mapChildren.setdefault(nodeId, []).append(newNodeId)
          self.sense.mapNodeToMainToken[newNodeId] = tokenId
        # Build sites for these rules
        sites = []
        for pos in range(len(tokens)):
          if pos in mapPositionToNewNode:
            sites.append(mapPositionToNewNode[pos])
          elif tokens[pos] < 0:
            sites.append(-tokens[pos])
        rulesFound = self.ruletable.setSitesForRules(rulesFound, sites)
        self.recordDependentSitesForNode(nodeId, sites)
        rules.extend(rulesFound)
      if rules:
        break
    return rules

  def findRecontructMatchingRules(self, nodeId):
    """
    Use modified CKY to just build rules for node.
    """
    tokens = self.tree.node(nodeId)
    assert len(tokens) > 0
    if len(tokens) == 1:
      return []
    nodeTag = self.getTagOfNode(nodeId)
    rc = Reconstructor(self.ruletable, self.model,
                       self.sense, tokens, nodeTag)
    rules = rc.parse()
    if rules:
      self.recordDependentSitesForNode(nodeId,[-t for t in tokens if t < 0])
    return rules

  def findDepravedMatchingRules(self, nodeId):
    """
    As the last chance we have, just build a pseudo rule,
    in a dirty way then break all tokens of this node to child nodes.
    Those nodes will surely be translated by lexical rules.
    But if given node is already a lexical node, then we need give a
    pseudo lexical translation rule.
    """
    tokens = list(self.tree.node(nodeId))
    assert len(tokens) > 0
    # Build lexical pseudo rule.
    if len(tokens) == 1:
      target = self.sense.tokens[tokens[0]-1][1]
      pseudoRule = self.ruletable.buildPsuedoRule(target, [])
      return [pseudoRule]
    # Build normal pseudo rule.
    terminalPositions = [n for n in range(len(tokens)) if tokens[n] > 0]
    rules = []
    mapPositionToNewNode = {}

    # Create new nodes for terminal tokens.
    for pos in terminalPositions:
      tokenId = tokens[pos]
      newNodeId = max(self.tree.nodes) + 1
      mapPositionToNewNode[pos] = newNodeId
      self.tree.nodes[newNodeId] = [tokenId]
      self.tree.mapParent[newNodeId] = nodeId
      self.tree.mapChildren.setdefault(nodeId, []).append(newNodeId)
      self.sense.mapNodeToMainToken[newNodeId] = tokenId
      self.tree.nodes[nodeId][pos] = -newNodeId
    # Build sites for these rules
    sites = []
    for pos in range(len(tokens)):
      if pos in mapPositionToNewNode:
        sites.append(mapPositionToNewNode[pos])
      elif tokens[pos] < 0:
        sites.append(-tokens[pos])
    # Get pseudo rule.
    pseudoRule = self.ruletable.buildPsuedoRule(None, sites)
    self.recordDependentSitesForNode(nodeId, sites)
    return [pseudoRule]

  def fetchRulesForNode(self, nodeId):
    """
    Fetch rules for given node in tree.
    """
    rules = []
    self.mapNodeDependentSites[nodeId] = set([])
    # exactlyMatched = self.findExactlyMatchingRules(nodeId)
    # rules.extend(exactlyMatched)
    mergedMatched = self.findMergedMatchingRules(nodeId)
    rules.extend(mergedMatched)
    if len(self.tree.node(nodeId)) > 12:
      rules.extend(self.findDepravedMatchingRules(nodeId))
    # HACK: 2012/10/22
    # elif not mergedMatched and exactlyMatched and len(exactlyMatched) <= 1:
    #   if exactlyMatched[0][2][2] < -3: # log(0.05)
    #     # Clear rules in this bad situtation.
    #     rules = []

    # Allow no rules to return, then the decoder will be forced to
    # build translation using CYK.
    if not rules:
      return None, {}
    # if not rules:
    #   rules.extend(self.findRecontructMatchingRules(nodeId))
    # if not rules:
    #   rules.extend(self.findDepravedMatchingRules(nodeId))
    # # Should rule got here!.
    # assert rules

    return rules, self.mapNodeDependentSites[nodeId]

  def fetch(self):
    """
    Fetch rules for given tree.
    """
    self.initJoints()
    # TODO: change to stack-loop style
    for joint in self.joints:
      rules, sitesFound = self.fetchRulesForNode(joint)
      # save to mapJointRules
      for site in sitesFound:
        if site not in self.joints:
          self.joints.append(site)
      # Save found sites to sorted list.
      self.mapJointRules[joint] = (rules, sorted(sitesFound))


############### FORBBBBBIDEN TEST AREA ################
def test():
  """
  Starry Night - Van Gogh.
  """
  def showRules(rules):
    for r in rules:
      t,s,c = r
      print t,"|",s,c
    return ""
  ruletable = GentileRuleTable()
  from testdata.testtree import testtree
  testtree.appendXToTree()
  fetcher = GentileRuleFetcher(testtree, ruletable)
  print "--- convertTokenToSourceString ---"
  source14 = fetcher.convertTokensToSourceString(testtree.tree.node(14))
  source7 = fetcher.convertTokensToSourceString(testtree.tree.node(7))
  print 14, source14
  print 7, source7
  fetcher.initJoints()
  print "--- findExactlyMatchingRules ---"
  print 14, showRules(fetcher.findExactlyMatchingRules(14))
  print 7, showRules(fetcher.findExactlyMatchingRules(7))
  print "--- findMergedMatchingRules ---"
  print 14, showRules(fetcher.findMergedMatchingRules(14))
  print 7, showRules(fetcher.findMergedMatchingRules(7))
  print 1, showRules(fetcher.findMergedMatchingRules(1))
  print "--- findRecontructMatchingRules ---"
  print 14, showRules(fetcher.findRecontructMatchingRules(23))
  print "--- findDepravedMatchingRules ---"
  print 23, showRules(fetcher.findDepravedMatchingRules(23))
  print 7, showRules(fetcher.findDepravedMatchingRules(7))
  print 27, showRules(fetcher.findDepravedMatchingRules(27))
if __name__ == '__main__':
  test()
