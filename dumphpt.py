"""
Neither shall thy name any more be called Abram,
but thy name shall be Abraham;
for a father of many nations have I made thee.
(Genesis 17:5)

- Raphael Shu 2012,3
"""

import sys,os, tempfile
sys.path += ["%s/abraham" % os.path.dirname(os.path.abspath(__file__))]
from abraham.setting import setting
from gentile.decoder import GentileDecoder
from gentile import sense
import StringIO

def dump_sense_tree(hptree,nodeId,level,stream=None):
    """
    @type hyp: GentileHypothesis
    """
    if level == 0 :
      prefix = ""
    else:
      prefix = "   "*(level-1)+"|--"
    tokens = []
    linkedNodes = []
    for tokenId in hptree.tree.node(nodeId):
      if tokenId > 0:
        word = hptree.tokens[tokenId-1][1]
        tokens.append(word)
      else:
        linkedNodeId = -tokenId
        linkedTokenId = hptree.mapNodeToMainToken[linkedNodeId]
        tag = hptree.tokens[linkedTokenId-1][0]
        tokens.append("[%s]" % (tag))
        linkedNodes.append(linkedNodeId)
    strTokens = " ".join(tokens)
    print >> stream, prefix + strTokens
    for linkedNodeId in linkedNodes:
      dump_sense_tree(hptree, linkedNodeId, level+1, stream)

if __name__ == "__main__":
  #sys.argv.append ("config.yaml")
  #sys.argv.append ("mert")
  arg_length = len(sys.argv)
  if arg_length == 1:
    # abraham.py
    print "usage : python abraham.py config.yaml"

  elif arg_length == 2:
    # abraham.py config.yaml
    setting.runningMode = "normal"
    setting.load(["file_translation_input_tree","file_translation_input_dep","file_translation_output","size_cube_pruning"])
    
    print "[Gentile]", "Interactive Mode"

    while True:
      sentence = raw_input("[INPUT]")

      sentence = sentence.strip()

      _, pathText = tempfile.mkstemp()
      _, pathCFG = tempfile.mkstemp()
      _, pathDep = tempfile.mkstemp()

      open(pathText, "w").write(sentence)
      print "[Gentile] Parsing CFG Tree ..."
      os.system("/home/raphael/apps/berkley/parse.sh < %s > %s" % (pathText, pathCFG))
      print "[Gentile] Parsing DEP Tree ..."
      os.system("/home/raphael/apps/stanford-parser/dep.berkeley.sh %s > %s" % (pathCFG, pathDep))
      cfg = open(pathCFG).read().strip()
      dep = open(pathDep).read().strip()

      t = sense.SenseTree(cfg,dep)
      t.rebuildTopNode()
      t.appendXToTree()
      t.upMergeAllConjNodes()
      t.rebuildCommaNodes()
      t.separateContiniousNonTerminals()
      resultStream = StringIO.StringIO()
      dump_sense_tree(t, t.tree.root, 0, resultStream)
      resultText = resultStream.getvalue()

      print resultText

      