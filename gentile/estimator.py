"""
Gentile Sense-to-string Model.
Estimator for dispersed temperate rule tables.

This will create final rule tables with translation probabilities.

- Raphael 2012.9
"""

import sys, os, math

from abraham.setting import setting

setting.load(["rule_table_path", "dispersion_tables"])

class Estimator:
  """
  A Estimator to calulate rule probabilities then produce final rules.
  """
  nSplittingRuleTable = None
  pathTables = None
  mapTargetCount = None
  stackContextRules = None

  def __init__(self):
    self.mapTargetCount = {}
    self.nSplittingRuleTable = setting.dispersion_tables
    self.pathTables = setting.rule_table_path

  
  def processTargetCountTable(self,path_file):
    mapThisTable = {}
    lines = open(path_file).xreadlines()
    for line in lines:
      if not line: continue
      target,count = line.split(" ")
      target = int(target,16)
      count = int(count)
      itable = target % self.nSplittingRuleTable
      self.mapTargetCount[itable].setdefault(target,0)
      self.mapTargetCount[itable][target] += count

  def processTargetCountTables(self):
    sys.stderr.write("[Estimator] Processing target count tables ... \n")

    for itable in range(self.nSplittingRuleTable):
      self.mapTargetCount[itable] = {}
      sys.stderr.write("#")
      tablefile = "%s/targetcount.tmp.%d" % (self.pathTables, itable)
      self.processTargetCountTable(tablefile)

    sys.stderr.write("\n")
    return self.mapTargetCount

  # @profile
  def saveRulesForSource(self,file_output,str_source,rules):
    """
    build a rule and output it
    output format:
    :H(Source)
    Target Pf2e Pe2f PLEX-f2e PLEX-e2f 2.718 
    ...
    ###
    tag-as-context ||| i_target1,i_target2
    ...

    @param rules: list of (hash_target,str_target,tag,freq,lex_prob_f2e,lex_prob_e2f)
    """
    # target -> (freq,penalty,strength)
    map_processed_target = {}
    map_processed_target_score = {}
    map_context_target = {}
    count_f = len(rules)
    rules.sort()
    irule = 0 
    while irule < count_f:
      rule = rules[irule]
      hash_target = rule[0]
      str_target = rule[1]
      #assert hash_target not in map_processed_target, "fatal error line253"
      count_fe,sum_freq,sum_lex_f2e,sum_lex_e2f = 0.0,0.0,0.0,0.0
      count_e = self.mapTargetCount[hash_target % self.nSplittingRuleTable][hash_target]
      while irule < count_f:
        rule_with_e = rules[irule]
        if rule_with_e[0] != hash_target: break
        e,str_e,context,freq,lex_prob_f2e,lex_prob_e2f = rule_with_e
        count_fe += 1
        sum_freq += freq
        sum_lex_f2e += lex_prob_f2e
        sum_lex_e2f += lex_prob_e2f
        irule += 1
        map_context_target.setdefault(context,set([]))
        map_context_target[context].add(hash_target)
      # calulate output final prob of features
      count_fe = float(count_fe)
      frequency = "%f" % math.log(sum_freq / count_fe)
      lex_prob_f2e = "%f" % (sum_lex_f2e / count_fe)
      lex_prob_e2f = "%f" % (sum_lex_e2f / count_fe)
      prob_f2e = math.log(count_fe / count_f)
      prob_e2f = math.log(count_fe / count_e)
      # record score for sort
      # map_processed_target_score[hash_target] = prob_f2e + prob_e2f
      map_processed_target_score[hash_target] = count_fe
      prob_f2e = "%f" % (prob_f2e)
      prob_e2f = "%f" % (prob_e2f)
      cost_count = "%f" % (math.log(count_fe / 1000) if count_fe < 1000 else 0.0)
      map_processed_target[hash_target] = str_target +" ||| " + \
               " ".join([cost_count, prob_f2e,prob_e2f,lex_prob_f2e,lex_prob_e2f,"2.718"])
  # got all rules , sort it, and prun it
    targets = map_processed_target.keys()
    targets.sort(key=lambda x:map_processed_target_score[x],reverse=True)
    targets = targets[:setting.max_rules_for_each_source]
    # write into output file
    file_output.write(":"+str_source+"\n")
    for hash_target in targets:
      rule = map_processed_target[hash_target]
      file_output.write(rule+"\n")
    # write context maps
    file_output.write("###\n")
    for context in map_context_target:
      acceptable = []
      for htgt in map_context_target[context]:
        try:
          acceptable.append(str(targets.index(htgt)))
        except:
          pass
      if acceptable:
        file_output.write("%s ||| %s\n" % (context, " ".join(acceptable)))
    return targets

  def processRuleTable(self,file,file_output):
    rules = []
    cur_source = None
    lines = file.xreadlines()
    for line in lines:
      line = line.strip()
      if not line: continue
      pairs_main = line.split(" ||| ")
      # SOURCE ||| TARGET ||| TAG ||| FREQ ||| LEX_PROB_F2E LEX_PROB_E2F
      source, target, tag, freq, lex_probs = pairs_main
      hash_source = int(source,16)

      # if moved into a new fragment
      # then save rules for previous fragment
      if hash_source != cur_source:
        if cur_source:
          saved_targets = self.saveRulesForSource(file_output, "%x" % cur_source, rules)
        rules = []
        cur_source = hash_source
      # record rules
      lex_prob_f2e, lex_prob_e2f = map(float, lex_probs.split(" "))
      freq = float(freq)
      rules.append((hash(target), target, tag, freq, lex_prob_f2e, lex_prob_e2f))
    if rules:
      self.saveRulesForSource(file_output, "%x" % cur_source, rules)

  def processRuleTables(self):
    sys.stderr.write("[Estimator] Processing rule tables ... \n")
    for itable in range(self.nSplittingRuleTable):
      #tablefile = open("%s/ruletable.tmp.sorted.%d" % (self.pathTables,itable))
      tablefile = os.popen("sort -k 1,17 %s/rules.tmp.%d" % (self.pathTables,itable))
      file_output = open("%s/rules.final.%d" % (self.pathTables,itable),"w")
      self.processRuleTable(tablefile,file_output)
      sys.stderr.write("#")
      file_output.close()
    sys.stderr.write("\n")

  def run(self):
    self.processTargetCountTables()
    self.processRuleTables()