"""
class of rule table to provide interfaces for
rule presentation and search for a rule

implement these interfaces
- __init__( file )
- findByHead( head )

- Raphael 2012 2
"""
import os,sys,cPickle
from abraham.treestruct import DepTreeStruct
from abraham.logger import log_error

class RuleTable:
  """
  virtual class for present rule table
  """
  def __init__(self,file_rule_table):
    pass
  def findByHead(self,head):
    return None

class NovelDepStrRuleTable(RuleTable):
  """
  present for novel dep-to-str model
  """
  # map of rules:
  # { hash("head:i")->{ len(src)->{ hash("pos of X,...")->rule }, ... }, ... }
  mapRuleTable = {}

  mapRuleScore = {}
  def __init__(self, file_rule_table):
    """
    load rule table file and initiate the map of rules
    @type file_rule_table: string
    """
    if not os.path.exists(file_rule_table):
      print "[Error] %s not exists" % file_rule_table
      sys.exit()
    print "[NovelDepStrRuleTable] loading rule table ..."
    if os.path.exists("ruletable.cache"):
      self.mapRuleTable = cPickle.load(open("ruletable.cache"))
      return

    for line in open(file_rule_table).xreadlines():
      line = line.strip()
      pair_rule = line.split(" ||| ")
      head,src,tgt,align,pfreq,probs = pair_rule
      hash_head = hash(head)
      len_src = len(src.split(","))
      self.mapRuleTable.setdefault(hash_head,{})
      self.mapRuleTable[hash_head].setdefault(len_src,[])
      self.mapRuleTable[hash_head][len_src].append(line)

    #cPickle.dump(self.mapRuleTable,open("ruletable.cache","w"))

  def findByHeadAndSrcLen(self,head,len_src):
    """
    Find the rule in plain text by given head and src length
    in format of "head:i"
    @type head : string
    @type len_src : number
    @rtype : list of string
    """
    hash_head = hash(head)
    try:
      return self.mapRuleTable[hash_head][len_src]
    except:
      # in this case some key cannot be found in the rule table
      return []

  def findByFragment(self,fragment):
    """
    Find rules by a head-dependent fragment described in novel dep-to-str model
    fragment : ( head id , DepTreeStruct )
    return a list of rules in plain text
    @type fragment: (number,DepTreeStruct)
    @rtype: list of string
    """
    head_id,tree = fragment
    if not tree.hasNode(head_id):
      return []
    # first build src ids,words,tags by input tree
    ids = sorted([head_id] + tree.getChildNodes(head_id))
    words,tags = [],[]
    head_idx = -1
    list_parent_ids = [id for id in ids if not tree.isLeafNode(id) and head_id!=id]
    # a list of idx of node with children
    # these node should only be replaced by node in rule
    # which have property of 1 or 2
    list_parents = []
    idx = 0
    for id in ids:
      node = tree.getNodeById(id)
      word,tag = node
      words.append( word )
      tags.append( tag )
      if id == head_id:
        head_idx = idx
      elif id in list_parent_ids:
        list_parents.append(idx)
      idx += 1
    assert head_id>=0 , "could not find head id ?"
    head = "%s:%d" % (words[head_idx],head_idx)
    rules = self.findByHeadAndSrcLen(head,len(ids))

    acceptable_rules = []
    for rule in rules:
      head,src,tgt,align,pfreq,probs = rule.split(" ||| ")
      align = align.split(",")
      list_sites = [ int(a[0]) for a in align if len(a)!=0 ]
      # first check if all node in list_parents
      # their corresponding position in rule is a substitution site , prop 1 or 2
      all_sites_found = True
      for idx in list_parents:
        if idx not in list_sites:
          # this site not found in rules
          all_sites_found = False
          break
      if not all_sites_found : continue
      # check the rule more detailed
      list_src = src.split(",")
      map_prop ={}
      for a in align:
        if len(a)==0 : continue
        map_prop[int(a[0])] = int(a[-1])
      # check for each word's corresponding
      all_corresponding = True
      for i in range(len(words)):
        if i not in map_prop or map_prop[i] == 1:
          # in this case , plain word should be corresponding
          if words[i] != list_src[i]:
            all_corresponding = False
            break
        else :
          if tags[i] != list_src[i]:
            all_corresponding = False
            break
      if all_corresponding:
        acceptable_rules.append(rule)

    return acceptable_rules

  def buildPsuedoRule(self,fragment):
    """
    Build a psuedo rule for given fragment
    @type fragment: (number,DepTreeStruct)
    @rtype: string
    """
    head_id,tree = fragment
    # first build src ids,words,tags by input tree
    ids = sorted([head_id] + tree.getChildNodes(head_id))
    list_src= []
    head_idx = -1
    # a list of idx of node with children
    # these node should only be replaced by node in rule
    # which have property of 1 or 2
    idx = 0
    for id in ids:
      node = tree.getNodeById(id)
      word,tag = node
      list_src.append( word )
      if id == head_id:
        head_idx = idx
      idx += 1
    assert head_id>=0 , "could not find head id ?"
    head = "%s:%d" % (list_src[head_idx],head_idx)
    src = ",".join( list_src )
    tgt = ",".join( ["X"]*len(list_src) )
    align = ",".join( [ "%d-%d-1" % (i,i) for i in range(len(list_src)) ] )
    pfreq = "0.000000001"
    probs = "0.1 0.1 0.1 0.1 2.7182"

    return " ||| ".join([head,src,tgt,align,pfreq,probs])


