import sys,os
import tempfile

if len(sys.argv) != 2 and len(sys.argv) != 4:
  print "python log-analyzer.py [log-file] [line-bleu-file] [correct]"
  print "python log-analyzer.py [descriptor]"
  sys.exit()

if len(sys.argv) == 2:
  _, descriptor = sys.argv
  pathTest = "/poisson2/home2/raphael/ntcir10/data.test.100"
  pathGentileResearch = "/poisson2/home2/raphael/home/research/gentile/research"
  pathLog = "%s/%s.log" % (pathGentileResearch, descriptor)
  pathAnswer = "%s/data.ja" % (pathTest,)
  pathEn = "%s/data.en" % (pathTest,)
  pathResult = "%s/gentile.%s.ja" % (pathTest, descriptor)
  tmpfile = tempfile.mkstemp()[1]
  os.system("ruby /poisson2/home2/raphael/home/apps/bleu_kit/line_bleu.rb %s %s > %s" % (pathResult, pathAnswer, tmpfile))
  pathBleu = tmpfile

  docBleu = os.popen("ruby /poisson2/home2/raphael/home/apps/bleu_kit/doc_bleu.rb %s %s" % (pathResult, pathAnswer)).read().strip()


else:
  _, pathLog, pathBleu, pathAnswer = sys.argv
  docBleu = None

linesBleu = open(pathBleu).readlines()
linesAnwser = open(pathAnswer).readlines()
linesEn = open(pathEn).readlines()

linesLog = open(pathLog).read().split("\n---\n")[1:]

count = 0
countGlue = 0

for nResult in range(len(linesLog)/2):
  detail = linesLog[2*nResult].strip()
  translation = linesLog[2*nResult + 1].strip().split("] ",1)[1]
  lineBleu = linesBleu[nResult].strip()
  bleu, _ = lineBleu.split("\t")
  bleu = float(bleu)
  correct = linesAnwser[nResult].strip()
  en = linesEn[nResult].strip()
  if bleu == 0.0:
    print "--[%d %f]--" % (nResult+1, bleu)
    print detail
    print "---"
    print "[E]", en
    print "[J]", correct
    print "[R]", translation
    
    print ""
    if detail.count("[X0] [X1] [X2]") > 0:
      countGlue += 1
    count += 1

print "---"
print "All Found: %d" % count
print "Glue Found: %d" % countGlue
if docBleu:
  print "Doc Bleu: %s" % docBleu