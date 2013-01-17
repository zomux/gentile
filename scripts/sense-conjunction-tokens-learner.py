import os,sys
sys.path.append(os.getcwd()+"/gentile")





if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "python sense-conjuction-tokens-learner.py [berkely tree file]"
    sys.exit()
  sys.argv.append("config.yaml")
  from sense import PCFGTree, SenseTree

  treeFile = sys.argv[1]
  lines = open(treeFile).xreadlines()

  actionLiftUp = SenseTree.liftUpTerminals
  s = SenseTree("(S (A A) (B B))","A-1 B-2")
  
  mapConjCount = {}
  n = 0
  for line in lines:
    if n % 10000 == 0:
      print n
    line = line.strip()
    if not line:
      break
    cfgTree = PCFGTree(line)
    tree = cfgTree.tree
    tokens = cfgTree.tokens
    # print tree.nodes
    tree = actionLiftUp(s, tree)
    # print tree.nodes
    for nodeId in tree.nodes:
      node = tree.node(nodeId)
      if type(node) == list and len(node) == 1:
        token = tokens[node[0]-1]
        tag, word = token
        k = "%s ||| %s" % (tag, word)
        mapConjCount.setdefault(k, 0)
        mapConjCount[k] += 1
    n += 1
  conjs = mapConjCount.keys()
  conjs.sort(key=lambda x:mapConjCount[x], reverse=True)
  for conj in conjs[:100]:
    print conj,mapConjCount[conj]



