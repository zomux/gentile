import sys,os
from abraham.setting import setting
import math
import time,threading
import multiprocessing

from gentile.disperser import Disperser
from gentile.estimator import Estimator

if __name__ == "__main__":
  command = sys.argv[1]
  if command == "--disperse":
    disperser = Disperser()
    disperser.run()
  elif command == "--estimate":
    estimator = Estimator()
    estimator.run()
  else:
    print \
    """
    python estimator.gentile.py --disperse config.yaml \n
    python estimator.gentile.py --estimate config.yaml
    """
