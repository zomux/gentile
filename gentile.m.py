"""
Neither shall thy name any more be called Abram,
but thy name shall be Abraham;
for a father of many nations have I made thee.
(Genesis 17:5)

- Raphael Shu 2012,3
"""

import sys, os, StringIO
sys.path += ["%s/abraham" % os.path.dirname(os.path.abspath(__file__))]
from abraham.setting import setting
from gentile.decoder import GentileDecoder

if __name__ == "__main__":
  arg_length = len(sys.argv)
  if arg_length == 1:
    # abraham.py
    print "usage : python gentile.m.py config.yaml"

  elif arg_length == 2:
    # abraham.py config.yaml
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

  elif arg_length == 3:
    command = sys.argv[1]
    if command == "mert":
      from multiprocessing import Process, Queue, Lock
      import time

      def subproc(pid, tasks, results, exits, lockTask):
        setting.runningMode = "mert"
        setting.load(["file_translation_input_tree","file_translation_input_dep","file_translation_output"])
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
          output = ""
          for hyp in hyps:
            line_output = " ||| ".join([str(tid),hyp.getTranslation(),
                                      " ".join([str(n) for n in hyp.getLambdas()])
                                     ])
            output += line_output + "\n"
          msg = "[%d] Got %d | %s" % (tid,len(hyps),hyps[0].getTranslation())
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
