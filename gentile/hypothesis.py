#coding:utf8
"""
Class of a Hypothesis to provide interfaces
present a hypothesis and prepare score for cube pruning

implement these interfaces
- __init__( fragment , rule )
  rule : rule in plain text

- getScore()
- getTranslation

- Raphael 2012.9
"""

import os,sys
from abraham.setting import setting
from abraham.logger import log_error,log

from gentile.model import GentileModel

class GentileHypothesis:
  """
  Class to present a translation hypothesis described in
  Novel dep-to-string model
  """
  # failed is true , when unable to build this hypothesis
  # by hypothesis list given as base hypothesis list

  model = None
  """@type: GentileModel"""
  sense = None
  node = None
  sites = None
  # save for target part
  translation = None
  translationTokens = None
  target = None
  # target hypothesis
  # { idx -> hyp }
  costs = None
  # end of target part
  # save the score
  score = None
  # end of score
  stackHypsSelected = None
  """@type: dict of GentileHypothesis"""

  def __init__(self, model, node, rule, stackHyps):
    """
    Build this hypothesis by given parameters , and calculate score
    @type fragment: (number,DepTreeStruct)
    @type rule: string
    @type list_base_hyps: list of NovelDepStrHypothesis
    @type model: NovelDepStrModel
    """
    self.sense = currentSenseTree
    self.model = model
    self.node = node
    if not rule:
      # Customize mode.
      return
    self.target, self.sites, costs = rule
    # add fake lm cost
    self.costs = costs[:]
    self.stackHypsSelected = stackHyps
    self.buildTargetTranslationAndMergeCosts()
    self.buildScore()

  def buildScore(self):
    """
    Set score of current hyp
    """
    lmcost = self.model.getSentenseCost(self.translationTokens)
    
    
    self.costs.append(lmcost)
    self.score = self.model.calculateHypothesisScore(self)

  def buildTargetTranslationAndMergeCosts(self):
    """
    1. Build target translation by the rule and base hypothesises
    2. Merge costs of base hypothesises to this hypothesis.
       !!! But do not merge lm cost
    """
    translation = self.target
    gotEmptyTranslation = False
    for isite in range(len(self.sites)):
      site = self.sites[isite]
      assert site in self.stackHypsSelected
      basehyp = self.stackHypsSelected[site]
      subtranslation = basehyp.getTranslation()
      if len(subtranslation) == 0:
        gotEmptyTranslation = True
      translation = translation.replace("[X%d]" % isite, subtranslation)
      # merge costs
      for icost in range(len(self.costs)):
        self.costs[icost] += basehyp.costs[icost]
      # end

    if gotEmptyTranslation:
      # an empty subtranslation is merged,
      # so need to merge two whitespaces to one guy
      translation = translation.replace("  "," ")
    self.translation = translation
    self.translationTokens = translation.split(" ")
    
    return True

  def getTranslation(self):
    """
    @rtype: string
    """
    return self.translation

  def getTranslationTokens(self):
    """
    @rtype: list
    """
    return self.translationTokens
  
  def getScore(self):
    """
    @rtype: float
    """
    return self.score

  def sourceString(self,hyp):
    """
    Represent fragment in string.
    """
    tokens = self.sense.tree.node(hyp.node)
    words = []
    for tokenId in tokens:
      if tokenId > 0:
        words.append(self.sense.tokens[tokenId-1][1])
      else:
        words.append(self.sense.tokens[self.sense.mapNodeToMainToken[-tokenId]-1][0])
    return " ".join(words)

  def traceHypothesis(self,hyp,level,stream=sys.stdout):
    """
    @type hyp: GentileHypothesis
    """
    if level == 0 :
      prefix = ""
    else:
      prefix = "   "*(level-1)+"|--"
    print >> stream, prefix+self.sourceString(hyp)+" -> "+hyp.target
    for site in hyp.sites:
      bhyp = hyp.stackHypsSelected[site]
      self.traceHypothesis(bhyp, level+1, stream)

      
  def trace(self,stream=sys.stdout):
    """
    @rtype: string
    """
    print >> stream, "---"
    self.traceHypothesis(self, 0, stream)
    print >> stream, "---"

  def getLambdas(self):
    """
    A interface for mert process , get every lambdas of features.
    @rtype: list of float
    """
    return self.costs