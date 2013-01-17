#coding:utf-8
import sys,os
import re

if len(sys.argv) != 2:
  print "python list-all-tags.py rules.extracted"
  sys.exit()

lines = open(sys.argv[1]).xreadlines()

mapTagCounts = {} 

for line in lines:
  line = line.strip()
  if not line:
    continue
  source, _, _, _, _ = line.split(" ||| ")
  tags = re.findall("\[.+?\]", source)
  for tag in tags:
    mapTagCounts.setdefault(tag, 0)
    mapTagCounts[tag] += 1

tags = mapTagCounts.keys()

tags.sort(key=lambda x: mapTagCounts[x], reverse=True)

for tag in tags:
  print tag, mapTagCounts[tag]
