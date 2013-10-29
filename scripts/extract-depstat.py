"""
Extract dependency crystals, may be mainly for nouns and verbs.
"""
import os,sys, re
sys.path.append(os.getcwd()+"/gentile")
sys.path.append(os.getcwd())

class DepStat(object):

  def __init__(self):
    self.nounModStat = {}

  def record(self, treeText, depText):
    sense = SenseTree(treeText, depText)
    deps = re.findall(r"(.+?)\(.+?\-(\d+?),.+?\-(\d+?)\)", depText)
    for modifier, depWordId, wordId in deps:
      depWordId, wordId = map(int, [depWordId, wordId])
      depWordTag = sense.tokens[depWordId - 1][0]
      if depWordTag.startswith("V"):
        self.nounModStat.setdefault(modifier, 0)
        self.nounModStat[modifier] += 1

  def show(self):
    # noun
    print "--- verb ---"
    allCount = sum(self.nounModStat.values())
    modifiers = self.nounModStat.keys()
    modifiers.sort(key=lambda x: self.nounModStat[x], reverse=True)
    for modifier in modifiers:
      count = self.nounModStat[modifier]
      print modifier, ":", float(count) / allCount



if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "python %s [tree file] [dep file]" % sys.argv[0]
    sys.exit()
  sys.argv.append("config.yaml")
  from sense import SenseTree, dump_sense_tree

  treeFile = open(sys.argv[1])
  depFile = open(sys.argv[2])

  linesTree = treeFile.readlines()
  linesDep = depFile.read().split("\n\n")

  stat = DepStat()

  for n in range(len(linesTree)):
    if n % 10000 == 0:
      print "#",
    lineTree = linesTree[n].strip()
    lineDep = linesDep[n].strip()

    stat.record(lineTree, lineDep)

  stat.show()

