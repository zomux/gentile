"""
Class for present model and calculate the cost for rule and hypothesis

Implement basic interface of calculating and hypothesis building
- calcRuleCost( rule )
- calcHypCost( hyp )


"""
import os,sys

import math 

from abraham.treestruct import DepTreeStruct
from abraham.ruletable import NovelDepStrRuleTable
from abraham.hypothesis import NovelDepStrHypothesis
from abraham.setting import setting
from abraham.logger import log_error,log
from languagemodel.srilm import LanguageModel

class Model:
  """
  Virtual class of models
  """
  def calcRuleCost(self,rule):
    return None
  def sortRules(self,rules,limit):
    return None
  def calcHypCost(self,hyp):
    return None

class NovelDepStrModel(Model):
  """
  class for presenting the model in Novel Dep-to-string Model
  """
  # { rule->cost object }
  # cost object : { word_penalty:,lm_cost:,       table_cost:,future_cost:,rule_cost: }
  #                 |-----no weight------|        |-----------weighted--------------|
  mapRuleCostObj = {}
  maxGram = None
  lm = None
  weight_word_penalty = None
  weight_lm = None
  weight_translate_costs = None
  def __init__(self):
    """
    Initiate the language model
    initiate the model with weights in setting file
    """
    setting.load(["max_gram","file_lm","weight_word_penalty","weight_lm","weight_translate_costs"])
    self.maxGram = int(setting.max_gram)
    sys.stderr.write("[NovelDepStrModel] loading language model... \n")
    self.lm = LanguageModel(lm_file=setting.file_lm, n=setting.max_gram)
    self.weight_word_penalty = setting.weight_word_penalty
    self.weight_lm = setting.weight_lm
    self.weight_translate_costs = setting.weight_translate_costs

  def calcLMforRule(self,tgts):
    """
    A B C X D E X
    in 3 gram
    lcost = sum(cost of 3gram)
    fcost = sum(cost of 1gram and 2gram)
    @type tgts: list of string
    @rtype: (lcost,fcost)
    """

    ngram_start_pos = 0
    fcost,lcost = 0.0,0.0
    for i,word in enumerate(tgts):
      if word == "X":
        # reset start position when meet x
        ngram_start_pos = i+1
      elif i+1-ngram_start_pos < self.maxGram:
        # for small than max gram , calculate future cost
        fcost += self.lm.readNGram(tgts[ngram_start_pos:i+1])
      elif i+1-ngram_start_pos >= self.maxGram:
        # calculate language cost
        lcost += self.lm.readNGram(tgts[i-self.maxGram+1:i+1])
    return lcost,fcost

  def calcRuleCost(self,rule):
    """
    calculate the cost of rule
    @type rule: string
    @rtype: object
    """
    objcost = {}
    head,src,tgt,align,pfreq,probs = rule.split(" ||| ")
    tgts = tgt.split(",")

    objcost['word_penalty'] = -(len(tgts) - tgts.count("X"))

    lcost,fcost = self.calcLMforRule(tgts)
    objcost['future_cost'] = fcost*self.weight_lm
    objcost['lm_cost'] = lcost

    translate_costs = [float(p) for p in probs.split(" ")]

    objcost['table_cost'] = 0.0
    for i,cost in enumerate(translate_costs):
      objcost['table_cost'] += self.weight_translate_costs[i]*cost
      if setting.runningMode == "mert":
        objcost['tcost_'+str(i)] = self.weight_translate_costs[i]*cost

    objcost['rule_cost'] = self.weight_word_penalty*objcost['word_penalty'] + \
                        self.weight_lm*objcost['lm_cost'] + \
                        objcost['table_cost']




    return objcost
  def calcHypCost(self,hyp):
    """
    calculate the cost of hyp
    @type hyp: NovelDepStrHypothesis
    @rtype: float
    """
    return 1.0
  def sortRules(self,rules,limit=1000):
    """
    For each [rules] , calculate the cost , and return sorted rules
    but only keep [limit] rules
    @type rules: list of string
    @type limit: number
    @rtype: list of string
    """

    mapCurrentRuleCost = {}

    for rule in rules:
      hash_key = hash(rule)
      if hash_key not in self.mapRuleCostObj:
        objcost = self.calcRuleCost(rule)
        self.mapRuleCostObj[ hash_key ] = objcost
        mapCurrentRuleCost[ rule ] = objcost['rule_cost'] + objcost['future_cost']
      else:
        objcost = self.mapRuleCostObj[hash_key]
        mapCurrentRuleCost[ rule ] = objcost['rule_cost'] + objcost['future_cost']

    rules.sort(key=lambda x:mapCurrentRuleCost[x],reverse=True)
    return rules[:limit]

  def getRuleCostObj(self,rule):
    """
    @type rule: string
    @rtype: object
    """
    hash_key = hash(rule)
    if hash_key not in self.mapRuleCostObj:
      objcost = self.calcRuleCost(rule)
      self.mapRuleCostObj[ hash_key ] = objcost
      return objcost
    else:
      return self.mapRuleCostObj[hash_key]

  def getSentenseCost(self,tokens):
    """
    @type tokens: list of string
    @rtype: float
    """
    if len(tokens) < self.maxGram:
      iters = 1
    else:
      iters = len(tokens) - self.maxGram + 1
    prob = 0.0
    for ibegin in range(iters):
      prob += self.lm.readNGram(tokens[ibegin:ibegin+self.maxGram])
       
    
    return prob/iters
