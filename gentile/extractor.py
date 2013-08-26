# coding: utf-8
"""
Gentile Sense-to-string Model.

Rule extractor.

Plan of extraction for Gentile
• Initial phrase extraction
  Follow the fashion in hiero, if no noise involved in alignment for a phrase pair, then extract them as initial phrase pairs.
  1. No word in source side aligned to other words in target.
  2. No word in target side aligned by other words in source.
  3. At least one word pair in source and target side are aligned.
  For each *leaf* node in the tree, build source side words and target spans, and do extraction.

• Hierarchical rule extraction
  Rule extraction for Gentile also follows the fashion of Hiero,
  Basically, if an initial phrase covers another initial phrase, then replace the child phrase with non-terminal.
  This will generate a large quantities of rules, so just also accept the constrains of that in Hiero:
  1. No expanding in target side.
  2. At least one aligned word pair involved.
  In practice, just look for each node, and if all child nodes of this node are initial phrase, then extract it as a rule, replace targets of child nodes with non-terminal.

• Node Merging Extraction
  For each node, try to merge max n layers of its child nodes into it(in practice, use 4).Then derive a new merged node with a merged target span.
  If this merged node is consistent, and all of its new child nodes are initial phrases, then extract it as a rule.

• Lexical rule extraction
  Just same as initial phrase extraction, get word pairs.
  Only extract from left nodes.

• Hole digging in leaf nodes
  (for future struggle)

Extracted Rule Format:
  (SOURCE, TARGET, TAG)
  SOURCE ||| TARGET ||| TAG ||| ALIGNMENT ||| FREQUENCY

Example:
  ([1,2,-1,4], [5,6,-1,8,9], 'NN')
  the hot X1 went ||| SONO ATSUI X1 NAKU NATTA ||| NN ||| 0-0 1-1 ||| 0.125

- Raphael 2012.8
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import math
from heapq import merge
from abraham.setting import setting
from sense import SenseTree, GeneralTree
import itertools



setting.load(["max_merge_nodes", "max_tokens"])

class Extractor:
  """
  Rule extractor for Gentile.
  """

  contentNodeSet = None
  sense = None
  """ @type: SenseTree """
  tree = None
  """ @type: GeneralTree """
  targets = None
  """ @type: list of string """
  mapAlignment = None
  """ @type: dict """
  mapReversedAlignment = None
  """ @type: dict """
  mapNodeTokens = None
  """ @type: dict """
  mapNodeSpan = None
  """ @type: dict """
  mapNodeConsistent = None
  """ @type: dict """

  initialPhrases = None
  hierarchicalRules = None
  mergedRules = None
  lexicalRules = None
  innerPhraseRules = None


  
  def __init__(self,sense,targets,mapAlignment):
    """
    @type sense: SenseTree
    @type targets: list of string
    @type mapAlignment: dict
    """
    self.getNodeTag = lambda n: "[%s]" % self.sense.tokens[self.sense.mapNodeToMainToken[n]-1][0]
    self.maxNTCount = setting.reconstruction_max_nt
    self.maxTransactionRate = setting.max_transaction_rate
    sense.rebuildTopNode()
    sense.appendXToTree()
    sense.upMergeAllConjNodes()
    sense.rebuildCommaNodes()
    sense.convertTags()
    sense.separateContiniousNonTerminals()
    # sense.mergeContinuousNTs()
    self.sense = sense
    self.tree = sense.tree
    """:type: GeneralTree """
    self.targets = targets
    self.mapAlignment = mapAlignment

    self.buildNodeTokensMap()
    self.buildReversedAlignmentMap()
    self.fillAlignmentMaps()
    self.buildNodeSpanMap()
    self.buildNodeConsistentMap()
    self.extractInitialPhrases()
    self.extractHierarchicalRules()
    self.extractMergedRules()
    self.extractLexicalRules()
    self.extractInnerPhraseRules()

  def buildNodeTokensMap(self, nodeId=None):
    """
    Build a map that maps a node to all source side tokens in the span of this node.
    """
    if not self.mapNodeTokens:
      self.mapNodeTokens = {}
    if not nodeId:
      nodeId = self.tree.root

    for childNodeId in self.tree.children(nodeId):
      self.buildNodeTokensMap(childNodeId)

    tokens = self.tree.node(nodeId)
    n = 0
    while n < len(tokens):
      token = tokens[n]
      if token < 0:
        linkedNodeId = -token
        tokensToInsert = self.mapNodeTokens[linkedNodeId]
        tokens = tokens[:n] + tokensToInsert + tokens[n+1:]
      n += 1

    self.mapNodeTokens[nodeId] = tokens

  def buildReversedAlignmentMap(self):
    """
    Build a map that saves alignment from target side to source side.
    """
    self.mapReversedAlignment = {}
    for nSource in self.mapAlignment:
      targets = self.mapAlignment[nSource]
      for nTarget in targets:
        self.mapReversedAlignment.setdefault(nTarget, []).append(nSource)

  def fillAlignmentMaps(self):
    """
    Fill alignment maps for those empty tokens to prevent error.
    """
    for i in range(len(self.sense.tokens)):
      tokenId = i + 1
      self.mapAlignment.setdefault(tokenId, [])
    for nTarget in range(len(self.targets)):
      self.mapReversedAlignment.setdefault(nTarget, [])

  def getSpanOfTokens(self, tokens):
    """
    Get target side span by given source side tokens.
    """
    targets = sum([self.mapAlignment[tokenId] for tokenId in tokens], [])
    if not targets:
      return []
    else:
      return range(min(targets), max(targets)+1)

  def buildNodeSpanMap(self):
    """
    Build a map that maps node id to its span in target side.
    """
    self.mapNodeSpan = {}
    for nodeId in self.tree.nodes:
      tokens = self.mapNodeTokens[nodeId]
      self.mapNodeSpan[nodeId] = self.getSpanOfTokens(tokens)

  def isPhrasePairConsistent(self, tokens, span):
    """
    Determine whether givens tokens is consistent, means:
      1. No other words outside the span aligned to tokens.
      2. No other tokens aligned to any word in span.
      3. At least one aligned word pair.
    """
    alignmentFound = False
    for tokenId in tokens:
      for targetId in self.mapAlignment[tokenId]:
        alignmentFound = True
        if targetId not in span:
          return False
    for targetId in span:
      for tokenId in self.mapReversedAlignment[targetId]:
        if tokenId not in tokens:
          return False
    return alignmentFound

  def buildNodeConsistentMap(self):
    """
    Build a map saves boolean value which indicates whether a node is consistent.
    """
    self.mapNodeConsistent = {}
    for nodeId in self.tree.nodes:
      tokens = self.mapNodeTokens[nodeId]
      span = self.mapNodeSpan[nodeId]
      self.mapNodeConsistent[nodeId] = self.isPhrasePairConsistent(tokens, span)

  def extractInitialPhrases(self):
    """
    Initial phrase extraction.
    """
    self.initialPhrases = []
    for nodeId in self.tree.nodes:
      # For each consistent leaf node, do extraction.
      if self.mapNodeConsistent[nodeId] and not self.tree.children(nodeId):
        tag = self.sense.tokens[self.sense.mapNodeToMainToken[nodeId]-1][0]
        tokens = self.mapNodeTokens[nodeId]
        span = self.mapNodeSpan[nodeId]
        self.initialPhrases.append((tokens, span, tag))

  def convertPhrasePairToRule(self, tokens, span, tag):
    """
    Convert a given pair to rule in the format of rule.
    Given tokens would be a list of tokens with holes in it.
    Span is a list of full range targets aligned to full tokens
    of the node having given tokens.
    If any child node is not consistent, then just return None.
    """
    holes = filter(lambda x: x < 0, tokens)
    # Check for all child nodes, make sure they are consistent.
    for hole in holes:
      linkedNodeId = -hole
      if not self.mapNodeConsistent[linkedNodeId]:
        return None
    # Rewrite tokens and span.
    span = list(span)
    tokens = list(tokens)
    nHole = 1
    for hole in holes:
      linkedNodeId = -hole
      childSpan = self.mapNodeSpan[linkedNodeId]
      assert childSpan
      # Rewrite source side token list.
      # tokens[tokens.index(hole)] = -nHole
      # Rewrite target side word list.
      firstWordInChildSpan = childSpan[0]
      span[span.index(firstWordInChildSpan)] = -nHole
      for wordId in childSpan:
        if wordId in span:
          span.remove(wordId)
      nHole += 1
    return (tokens, span, tag)

  def extractMergedRules(self):
    """
    Find consistent merged phrase pair for each node, try to merge max N child nodes.
    Only consistent node are searched, as the trick 1 's conclusion.
    Then Extract rules from merged phrase pairs.
    """
    maxMergeNodes = setting.max_merge_nodes
    self.mergedRules = []
    for nodeId in self.tree.nodes:
      if not self.mapNodeConsistent[nodeId]:
        continue
      tokens = self.tree.node(nodeId)
      span = self.mapNodeSpan[nodeId]
      tag = self.sense.tokens[self.sense.mapNodeToMainToken[nodeId]-1][0]
      holes = filter(lambda x: x < 0, tokens)
      if not holes:
        # No hole in the tokens, so unable to merge.
        continue
      for mergeNodes in range(1, maxMergeNodes+1):
        if mergeNodes > len(holes):
          break
        for holesSelected in itertools.combinations(holes, mergeNodes):
          # Replace tokens with tokens in child nodes.
          newTokens = tokens
          for hole in holesSelected:
            linkedNodeId = -hole
            childTokens = self.tree.node(linkedNodeId)
            posHole = newTokens.index(hole)
            newTokens = newTokens[:posHole] + childTokens + newTokens[posHole+1:]
          rule = self.convertPhrasePairToRule(newTokens, span, tag)
          if rule:
            self.mergedRules.append(rule)

  def extractHierarchicalRules(self):
    """
    Try to extract rule from each consistent node.
    """
    self.hierarchicalRules = []
    for nodeId in self.tree.nodes:
      if not self.mapNodeConsistent[nodeId]:
        continue
      if not self.tree.children(nodeId):
        continue
      tokens = self.tree.node(nodeId)
      span = self.mapNodeSpan[nodeId]
      tag = self.sense.tokens[self.sense.mapNodeToMainToken[nodeId]-1][0]
      rule = self.convertPhrasePairToRule(tokens, span, tag)
      if rule:
        self.hierarchicalRules.append(rule)

  def buildSpanForLattice(self, tokens, begin, width):
    """
    Build span for given item in lattice.
    @return: list, str
    """
    if width == 1 and tokens[begin] < 0:
      return None
    subtokens = tokens[begin:begin+width]
    terminals = [t for t in subtokens if t > 0]
    if not terminals:
      return None
    nonterminals = [t for t in subtokens if t < 0]
    linkedTokens = sum([self.mapNodeTokens[-t] for t in nonterminals], [])
    coveredTokens = terminals + linkedTokens
    span = self.getSpanOfTokens(coveredTokens)
    if self.isPhrasePairConsistent(coveredTokens, span):
      return span, self.sense.getTokensTag(terminals)
    else:
      return None

  def findAllCombinations(self, begin, width):
    """
    Find all possible child lattice combinations for hierarchical phrase
    based style rule extraction.

    0 stands for terminals, and 1 stands for nonterminals,
    loop from 000 to 110 (do not allow all 1).
    Original nonterminals should not be indicated as terminals.
    Return:
    [NT Span, ...]
    [(begin1, width1, 0), ...]
                      |
                      terminal or nonterminal
    """
    combs = []
    for bits in range(0, 2**width-1):
      comb = []
      duringNT = False
      ntLength = 0
      ntBeginPos = 0
      ntCount = 0
      for iBit in range(0, width):
        if (bits >> iBit) % 2 == 0:
          # Check for Non-terminal end.
          if duringNT:
            comb.append((begin + ntBeginPos, ntLength, 1))
            ntLength = 0
            ntBeginPos = 0
            duringNT = False
            ntCount += 1
          # Append terminal.
          comb.append((begin + iBit, 1, 0))
        else:
          # Append Non-terminals.
          if not duringNT:
            ntBeginPos = iBit
            duringNT = True
          ntLength += 1
      # Check for Non-terminal end.
      if duringNT:
        comb.append((begin + ntBeginPos, ntLength, 1))
        ntCount += 1
      if ntCount <= self.maxNTCount:
        combs.append(comb)
    return combs

  def extractRulesForComb(self, tokens, begin, width, comb, mapLattice):
    """
    Extract rules for one combination in the lattice.
    """
    # Verification.
    for subBegin, subWidth, isNT in comb:
      # Original site be terminal.
      if subWidth == 1 and isNT and tokens[subBegin] < 0:
        return None
      # Support lattice for nonterminal does not exist.
      if isNT and not mapLattice[(subBegin, subWidth)]:
        return None
    # Build rule.
    sourceTokens = []
    sources = []
    targetsToAppend = []
    targetsToRemove = []
    siteTargets = []
    for subBegin, subWidth, isNT in comb:
      if not isNT:
        for token in tokens[subBegin:subBegin + subWidth]:
          if token > 0:
            sourceTokens.append(token)
            sources.append(self.sense.tokens[token - 1][1])
          else:
            linkedNodeId = -token
            if not self.mapNodeConsistent[linkedNodeId]:
              return None
            linkedMainToken = self.sense.mapNodeToMainToken[linkedNodeId]
            tag = self.sense.tokens[linkedMainToken-1][0]
            sourceTokens.append(token)
            sources.append("[%s]" % tag)
            targetSpan = self.mapNodeSpan[linkedNodeId]
            if not targetSpan:
              return None
            firstTarget = targetSpan[0]
            targetsToAppend.append(firstTarget)
            targetsToRemove.extend(targetSpan[1:])
            siteTargets.append(firstTarget)
      else:
        # For sites
        targetSpan, tag = mapLattice[(subBegin, subWidth)]
        if not targetSpan:
          return None
        sourceTokens.append(-1)
        sources.append("[%s]" % tag)
        firstTarget = targetSpan[0]
        targetsToAppend.append(firstTarget)
        targetsToRemove.extend(targetSpan[1:])
        siteTargets.append(firstTarget)
    wholeSpan, tag = mapLattice[(begin, width)]
    finalSpan = set(wholeSpan)
    finalSpan.update(targetsToAppend)
    finalSpan.difference_update(targetsToRemove)
    finalSpan = sorted(list(finalSpan))
    # Check max transaction rate.
    if len(finalSpan) > len(sources)*self.maxTransactionRate:
      return None
    source = " ".join(sources)
    targets = []
    for target in finalSpan:
      if target in siteTargets:
        targets.append("[X%d]" % siteTargets.index(target))
      else:
        targets.append(self.targets[target])
    target = " ".join(targets)
    alignmentString = self.buildAlignmentString((sourceTokens, finalSpan, None))
    return (source, target, tag, alignmentString)


  def extractRulesForLattice(self, tokens, begin, width, mapLattice):
    """
    For given item in lattice, extract possible rules follows hierarchical phrase based style.
    """
    rules = []
    # Find combinations.
    combs = self.findAllCombinations(begin, width)
    for comb in combs:
      rule = self.extractRulesForComb(tokens, begin, width, comb, mapLattice)
      if rule:
        rules.append(rule)
    return rules

  def  deepExtractNode(self, nodeId):
    """
    Use phrase based style to deep extract rules for given node.
    """
    rules = []
    tokens = self.tree.node(nodeId)
    # lattice -> span, tag
    mapLattice = {}
    for width in range(1, len(tokens) + 1):
      for begin in range(0, len(tokens) - width + 1):
        result = self.buildSpanForLattice(tokens, begin, width)
        mapLattice[(begin, width)] = result
        if result and width > 1:
          rulesLattice = self.extractRulesForLattice(tokens, begin, width, mapLattice)
          rules.extend(rulesLattice)
    return rules


  def extractInnerPhraseRules(self):
    """
    For nodes have many terminals, try to extract inner rules using
    that style in hierarchical phrase model.
    """
    self.innerPhraseRules = []
    minExtractTerminals = setting.min_deep_extract_terminals
    # Exact glue rule patterns
    minExtractTerminals = 0
    tree = self.tree
    for nodeId in tree.nodes:
      tokens = tree.node(nodeId)
      terminals = [t for t in tokens if t > 0]
      if len(terminals) >= minExtractTerminals and len(tokens) <= 10:
        rulesForNode = self.deepExtractNode(nodeId)
        self.innerPhraseRules.extend(rulesForNode)
    # Remove rules with connected two nonterminals.
    idx = 0
    while idx < len(self.innerPhraseRules):
      if self.innerPhraseRules[idx][0].count("] [") > 0:
        self.innerPhraseRules.pop(idx)
      else:
        idx += 1

  def exportGlueRules(self):
    """
    For all nodes, extract patterns for forming glue rules.
    """
    glueRules = []
    tree = self.tree
    for nodeId in tree.nodes:
      tokens = tree.node(nodeId)
      if len(tokens) > 8:
        continue
      # Build glue rule
      sourceString = " ".join(["[%s]" % self.sense.tokens[x - 1][0] if x > 0 else self.getNodeTag(-x) for x in tokens])
      spanAndTag = self.buildSpanForLattice(tokens, 0, len(tokens))
      if not spanAndTag:
        continue
      span, nodeTag = spanAndTag
      replaceCount = 0
      # Replace all targets for subtokens
      tokenIndex = 0
      for token in tokens:
        if token > 0:
          spanForToken = self.getSpanOfTokens([token])
        else:
          if -token not in self.mapNodeSpan:
            continue
          spanForToken = self.mapNodeSpan[-token]
        if not spanForToken or spanForToken[0] not in span:
          continue
        span[span.index(spanForToken[0])] = - tokenIndex - 1
        for targetToRemove in spanForToken:
          if targetToRemove in span:
            span.remove(targetToRemove)
        replaceCount += 1
        tokenIndex += 1
      if replaceCount != len(tokens):
        continue
      targetString = " ".join([self.targets[x] if x >= 0 else "[X%d]" % (-x-1) for x in span])
      glueRules.append((sourceString, targetString, nodeTag))
    # Export rules
    ruleStrings = []
    if not glueRules:
      return ""
    frequency = 1.0 / len(glueRules)
    for sourceString, targetString, tag in glueRules:
      ruleStrings.append("%s ||| %s ||| %s |||  ||| %f" % (sourceString, targetString, tag, frequency))
    return "\n".join(ruleStrings)


  def extractLexicalRules(self):
    """
    Extract lexical rules
    """
    self.lexicalRules = []
    for nodeId in self.tree.nodes:
      if self.tree.children(nodeId):
        continue
      tokens = self.tree.node(nodeId)
      for tokenId in tokens:
        span = self.mapAlignment[tokenId]
        if self.isPhrasePairConsistent([tokenId], span):
          tag = self.sense.tokens[tokenId-1][0]
          self.lexicalRules.append(([tokenId], span, tag))

  def buildAlignmentString(self, rule):
    """
    Build alignment string for a rule for future calculation of lexical probabilities.
    """
    tokens, span, _ = rule
    alignStrings = []
    for nToken, tokenId in enumerate(tokens):
      if tokenId < 0:
        continue
      alignedWords = self.mapAlignment[tokenId]
      for alignedWord in alignedWords:
        if alignedWord in span:
          alignStrings.append("%d-%d" % (nToken, span.index(alignedWord)))
    return " ".join(alignStrings)

  def exportRuleStrings(self):
    """
    Export all rules in string format.
    """
    # Export normal rules extracted from sense tree.
    maxTokensAllowed = setting.max_tokens
    rules = (self.initialPhrases + self.hierarchicalRules +
             self.mergedRules + self.lexicalRules)
    ruleStrings = []
    ruleFrequency = (1.0 / len(rules)) if rules else 0
    for rule in rules:
      tokens, targets, tag = rule
      if len(tokens) > maxTokensAllowed:
        continue
      # Check max transaction rate.
      if len(targets) > len(tokens)*self.maxTransactionRate:
        continue
      strTokens = " ".join([self.sense.tokens[x-1][1] if x > 0 else self.getNodeTag(-x) for x in tokens])
      strTargets = " ".join([self.targets[x] if x >= 0 else "[X%d]" % (-x-1) for x in targets])
      strAlignment = self.buildAlignmentString(rule)
      strRule = "%s ||| %s ||| %s ||| %s ||| %f" % (strTokens, strTargets, tag, strAlignment, ruleFrequency)
      ruleStrings.append(strRule)

    # Export hierarchical phrase based style extracted rules.
    ruleFrequency = (1.0 / len(self.innerPhraseRules)) if self.innerPhraseRules else 0
    for rule in self.innerPhraseRules:
      source, target, tag, alignmentString = rule
      strRule = "%s ||| %s ||| %s ||| %s ||| %f" % (source, target, tag, alignmentString, ruleFrequency)
      ruleStrings.append(strRule)

    return "\n".join(ruleStrings)

def test():
  """
  Hey !! you dear stick into unit test.
  Which destroys the art of codes.
  AAAEEEESSSHHHHHHHOOOO <-- means I hate unit test and anything related with test suite.
  Okay, Watch your back.
  Gukk, Momi, I saw a real test which improves development confidence and waste no time.
  """
  pcfg = "( (S (NP (JJ hexagonal) (NN hole) (NN 21j)) (VP (VBZ is) (VP (VBN formed) (PP (IN in) (NP (DT the) (NN end) (NN surface))) (PP (IN on) (NP (NP (DT the) (NN side)) (PP (IN of) (NP (JJ flange) (NN 21a))) (PP (IN in) (NP (NP (DT the) (NN center)) (PP (IN of) (NP (NP (PRP$ its) (NN axis)) (PP (IN of) (NP (NN stud) (CD 21))))))))))) (. .)) )"
  dep = """amod(21j-3, hexagonal-1)
nn(21j-3, hole-2)
nsubjpass(formed-5, 21j-3)
auxpass(formed-5, is-4)
root(ROOT-0, formed-5)
prep(formed-5, in-6)
det(surface-9, the-7)
nn(surface-9, end-8)
pobj(in-6, surface-9)
prep(formed-5, on-10)
det(side-12, the-11)
pobj(on-10, side-12)
prep(side-12, of-13)
amod(21a-15, flange-14)
pobj(of-13, 21a-15)
prep(side-12, in-16)
det(center-18, the-17)
pobj(in-16, center-18)
prep(center-18, of-19)
poss(axis-21, its-20)
pobj(of-19, axis-21)
prep(axis-21, of-22)
pobj(of-22, stud-23)
num(stud-23, 21-24)"""
  targets = "スタッド １ の フランジ １ ａ 側 の 端 面 に 軸 中心 に 六 角 穴 １ ｊ が 形成されている 。".split(" ")
  alignment = "22-0 23-0 23-1 12-2 13-3 14-4 14-5 9-6 11-6 6-7 10-7 7-8 8-9 9-10 17-12 15-13 0-14 0-15 1-16 2-17 2-18 3-19 4-20 24-21"
  mapAlignment = {}
  for pair in alignment.split(" "):
    src, tgt = map(int, pair.split("-"))
    mapAlignment.setdefault(src + 1, []).append(tgt)
  sense = SenseTree(pcfg, dep)
  ex = Extractor(sense, targets, mapAlignment)
  print "--- mapNodeTokens ---"
  for nodeId in ex.mapNodeTokens:
    print nodeId, ":", [ex.sense.tokens[n-1][1] for n in ex.mapNodeTokens[nodeId]]
  print "--- mapReversedAlignment ---"
  print ex.mapReversedAlignment
  print "--- buildNodeSpanMap ---"
  print ex.mapNodeSpan
  print "--- buildNodeConsistentMap ---"
  print ex.mapNodeConsistent
  print "--- extractInitialPhrases ---"
  print ex.initialPhrases
  print "--- extractHierarchicalRules ---"
  print [([ex.sense.tokens[x-1][1] if x > 0 else x for x in r[0]], r[1], r[2]) for r in ex.hierarchicalRules]
  print "--- extractMergedRules ---"
  print [([ex.sense.tokens[x-1][1] if x > 0 else x for x in r[0]], r[1], r[2]) for r in ex.mergedRules]
  print "--- extractLexicalRules ---"
  print [([ex.sense.tokens[x-1][1] if x > 0 else x for x in r[0]], r[1], r[2]) for r in ex.lexicalRules]
  print "--- deepExtractNode ---"
  print ex.deepExtractNode(2)
  print "--- extractInitialPhrases ---"
  print ex.innerPhraseRules
  print "--- extractGlueRules ---"
  print ex.exportGlueRules()
  print "--- exportRuleStrings ---"
  print ex.exportRuleStrings()

if __name__ == "__main__":
  test()
    
