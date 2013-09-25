import sys, os
from abraham.setting import setting

setting.load(["rule_table_path"])

if len(sys.argv) != 2:
  print "python auto-do-all.py [config.yaml]"
  sys.exit()

_, cfg = sys.argv

if not os.path.exists(cfg):
  print "config not exist"
  sys.exit()

def run(cmd):
  print cmd
  os.system(cmd)

desc = cfg.replace("config.", "").replace(".yaml", "")

run("python extractor.gentile.py %s" % cfg)
# Filter extracted rules
ruletable = "%s/rules.extracted" % setting.rule_table_path
run("mv %s %s.withdtcomma" % (ruletable, ruletable))
run("python research/remove-dt-to-comma-rules.py %s.withdtcomma > %s" % (ruletable, ruletable))
run("python estimator.gentile.py --disperse %s" % cfg)
run("python estimator.gentile.py --estimate %s" % cfg)
run("python index.gentile.py %s" % cfg)
run("python gentile.m.py %s > research/%s.log" % (cfg, desc))
run("date")