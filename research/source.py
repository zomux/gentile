import sys,os
sys.path.append(os.path.abspath("./"))
from abraham.setting import setting

if __name__ == "__main__":
  if len(sys.argv) < 3:
    print "argument: fragment id , config.yaml"
    sys.exit()
  setting.load(["rule_table_path","dispersion_tables"])
  str_fragid = sys.argv[1]
  print str_fragid
  fragid = hash(str_fragid)
  path_table = "%s/source.table.%d" % (setting.rule_table_path, fragid % setting.dispersion_tables)
  lines = open(path_table).xreadlines()
  for line in lines:
    if line.startswith(str_fragid):
      print line
      break
