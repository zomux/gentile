"""
Gentile Sense-to-string Model.

Rule table indexer.

- Raphael 2012,2
"""
import sys,os,re,math

from abraham.setting import setting

setting.load(["rule_table_path","dispersion_tables"])

def build_index_table(file,file_output):
  lines = open(file).xreadlines()
  foutput = open(file_output,"w")
  record_for_flag = None
  sizecounter = 0
  for line in lines:
    sizecounter += len(line)
    if line.startswith(":"):
      flag = line[1:].strip()
      foutput.write("%s %d\n" % (flag,sizecounter))

for isplit in range(setting.dispersion_tables):
  print "[Indexer] Creating index for table",isplit
  path_input = "%s/rules.final.%d" % (setting.rule_table_path, isplit)
  path_output = "%s/index.final.%d" % (setting.rule_table_path, isplit)
  build_index_table(path_input,path_output)