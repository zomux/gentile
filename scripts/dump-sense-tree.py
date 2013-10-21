import os,sys
sys.path.append(os.getcwd()+"/gentile")
sys.path.append(os.getcwd())

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "python sense-conjuction-tokens-learner.py [tree file] [dep file]"
    sys.exit()
  sys.argv.append("config.yaml")
  from sense import SenseTree, dump_sense_tree

  treeFile = open(sys.argv[1])
  depFile = open(sys.argv[2])

  linesTree = treeFile.readlines()
  linesDep = depFile.read().split("\n\n")


  for n in range(len(linesTree)):
    lineTree = linesTree[n].strip()
    lineDep = linesDep[n].strip()
    tree = SenseTree(lineTree, lineDep)
    tree.rebuildTopNode()
    tree.appendXToTree()
    tree.upMergeAllConjNodes()
    tree.rebuildCommaNodes()
    tree.convertTags()
    tree.separateContiniousNonTerminals()
    print dump_sense_tree(tree)
    print tree.tree.nodes
    print ""
