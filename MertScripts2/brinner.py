"""
 Brinner for abraham
 will be called in command line 

 python brinner.py path_abraham.py template.yaml \
 SOURCE_FILE OUTPUT_FILE 'lambda1 lambda2 ... lambdaN'

 Lambda order : LM , Word Penalty , Translation costs...
 
 Raphael Shu , 2012.3
"""

# config
path_tmpconfig = "mert2.tmp.yaml"

import sys,os

if len(sys.argv)!=6:
  print "Command Format Error:"
  print " ".join(sys.argv)
  sys.exit()

path_brinner,path_abraham,path_config_template,path_input,path_output,lambdas = sys.argv

lambdas = lambdas.replace("'","").split(" ")

data_template = open(path_config_template).read()
data_template = data_template.replace("[PATH_INPUT]",path_input)
data_template = data_template.replace("[PATH_OUTPUT]",path_output)
data_template = data_template.replace("[WEIGHTS]",
                                      "\n".join(["- "+l for l in lambdas])
                                     )


open(path_tmpconfig,"w").write(data_template)

os.system("python %s mert %s" % (path_abraham,path_tmpconfig))

