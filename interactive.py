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
    
    decoder = GentileDecoder()
    

    print "[Gentile]", "Interactive Mode"

    while True:
      sentence = raw_input("[INPUT]")

      sentence = sentence.strip()

      _, pathText = tempfile.mkstemp()
      _, pathCFG = tempfile.mkstemp()
      _, pathDep = tempfile.mkstemp()

      open(pathText, "w").write(sentence)
      print "[Gentile] Parsing CFG Tree ..."
      os.system("cat %s | python /home/raphael/research/preprocess-en/preprocess-line.py | /home/raphael/apps/berkley/parse.sh > %s" % (pathText, pathCFG))
      print "[Gentile] Parsing DEP Tree ..."
      os.system("/home/raphael/apps/stanford-parser/dep.berkeley.sh %s > %s" % (pathCFG, pathDep))
      cfg = open(pathCFG).read().strip()
      dep = open(pathDep).read().strip()

      hyps = decoder.translateNBest(cfg, dep)
      hyps[0].trace()
      if len(hyps)==0:
        print "[%d]" % i , "Translation Failed!!!"
        foutput.write("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n")
        continue
      result = hyps[0].getTranslation()
      
      print "[TRANSLATION]", result

      
