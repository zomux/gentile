"""
RPC master

- Raphael Shu 2012,3
"""

import sys,os
sys.path += ["%s/abraham" % os.path.dirname(os.path.abspath(__file__))]
from abraham.setting import setting
import xmlrpclib
import socket

SLAVE_LIST = ["localhost", "172.16.100.12"]

if __name__ == "__main__": 
  setting.load(["file_translation_input_tree","file_translation_input_dep","file_translation_output"])
  arg_length = len(sys.argv)
  if arg_length == 1:
    # abraham.py
    print "%s config.yaml" % sys.argv[0]
    raise SystemExit

  if arg_length == 3 and sys.argv[1] == "mert":
    # abraham.py config.yaml
    runningMode = "mert"
  else:
    runningMode = "normal"

  # Scan
  socket.setdefaulttimeout(3) 
  aliveSlaveList = []
  for address in SLAVE_LIST:
    port = 7000
    while True:
      url = "http://%s:%d" % (address, port)
      try:
        slave = xmlrpclib.ServerProxy(url)
        if slave.hello():
          aliveSlaveList.append(slave)
          print >> sys.stderr, "[Slave Found]", url
      except socket.error:
        break
      port += 1
  socket.setdefaulttimeout(None)

  # Run
  from multiprocessing import Process, Queue, Lock
  import time

  def subproc(pid, tasks, results, exits, lockTask):
    setting.runningMode = "normal"
    setting.load(["file_translation_input_tree","file_translation_input_dep","file_translation_output","size_cube_pruning"])
    decoder = GentileDecoder()

    while True:
      lockTask.acquire()
      if not tasks.empty():
        task = tasks.get()
      else:
        task = None
      lockTask.release()
      if not task:
        exits.put(pid)
        return
      tid, lineTree, lineDep = task
      
      hyps = decoder.translateNBest(lineTree, lineDep)
      result = hyps[0].getTranslation()
      output = result + "\n"
      msgStream = StringIO.StringIO()
      hyps[0].trace(stream=msgStream)
      print >> msgStream, "[%d]" % tid , result
      
      msg = msgStream.getvalue()
      results.put((tid, output, msg))

  lockTask = Lock()
  tasks = Queue()
  # Put tasks.
  linesDep = open(setting.file_translation_input_dep).read().split("\n\n")
  linesTree = open(setting.file_translation_input_tree).readlines()
  foutput = open(setting.file_translation_output,"w")

  for i in range(len(linesTree)):
    lineTree = linesTree[i].strip()
    lineDep = linesDep[i].strip()
    tasks.put((i,lineTree,lineDep))

  results = Queue()
  exits = Queue()
  procs = 8

  for pid in range(1, procs+1):
    p = Process(target=subproc, args=(pid, tasks, results, exits, lockTask))
    p.start()

  translationIdNeed = 0
  resultStack = {}
  exited = 0

  while True:
    # Copy translation results.
    if not results.empty():
      result = results.get()
      resultStack[result[0]] = result
    elif not exits.empty():
      exits.get()
      exited += 1
    elif resultStack:
      if translationIdNeed in resultStack:
        tid, output, msg = resultStack[translationIdNeed]
        foutput.write(output)
        print msg
        del resultStack[translationIdNeed]
        translationIdNeed += 1
      else:
        time.sleep(3)
    else:
      if exited == procs:
        foutput.close()
        break
      else:
        time.sleep(3)

