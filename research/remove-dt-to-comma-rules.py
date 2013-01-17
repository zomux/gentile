#coding:utf-8
import sys,os

if len(sys.argv) != 2:
  print "python remove-dt-to-comma-rules.py rules.extracted"
  sys.exit()

lines = open(sys.argv[1]).xreadlines()

for line in lines:
  line = line.strip()
  if not line:
    continue
  source, target, _, _, _ = line.split(" ||| ")
  words = source.split(" ")
  if "the" in words or "a" in words or "an" in words:
    if "、" in target:
      continue
  if words[0] == "the" or words[0] == "a" or words[0] == "an":
    if target.startswith("の") or target.startswith("な"):
      continue
  print line
