import os,sys
sys.path.append(os.getcwd()+"/gentile")
sys.path.append(os.getcwd())

class ConflictEvaluator(object):

  def __init__(self):
    self.allAlignmentCount = 0
    self.conflictedCount = 0
    self.conflictRatioList = []

  def buildAlignmentMap(self, alignmentText):
    alignmentMap = {}
    for pairString in alignmentText.split(" "):
      src, tgt = map(int, pairString.split("-"))
      alignmentMap.setdefault(src + 1, []).append(tgt + 1)
    return alignmentMap

  def buildTargetSpan(self, alignmentMap):
    maxTokenId = max(map(max, alignmentMap.values()))
    return [False] * (maxTokenId + 1)


  def record(self, cfgText, depText, targetText, alignmentText):
    # Build tree
    sense = SenseTree(cfgText, depText)
    sense.rebuildTopNode()
    sense.appendXToTree()
    sense.upMergeAllConjNodes()
    sense.rebuildCommaNodes()
    sense.forceUsingDepCrystals()
    sense.convertTags()
    sense.separateContiniousNonTerminals()


    alignmentMap = self.buildAlignmentMap(alignmentText)
    targetSpanUsed = self.buildTargetSpan(alignmentMap)

    # Surf bottom-up
    sense.buildLevelMap()
    cur_level = sense.getMaxLevel()
    conflictedCount = 0

    while cur_level > 0:
      # [head id,]
      nodes_cur_level = sense.getNodesByLevel(cur_level)
      for nodeId in nodes_cur_level:
        tokens = sense.tree.node(nodeId)
        alignedTargets = sum([alignmentMap[t] if t in alignmentMap else [] for t in tokens], [])
        if not alignedTargets:
          continue
        minTargetId = min(alignedTargets)
        maxTargetId = max(alignedTargets)
        for targetId in range(minTargetId, maxTargetId + 1):
          if targetSpanUsed[targetId] and targetId in alignedTargets:
            conflictedCount += 1
          else:
            targetSpanUsed[targetId] = True
      # end of current node
      cur_level -= 1

    alignmentCount = len(sum(alignmentMap.values(), []))

    self.conflictedCount += conflictedCount
    self.allAlignmentCount += alignmentCount
    self.conflictRatioList.append(float(conflictedCount)/alignmentCount)

  def show(self):
    print "Conflict ratio of all alignments:", float(self.conflictedCount) / self.allAlignmentCount, "(", self.conflictedCount, \
      "/", self.allAlignmentCount, ")"
    print "Average conflict ratio of each pair", sum(self.conflictRatioList) / len(self.conflictRatioList)
  





if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "python %s [folder]" % sys.argv[0]
    sys.exit()
  sys.argv.append("config.yaml")
  from sense import SenseTree, dump_sense_tree

  folderPath = sys.argv[1]

  treeFilename = folderPath + os.sep + "data.en.tree"
  depFilename = folderPath + os.sep + "data.en.dep"
  targetFilename = folderPath + os.sep + "data.ja"
  alignmentFilename = folderPath + os.sep + "aligned.grow-diag-final-and"

  treeFile = open(treeFilename)
  depFile = open(depFilename)
  alignmentFile = open(alignmentFilename)

  linesTree = treeFile.readlines()
  linesDep = depFile.read().split("\n\n")
  linesAlignment = alignmentFile.readlines()

  cfEvaluator = ConflictEvaluator()

  for n in range(len(linesTree)):
    lineTree = linesTree[n].strip()
    lineDep = linesDep[n].strip()
    lineAlignment = linesAlignment[n].strip()

    cfEvaluator.record(lineTree, lineDep, "", lineAlignment)

  cfEvaluator.show()
    