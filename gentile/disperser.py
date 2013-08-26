"""
Gentile Sense-to-string Model
Dispersion for extracted rules.

To estimate translation probabilities of rules in a controllable time,
we need to disperse rules into server independent tables by Hash(Source).
Then we could estimate them one by one.

So the disperser should finish these works:
1. disperse extracted rules into N dispersed tables by Hash(source).
2. During the dispersion, calculate lexical probabilities and 
   add scores other than translation probabilities to those rule tables.
3. Record target counts, and create a target count table after all done.

Dispersed Table Format:
HASH(SOURCE) ||| TARGET ||| TAG ||| FREQUENCY ||| P_lex(e|f) P_lex(f|e) 2.718

Target Count Table Format:
HASH(TARGET) COUNT

- Raphael 2012.8
"""

import sys, os
import math
from abraham.setting import setting

setting.load(["rule_table_path", "dispersion_tables"])
BACKOFF_LEXICAL_PROB = 0.0000002

class Disperser:
  """
  Build tables for final estimation.
  """
  heapSavedSources = None
  heapSavedTargets = None
  nSplittingRuleTable = setting.dispersion_tables
  listFileRuleTables = None
  pathTables = None
  listSourceTables = None
  listTargetTables = None
  listTargetCountTables = None
  mapTargetCount = None
  countTargetsSaved = 0

  def __init__(self, extractGlueRules = False):
    sys.stderr.write("[Disperser] Building tables ... \n")
    self.extractGlueRules = extractGlueRules
    self.glueToken = "glue-" if self.extractGlueRules else ""
    self.heapSavedSources = set([])
    self.heapSavedTargets = set([])
    self.mapTargetCount = {}
    if not os.path.exists(setting.rule_table_path):
      os.makedirs(setting.rule_table_path)
    self.pathTables = setting.rule_table_path
    # create source tables
    self.listSourceTables = []
    if setting.debug:
      for itable in range(self.nSplittingRuleTable):
        self.listSourceTables.append(open("%s/source.table.%d" % (self.pathTables,itable),"w"))
    # create target-count tables
    self.listTargetCountTables = []
    for itable in range(self.nSplittingRuleTable):
      self.listTargetCountTables.append(open("%s/%stargetcount.tmp.%d" % (self.pathTables, self.glueToken, itable),"w"))
    # create tmp splited rule tables
    self.listFileRuleTables = []
    for itable in range(self.nSplittingRuleTable):
      self.listFileRuleTables.append(open("%s/%srules.tmp.%d" % (self.pathTables, self.glueToken, itable),"w"))
    self.loadLexTables()

  def saveSource(self,hash_source,str_source):
    if not hash_source in self.heapSavedSources:
      self.listSourceTables[hash_source % self.nSplittingRuleTable].write("%x %s\n" % (hash_source,str_source))
      self.heapSavedSources.add(hash_source)

  def saveTargetCounts(self):
    for hash_target in self.mapTargetCount:
      count = self.mapTargetCount[hash_target]
      self.listTargetCountTables[hash_target % self.nSplittingRuleTable].write("%x %d\n" % (hash_target,count))
    self.countTargetsSaved = 0
    self.mapTargetCount = {}

  def saveTarget(self,hash_target,str_target):
    # save target count
    self.mapTargetCount.setdefault(hash_target,0)
    self.mapTargetCount[hash_target] += 1
    if self.countTargetsSaved > 50000:
      self.saveTargetCounts()
    self.countTargetsSaved += 1

  def saveRule(self,hash_source,rule):
    self.listFileRuleTables[hash_source % self.nSplittingRuleTable].write(rule+"\n")

  def loadLexTables(self):
    """
    Load two tables of lexical probabilities.
    """
    print "[Disperser] Loading lexical tables ..."
    self.lexE2F = {}
    self.lexF2E = {}
    self.failedLexicalRequestLog = open("%s/failed-lexical-requests.log" % self.pathTables, "w")
    lines = open(setting.file_lex_e2f).xreadlines()
    for line in lines:
      wf,we,prob = line.strip().split(" ")
      prob = float(prob)
      self.lexE2F[hash("%s %s" % (we, wf))] = prob
    lines = open(setting.file_lex_f2e).xreadlines()
    for line in lines:
      we,wf,prob = line.strip().split(" ")
      prob = float(prob)
      self.lexF2E[hash("%s %s" % (wf, we))] = prob

  def calcLexicalProb(self, source, target, alignments):
    """
    Calculate lexical probabilities.
    """
    if self.extractGlueRules:
      return (BACKOFF_LEXICAL_PROB, BACKOFF_LEXICAL_PROB)
    wordsF = source.split(" ")
    wordsE = target.split(" ")
    # Build alignment map.
    mapAlignF2E, mapAlignE2F = {}, {}
    for pair in alignments.split(" "):
      if not pair:
        continue
      iSrc, iTgt = map(int, pair.split("-"))
      mapAlignF2E.setdefault(iSrc, []).append(iTgt)
      mapAlignE2F.setdefault(iTgt, []).append(iSrc)
    # Fill map in case of null alignment.
    # -1 indicates null word.
    for iSrc in range(len(wordsF)):
      if wordsF[iSrc].startswith("["):
        continue
      if iSrc not in mapAlignF2E:
        mapAlignF2E[iSrc] = [-1]
    for iTgt in range(len(wordsE)):
      if wordsE[iTgt].startswith("["):
        continue
      if iTgt not in mapAlignE2F:
        mapAlignE2F[iTgt] = [-1]
    # Situation of NULL -> ALL.
    if not mapAlignF2E:
      mapAlignF2E[-1] = [tgt for tgt in range(len(wordsE)) if not wordsE[tgt].startswith("[")]
    if not mapAlignE2F:
      mapAlignE2F[-1] = [src for src in range(len(wordsF)) if not wordsF[src].startswith("[")]
    # Calculate f to e.
    lexProbF2E = 1.0
    for src in mapAlignF2E:
      sourceWord = wordsF[src] if src >= 0 else "NULL"
      targetWords = [wordsE[tgt] if tgt >= 0 else "NULL" for tgt in mapAlignF2E[src]]
      probOfThisWord = 0.0
      for targetWord in targetWords:
        k = hash("%s %s" % (sourceWord, targetWord))
        if k in self.lexF2E:
          prob = self.lexF2E[k]
        else:
          prob = BACKOFF_LEXICAL_PROB
          self.failedLexicalRequestLog.write("%s %s\n" % (sourceWord, targetWord))
        probOfThisWord += prob
      lexProbF2E *= probOfThisWord / len(targetWords)
    # Calculate e to f.
    lexProbE2F = 1.0
    for tgt in mapAlignE2F:
      targetWord = wordsE[tgt] if tgt >= 0 else "NULL"
      sourceWords = [wordsF[src] if src >= 0 else "NULL" for src in mapAlignE2F[tgt]]
      probOfThisWord = 0.0
      for sourceWord in sourceWords:
        k = hash("%s %s" % (targetWord, sourceWord))
        if k in self.lexE2F:
          prob = self.lexE2F[k]
        else:
          prob = BACKOFF_LEXICAL_PROB
          self.failedLexicalRequestLog.write("%s %s\n" % (targetWord, sourceWord))
        probOfThisWord += prob
      lexProbE2F *= probOfThisWord / len(sourceWords)

    return (math.log(lexProbF2E), math.log(lexProbE2F))
    
  def processRule(self, hashSource, rulePair):
    """
    Process input rule and return a string of tmp rule.
    The main task is to append lexical probabilities to given rule.
    @param hashSource: HASH(SOURCE)
    @param rulePair: a list of inputted extracted rule
    @return : H(source) ||| target ||| tag ||| frequency ||| PLEX_F2E PLEX_E2F
    """
    source, target, tag, alignments, freq = rulePair
    lexProbF2E, lexProbE2F = self.calcLexicalProb(source, target, alignments)

    return " ||| ".join(["%x" % hashSource, target, tag, freq, "%5f %5f" % (lexProbF2E, lexProbE2F)])




  def run(self):
    """
    Extract.
    """
    print "[Disperser] running ..."
    lines_rules_extracted = open("%s/%srules.extracted" % (self.pathTables, self.glueToken)).xreadlines()
    crules = 0
    setting_debug = setting.debug
    for line_rule_extracted in lines_rules_extracted:
      line_rule_extracted = line_rule_extracted.strip()
      if not line_rule_extracted:
        continue
      crules += 1
      if crules % 10000 == 0:
        sys.stderr.write("[Disperser] %d rules processed ... \n" % crules)
      # input rule format
      # source ||| target ||| tag ||| alignments ||| frequency

      pairs_main = line_rule_extracted.split(" ||| ")
      str_source, str_target, str_tag, str_alignments, str_frequency = pairs_main
      
      hash_target = hash(str_target)
      hash_source = hash(str_source)
        
      # save target to target hash table
      # only save count
      if setting_debug:
        self.saveSource(hash_source, str_source)

      self.saveTarget(hash_target,str_target)
     
      # save all rules to splited rule tables
      # tmp rule format:
      # H(source) ||| taget ||| tag ||| frequency ||| PLEX_F2E PLEX_E2F
      
      # Convert rules
     
      strRule = self.processRule(hash_source, pairs_main)

      # save rule
      self.saveRule(hash_source,strRule)

    # clean up
    self.saveTargetCounts()


