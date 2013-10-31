"""
Gentile over network.

- Raphael Shu 2013.10
"""

import sys,os
sys.path += ["%s/abraham" % os.path.dirname(os.path.abspath(__file__))]
from abraham.setting import setting
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

class GentileSlave(object):

  def __init__(self, runningMode):
    setting.load(["file_translation_input_tree","file_translation_input_dep","file_translation_output"])
    setting.runningMode = runningMode
    print >> sys.stderr, "[GentileSlave]", "Initilizing decoder ..."
    # self.decoder = GentileDecoder()
    self.runningMode = runningMode
    self.busy = False
    print >> sys.stderr, "[GentileSlave]", "Waiting connection ..."

  def hello(self):
    return "hello"

  def doTranslation(self, id, cfgText, depText):
    hyps = decoder.translateNBest(cfgText, depText)
    if setting.runningMode == "mert":
      returnText = ""
      for hyp in hyps:
        line_output = " ||| ".join([str(i),hyp.getTranslation(),
                                    " ".join([str(n) for n in hyp.getLambdas()])
                                   ])
        returnText += line_output + "\n"
      print "[%d] Got %d | %s" % (id, len(hyps), hyps[0].getTranslation())
      return returnText
    else:
      hyps[0].trace()
      if len(hyps)==0:
        print "[%d]" % i , "Translation Failed!!!"
        return "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
      result = hyps[0].getTranslation()

      print "[%d]" % id , result
      return result+"\n"






if __name__ == "__main__":

  if len(sys.argv) != 4:
    print "%s [running-mode] [port] [config.yaml]" % sys.argv[0]
    raise SystemExit

  _, runningMode, port, _ = sys.argv

  port = int(port)

  server = SimpleXMLRPCServer(("localhost", port))
  server.register_introspection_functions()
  server.register_instance(GentileSlave(runningMode))
  server.serve_forever()
