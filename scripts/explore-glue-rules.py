"""
Output glue rules
"""

import sys,os

sys.path.append(os.path.realpath("."))

from abraham.setting import setting
from gentile.ruletable import GentileRuleTable

setting.load()

class GlueRuleExplorer(object):

  def __init__(self):
    self.sourceFreqMap = {}

  def listSources(self):
    extractedFile = open("%s/glue-rules.extracted" % setting.rule_table_path)
    self.ruletable = GentileRuleTable(glue=True)
    for line in extractedFile.xreadlines():
      if not line:
        continue
      sourceString = line.split(" ||| ")[0]
      self.sourceFreqMap.setdefault(sourceString, 0)
      self.sourceFreqMap[sourceString] += 1

  def showTopSources(self):
    sourceStrings = self.sourceFreqMap.keys()
    sourceStrings.sort(key=lambda x: self.sourceFreqMap[x], reverse=True)
    for sourceString in sourceStrings[:20]:
      rules = self.ruletable.findBySource(sourceString, [], "")
      if rules:
        print "--- %s : %d ---" % (sourceString, self.sourceFreqMap[sourceString])
      for targetString, _, costs in rules:
        print targetString, ":", ",".join(["%f" % c for c in costs])

  def run(self):
    self.listSources()
    print "--- showTopSources ---"
    self.showTopSources()



if __name__ == "__main__":
  GlueRuleExplorer().run()