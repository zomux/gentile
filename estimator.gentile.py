import sys,os
from abraham.setting import setting
import math
import time,threading
import multiprocessing
import argparse

from gentile.disperser import Disperser
from gentile.estimator import Estimator

if __name__ == "__main__":

  # Parse arguments
  argParser = argparse.ArgumentParser(description="Gentile Estimator")
  argParser.add_argument("--disperse", action="store_true")
  argParser.add_argument("--estimate", action="store_true")
  argParser.add_argument("--glue", action="store_true")
  argParser.add_argument("config")
  args = argParser.parse_args()

  command = sys.argv[1]
  if command == "--disperse":
    disperser = Disperser(extractGlueRules=args.glue)
    disperser.run()
  elif command == "--estimate":
    estimator = Estimator(estimateGlueRules=args.glue)
    estimator.run()
  else:
    print \
    """
    python estimator.gentile.py --disperse config.yaml \n
    python estimator.gentile.py --estimate config.yaml
    """
