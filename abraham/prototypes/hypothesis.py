#coding:utf8
"""
class of a Hypothesis to provide interfaces
present a hypothesis and prepare score for cube pruning

implement these interfaces
- __init__( fragment , rule )
  fragment : (head_id,TreeStruct)
  rule : rule in plain text

- getScore()
- getTranslation

- Raphael 2012 2
"""

import os,sys
from abraham.treestruct import DepTreeStruct
from abraham.ruletable import NovelDepStrRuleTable
from abraham.setting import setting
from abraham.logger import log_error,log

class Hypothesis:
  """
  Virtual class to present a hypothesis of a fragment translation
  """
  def __init__(self,fragment,rule):
    """
    @type fragment: (number,TreeStruct)
    @type rule: string
    """
    pass
  def getTranslation(self):
    """
    @rtype: string
    """
    pass
  def getScore(self):
    """
    @rtype: float
    """
    pass

class NovelDepStrHypothesis(Hypothesis):
  """
  Class to present a translation hypothesis described in
  Novel dep-to-string model
  """
  # failed is true , when unable to build this hypothesis
  # by hypothesis list given as base hypothesis list
  failed = False
  isLexical = False
  headWordId = None
  headWord = None
  headWordTag = None
  tree = None
  """@type: DepTreeStruct"""
  sourceRule = None 
  # save for target part
  targetTranslation = None
  targetTranslationLength = None
  targetRule = None
  # target hypothesis
  # { idx -> hyp }
  targetBaseHypList = None
  targetSitePosition = None
  # end of target part
  # save the score
  score = None
  objcost = None
  # end of score
  model = None
  def __init__(self, model,fragment, rule, list_base_hyps=[]):
    """
    Build this hypothesis by given parameters , and calculate score
    @type fragment: (number,DepTreeStruct)
    @type rule: string
    @type list_base_hyps: list of NovelDepStrHypothesis
    @type model: NovelDepStrModel
    """
    self.targetBaseHypList = {}
    self.targetSitePosition = []
    self.failed = False
    self.model = model
    self.headWordId,self.tree = fragment
    self.headWord = self.tree.getNodeById(self.headWordId)[0]
    self.headWordTag = self.tree.getNodeById(self.headWordId)[1]
    self.buildTargetTranslation(rule,list_base_hyps)
    if self.failed : return
    self.score = self.calculateScore(rule)

  def buildTargetTranslation(self,rule,list_base_hyps):
    """
    Build target translation by the rule and base hypothesises
    if no enough base hypothesises are found, then set failed to TRUE
    @type rule: string
    @type list_base_hyps: list of NovelDepStrHypothesis
    """
    head,src,tgt,aligns,pfreq,probs = rule.split(" ||| ")
    # append the target string as my target rule
    self.targetRule = tgt
    self.sourceRule = src
    #
    tgts = tgt.split(",")
    srcs = src.split(",")
    self.targetTranslationLength = 0
    for tgt in tgts:
      self.targetTranslationLength += tgt.count(" ")+1
    # if is a lexical hypothesis , then set the flag to true
    if len(srcs) == 1: self.isLexical = True
    # for every substitution sites , find corresponding hyp
    # then save to the base list , and apply to the target translation
    for align in aligns.split(","):
      if len(align) == 0 : continue
      pos_f,pos_e,prop = [int(p) for p in align.split("-")]
      word = srcs[pos_f]
      hyp_found = False
      hyp = list_base_hyps[pos_f]
      if (prop<2 and hyp.headWord == word) or (prop==2 and hyp.headWordTag == word):
        tgts[pos_e] = hyp.getTranslation()
        self.targetTranslationLength += hyp.targetTranslationLength - 1
        self.targetBaseHypList[pos_e] = hyp
        self.targetSitePosition.append(pos_e)
        hyp_found = True
      if not hyp_found:
        self.failed = True
        return False
    self.targetTranslation = " ".join(tgts)
    
    return True



    
  def calculateScore(self,rule):
    """
    Calculate score of current hypothesis by rule,translation,and base hypothesis's scores
    @type rule: string
    @rtype: float
    """
    global model
    self.objcost = {}
    objcost_rule = self.model.getRuleCostObj(rule)

    self.objcost['word_penalty'] = objcost_rule['word_penalty'] + sum([hyp.objcost['word_penalty'] for hyp in self.targetBaseHypList.values()])
    lcost = objcost_rule['lm_cost'] + sum([hyp.objcost['lm_cost'] for hyp in self.targetBaseHypList.values()])
    fcost = 0.0

    # append new lm cost and future cost
    idx_site = 0
    cur_block_count = 0
    tgts = self.targetTranslation.split(" ")
    i = 0
    iWord = 0
    #self.lmwords = []
    #if hash(rule) == -6455657465040808917 and tgts==['\xef\xbc\x91', '', '\xe3\x81\x8a\xe3\x82\x88\xe3\x81\xb3', '\xef\xbc\x93']:
      #cur_block_countimport pdb;pdb.set_trace()
    while i < len(self.targetRule.split(",")):
      cur_block_count += 1
      if i in self.targetSitePosition:
        # in a X substitution site
        cur_block_count = 0
        pos_site_end = iWord + self.targetBaseHypList.values()[idx_site].targetTranslationLength - 1
        while iWord <= pos_site_end:
          if cur_block_count < self.model.maxGram:
            if iWord < self.model.maxGram-1:
              fcost += self.model.lm.readNGram(tgts[:iWord+1])
            else:
              lcost += self.model.lm.readNGram(tgts[iWord-self.model.maxGram+1:iWord+1])
              #self.lmwords.append(tgts[iWord-4:iWord+1])
              #print " ".join(tgts[iWord-self.model.maxGram+1:iWord+1])
          iWord += 1
          cur_block_count += 1
        
        cur_block_count = 0
        idx_site += 1
      else:
        # in the plain rule words
        if idx_site < len(self.targetBaseHypList.values()):
          # next site exists
          translation_of_next_site = self.targetBaseHypList.values()[idx_site].targetTranslation
          length_of_next_site = self.targetBaseHypList.values()[idx_site].targetTranslationLength
        else:
          # no further substitution site
          translation_of_next_site = None
          length_of_next_site = 0
        iii = iWord 
        #if translation_of_next_site == '\xef\xbc\x93':
          #import pdb; pdb.set_trace()
        while (translation_of_next_site == None and iWord<self.targetTranslationLength) or (translation_of_next_site != None and " ".join(tgts[iWord:iWord+length_of_next_site])!=translation_of_next_site):
          #if cur_block_count < self.model.maxGram:
          #if iWord > 1000:
            #import pdb; pdb.set_trace()
          if iWord < self.model.maxGram-1:
            fcost += self.model.lm.readNGram(tgts[:iWord+1])
          else:
            lcost += self.model.lm.readNGram(tgts[iWord-self.model.maxGram+1:iWord+1])
            #self.lmwords.append(tgts[iWord-4:iWord+1])
            #print " ".join(tgts[iWord-self.model.maxGram+1:iWord+1]) #ngram ?
          iWord += 1
      i += 1
    # end while

    self.objcost['lm_cost'] = lcost
    
    self.objcost['translation_cost'] = objcost_rule['table_cost'] + sum([hyp.objcost['translation_cost'] for hyp in self.targetBaseHypList.values()])

    if setting.runningMode == "mert":
      # save every lambdas for table costs
      for i in range(len(setting.weight_translate_costs)):
        keyTCost = "tcost_"+str(i)
        self.objcost[keyTCost] = objcost_rule[keyTCost] + sum([hyp.objcost[keyTCost] for hyp in self.targetBaseHypList.values()])

    cost = self.model.weight_lm*lcost + self.model.weight_word_penalty*self.objcost['word_penalty'] \
           + self.objcost['translation_cost'] + self.model.weight_lm*fcost

    return cost
  
  def getTranslation(self):
    """
    @rtype: string
    """
    return self.targetTranslation
  def getScore(self):
    """
    @rtype: float
    """
    return self.score
  def traceHypothesis(self,hyp,level):
    """
    @type hyp: NovelDepStrHypothesis
    """
    if level == 0 :
      prefix = ""
    else:
      prefix = "   "*(level-1)+"|--"
    print prefix+hyp.sourceRule+" -> "+hyp.targetRule
    for bhyp in hyp.targetBaseHypList.values():
      self.traceHypothesis(bhyp,level+1)
  def trace(self):
    """
    @rtype: string
    """
    self.traceHypothesis(self,0)

  def getLambdas(self):
    """
    a interface for mert process , get evert lambdas of cost
    should be presented in specified order , for this model , in order of
    LM , Word Penalty , translation costs
    -------- ex ------
    5.1 , 2.2 ,         3.21 , 1.33 , 1.0 , 2.32 , 2.2
    @rtype: list of float
    """
    li = [self.model.weight_lm*self.objcost["lm_cost"],self.model.weight_word_penalty*self.objcost["lm_cost"]]
    li += [self.objcost["tcost_"+str(i)] for i in range(len(setting.weight_translate_costs))]
    return li