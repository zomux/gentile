"""
Decoder class
the overall translation task is completed in the class

the translation process is detailed as following.
first , we build lexical translation hypothesis list for each node
then , for all nodes but beside leaf nodes in bottom-up style order
we use cube pruning to produce translation hypothesis lists
then the translation hypothesis list of the root node is N-best results
In cube pruning,
rules corresponding to this head-dependent fragment and hypothesis list for each X
( lexical hypothesis for leaf nodes and head nodes, and normal hypothesis for internal nodes )
is put together to perform a bug-crawl style cube pruning

so , if a fragment has  n nodes , the dimension of cube pruning should be n+1

a rule dimension and hypothesises for each node
(lexical for leaf and head , normal for internal nodes)


praise the lord ! how nice the voice of Libera !

- Raphael Shu  2012,2
"""

import os,sys
from abraham.treestruct import DepTreeStruct
from abraham.ruletable import NovelDepStrRuleTable
from abraham.model import NovelDepStrModel
from abraham.hypothesis import NovelDepStrHypothesis
from abraham.cubepruner import AllInOneCubePruner
from abraham.setting import setting

from logger import log_error,log

class Decoder:
  """
  Virtual class of decoder
  """
  def translate(self,data):
    """
    @type data: string
    @rtype : string
    """
    return None

class NovelDepStrDecoder(Decoder):
  """
  Class that actually do the translation job
  present the translation model described in novel dep-to-str model
  """
  ruletable = None
  model = None
  lexicalTable = None
  
  def __init__(self):
    """
    Load rule table and language model once !!!
    """
    self.ruletable = NovelDepStrRuleTable(setting.file_rules_final)
    self.model = NovelDepStrModel()
    self.lexicalTable = {}

  def translateStanford(self,data_tag,data_dep):
    """
    translate the data in format of stanford parser (tag,basicDependency)
    @type data_tag: string
    @type data_dep: string
    @rtype: string
    """
    return self.translateStanfordNBest(data_tag,data_dep)[0].getTranslation()

  def build_lex_stack(self,tree,ruletable,model):
    """
    Build a stack for saving first n best lexical translation hypothesis for each node
    this n is usually same as the size of cube pruning
    @type tree: DepTreeStruct
    @type ruletable: NovelDepStrRuleTable
    @type model
    @rtype: object
    """
    stack_lex = {}
    # for each node in tree
    for id in tree.nodes:
      if id == 0 : continue # root node
      word = tree.nodes[id][0]
      # find lexical rules of the word of this node , and sort them
      rules = ruletable.findByHeadAndSrcLen(word+":0",1)
      if len(rules) == 0:
        # no lex rules found
        # ok we need to go to lex table to find one
        # and construct a pseudo rule
        setting.load(["file_lexical_translation_table"])
        if word in self.lexicalTable:
          # lexical rules of this word cached
          rules = self.lexicalTable[word]
        else:
          # not found in lexical translation table
          # then build pseudo rules
          print "[NovelDepStrDecoder] build pseudo lex rule for '%s'" % word
          lines = open(setting.file_lexical_translation_table).xreadlines()
          section_entered = False
          for line in lines:
            if line.startswith(word+" "):
              section_entered = True
              word_src,word_ref,prob = line.strip().split(" ")
              pseudo_rule = "%s:0 ||| %s ||| %s |||  ||| %s ||| %s %s %s %s 2.7182" \
                         % (word,word,word_ref,prob,prob,prob,prob,prob)
              rules.append(pseudo_rule)
            else:
              if section_entered == True:
                # all lexical rules should be created ,
                # and now its another section here
                # so there should be no more rule except to be extracted
                break
          if len(rules) == 0:
            # still not found , then make itself be translation (maybe a number)
            pseudo_rule = "%s:0 ||| %s ||| %s |||  ||| 0.001 ||| 0.001 0.001 0.001 0.001 2.7182" \
                         % (word,word,word)
            rules.append(pseudo_rule)
          # build pseudo rules finished , got rules
          # cache it
          self.lexicalTable[word] = rules
      rules = model.sortRules(rules,setting.size_cube_pruning)
      # build hypothesises and append to lexical stack
      stack_lex[id] = []
      for rule in rules:
        stack_lex[id].append( NovelDepStrHypothesis(model,(id,tree),rule) )

    return stack_lex
  
  def translateStanfordNBest(self,data_tag,data_dep):
    """
    Translate and return a N-best list
    @type data_tag: string
    @type data_dep: string
    @rtype: list of NovelDepStrHypothesis
    """
    # first, we need get the tree of input
    setting.load(["nbest"])
    tree = DepTreeStruct(data_tag,data_dep)
    ruletable = self.ruletable
    model = self.model
    # build lexical hypothesis stack
    # { id->[lexical hyp,] }
    stack_lex = self.build_lex_stack(tree,ruletable,model)
    # { id->[lexical hyp,] }
    stack_normal = {}
    # for each fragment ( head node is not leaf ) at bottom-up style
    # use corresponding rules and basic hypothesis(lex or normal) to build normal hyp for this fragment
    cur_level = tree.getMaxLevel()-1
    while cur_level > 0:
      # [head id,]
      nodes_cur_level = tree.getNodesByLevel(cur_level)
      for headid in nodes_cur_level:
        # only build normal hypothesises for internal nodes
        if tree.isLeafNode(headid) : continue
        # build rule list
        cur_fragment = (headid,tree)
        rules = ruletable.findByFragment(cur_fragment)
        if len(rules) == 0:
          # rules not found !!!
          rules = [ruletable.buildPsuedoRule(cur_fragment)]
          
        # [(rule,cost),...]
        stack_rules = model.sortRules(rules,setting.size_cube_pruning)
        # build hypothesis stacks for cube pruning
        # head node : lexical hypothesises
        # internal nodes : normal hypothesises
        # leaf nodes : lexical hypothesises
        # [[hyp,...],...]
        stacks_pruning = []
        # append lexical hypothesis stack for head node
        stacks_pruning.append(stack_lex[headid])
        # add other hypothesis stacks
        for nodeid in tree.getChildNodes(headid):
          if tree.isLeafNode(nodeid): # leaf node
            stacks_pruning.append(stack_lex[nodeid])
          else: # internal node
            assert nodeid in stack_normal
            stacks_pruning.append(stack_normal[nodeid])
        # now run the cube pruning and get normal hypothesises for current node
        pruner = AllInOneCubePruner(model,cur_fragment,stack_rules,stacks_pruning,setting.size_cube_pruning)
        list_hyps = pruner.prune()
        # sort pruned hyps
        stack_normal[headid] = list_hyps
      # end of current node
      cur_level -= 1

    if tree.headNodeId not in stack_normal or len(stack_normal[tree.headNodeId])==0:
      # failed
      print "NovelDepStrDecoder","Translation Failed!!!"
      return []

    # end building normal hypothesis stack
    stack_normal[tree.headNodeId][0].trace()

    return stack_normal[tree.headNodeId][:setting.nbest]
