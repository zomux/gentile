import sys,os
sys.path.append(os.path.abspath("./"))
from abraham.setting import setting

if __name__ == "__main__":
  if len(sys.argv) < 3:
    print "argument: fragment"
    sys.exit()
  #sys.argv.append("config.yaml")
  setting.load(["rule_table_path","dispersion_tables"])
  str_frag = sys.argv[1]
  fragid = hash(str_frag)
  str_fragid = "%x" % fragid
  print "finding ",str_frag, str_fragid
  path_table = "%s/index.final.%d" % (setting.rule_table_path, fragid % setting.dispersion_tables)
  print path_table
  lines = open(path_table).xreadlines()
  for line in lines:
    if line.startswith(str_fragid):
      print line
      pos = int(line.strip().split(" ")[1])
      ftable = open("%s/rules.final.%d" % (setting.rule_table_path, fragid % setting.dispersion_tables))
      ftable.seek(pos)
      line = ftable.readline()
      while not line.startswith("#"):
        print line.strip()
        line = ftable.readline()
      break
  print "found ",str_frag, str_fragid
