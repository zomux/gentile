"""
build global setting object
interface:
- load: [config_needed,]
- __getattr__
"""
__author__ = 'raphael'
import sys,os
sys.path += [ "%s/%s" % (os.path.dirname(os.path.abspath(__file__)),d) for d in ['../utils','../abraham','../LibAbram'] ]
import yaml

class Setting:
  config = None
  loaded = False
  runningMode = None
  def __init__(self):
    pass

  def load(self,list_config_needed=[]):
    """
    Load file from config.yaml
    Exit with error if could not find key in list_config_needed
    """
    if self.loaded:
      for k in list_config_needed:
        if k not in self.config:
          print "[Error] not find %s in config" % k
          sys.exit()
          
    if len(sys.argv) < 2:
      print "[Error] run with argument of config file"
      print "[Example] python xxx.py config.yaml"
      sys.exit()

    file_config = sys.argv[-1]

    if not os.path.exists(file_config):
      print "[Error] config file not exists"
      sys.exit()

    self.config = yaml.load(open(file_config))
    for k in list_config_needed:
      if k not in self.config:
        print "[Error] not find %s in config" % k
        sys.exit()
    self.loaded = True

  def __getattr__(self, item):
    """
    get a item in config file
    @type item: string
    @rtype: string
    """
    if item in self.config and self.config[item]:
      return self.config[item]
    else:
      return None
    
setting = Setting()

############ unit test ##################
def unit_test():
  setting.load()
  print setting.file_source

#unit_test()