"""
Neither shall thy name any more be called Abram,
but thy name shall be Abraham;
for a father of many nations have I made thee.
(Genesis 17:5)

- Raphael Shu 2012,3
"""

import sys,os
sys.path += ["%s/abraham" % os.path.dirname(os.path.abspath(__file__))]
from abraham.setting import setting
from gentile.decoder import GentileDecoder
from chiropractor.decoder import ChiropracticDecoder

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
    setting.load(["enable_chiropractic","file_translation_input_tree","file_translation_input_dep","file_translation_output","size_cube_pruning"])
    linesDep = open(setting.file_translation_input_dep).read().split("\n\n")
    linesTree = open(setting.file_translation_input_tree).readlines()

    decoder = setting.enable_chiropractic and ChiropracticDecoder() or GentileDecoder()
    foutput = open(setting.file_translation_output, "w")

    print "[Abraham]","translate %d sentences..." % (len(linesTree))
    
    for i in range(len(linesTree)):
      lineTree = linesTree[i].strip()
      lineDep = linesDep[i].strip()
      hyps = decoder.translateNBest(lineTree, lineDep)
      hyps[0].trace()
      if len(hyps)==0:
        print "[%d]" % i , "Translation Failed!!!"
        foutput.write("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n")
        continue
      result = hyps[0].getTranslation()

      print "[%d]" % i , result
      foutput.write(result+"\n")
      foutput.flush()
    foutput.close()

  elif arg_length == 3:
    # abraham.py config.yaml [cmd]
    command = sys.argv[1]
    if command == "mert":
      # when in the mert mode , nothing is other than normal
      # but output is a nbest text with format of
      # number ||| translation ||| lambda1 lambda2 ...
      # so here we need to defined the lambdas
      setting.runningMode = "mert"
      setting.load(["file_translation_input_tree","file_translation_input_dep","file_translation_output"])
      decoder = GentileDecoder()
      linesDep = open(setting.file_translation_input_dep).read().split("\n\n")
      linesTree = open(setting.file_translation_input_tree).readlines()
      foutput = open(setting.file_translation_output,"w")

      for i in range(len(linesTree)):
        lineTree = linesTree[i].strip()
        lineDep = linesDep[i].strip()
        hyps = decoder.translateNBest(lineTree, lineDep)
        hyps[0].trace()
        for hyp in hyps:
          line_output = " ||| ".join([str(i),hyp.getTranslation(),
                                    " ".join([str(n) for n in hyp.getLambdas()])
                                   ])
          foutput.write(line_output+"\n")

        print "[%d] Got %d | %s" % (i,len(hyps),hyps[0].getTranslation())
