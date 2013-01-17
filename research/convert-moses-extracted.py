import sys, os

if len(sys.argv) != 2:
  print "python convert-moses-extracted [extracted]"
  raise SystemExit

_, path = sys.argv

lines = open(path).xreadlines()

for line in lines:
  line = line.strip()
  if not line:
    continue
  source, target, alignment, freq = line.split(" ||| ")
  source = source.replace("[X][X]", "[X]").replace("(", "-LRB-").replace(")", "-RRB-")
  target = target.replace("[X][X]", "[X1]").replace("[X]", "[X0]")
  newLine = " ||| ".join([source, target, "X", alignment, freq])
  print newLine