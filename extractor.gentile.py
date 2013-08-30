"""
Gentile, sense tree-to-string model.
Rule extractor.

- Raphael 2012.8
"""
import sys, os
from abraham.setting import setting
from gentile.extractor import Extractor
from gentile.sense import SenseTree

# Parse arguments, this only works in python 2.7
import argparse
parser = argparse.ArgumentParser(description='Gentile Extractor.')
parser.add_argument("--glue", action='store_true', help="Extract glue rules")
parser.add_argument("config", help="path to the config file")
args = parser.parse_args()



#sys.argv.append("config.yaml")
setting.load(["file_source_tree","file_source_dep",
  "file_target","file_alignment","rule_table_path"])
if len(sys.argv) == 7:
  _,FILE_SOURCE_TREE,FILE_SOURCE_DEP,FILE_TARGET,FILE_ALIGNMENT,PATH_RULETABLES,_ = sys.argv

else:
  FILE_SOURCE_TREE = setting.file_source_tree
  FILE_SOURCE_DEP = setting.file_source_dep
  FILE_TARGET = setting.file_target
  FILE_ALIGNMENT = setting.file_alignment
  PATH_RULETABLES = setting.rule_table_path

linesTree = open(FILE_SOURCE_TREE).readlines()
linesDep = open(FILE_SOURCE_DEP).read().split("\n\n")
linesTarget = open(FILE_TARGET).readlines()
linesAlignment = open(FILE_ALIGNMENT).readlines()
print "[GENTILE] Extracting ..."
print "Tree: %d lines, Dep: %d blocks" % (len(linesTree), len(linesDep))
assert len(linesTree) <= len(linesDep)

def buildAlignmentMap(textAlignment):
  """
  Convert alignment text to a dict.
  """
  mapAlignment = {}
  pairs = textAlignment.split(" ")
  for pair in pairs:
    src, tgt = map(int, pair.split("-"))
    src += 1
    mapAlignment.setdefault(src, []).append(tgt)

  return mapAlignment

if not os.path.exists(PATH_RULETABLES):
  os.mkdir(PATH_RULETABLES)
if args.glue:
  fileOutput = open("%s/glue-rules.extracted" % PATH_RULETABLES, "w")
else:
  fileOutput = open("%s/rules.extracted" % PATH_RULETABLES, "w")

nLine = 0
while nLine < len(linesTree):
  # if nLine < 500000:
  #   nLine += 1
  #   continue
  textTree = linesTree[nLine].strip()
  if not textTree:
    assert nLine == len(linesTree) - 1
    continue
  textDep = linesDep[nLine].strip()
  textTarget = linesTarget[nLine].strip()
  textAlignment =linesAlignment[nLine].strip()
  mapAlignment = buildAlignmentMap(textAlignment)
  targets = textTarget.split(" ")
  try:
    senseTree = SenseTree(textTree, textDep)
  except:
    print >> sys.stderr, "\nError : Could not build sense tree"
    nLine += 1
    continue
  extractor = Extractor(senseTree, targets, mapAlignment)
  if args.glue:
    fileOutput.write(extractor.exportGlueRules())
  else:
    fileOutput.write(extractor.exportRuleStrings())
  fileOutput.write("\n")
  nLine += 1
  if nLine % 1000 == 0:
    print nLine,
    sys.stdout.flush()

fileOutput.close()

