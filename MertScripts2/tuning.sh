#!/bin/sh

command="python MertScripts2/brinner.py gentile.m.py MertScripts/config.template.yaml"
mincosts="-10 -10 -10 -10 -10 -10 -10 -10 -10 "
maxcosts="10 10 10 10 10 10 10 10 10"
initcosts="0.008574 0.165201 0.062078 0.093501 0.142538 -0.061505 -0.186249 0.017387 0.262967"
ref="/poisson2/home2/raphael/ntcir10/data.dev.full/data.ja"
workdir="/poisson2/home2/raphael/ntcir10/gentile.full.model/tuning2"
LC_ALL=C MertScripts2/mert-1.33/mert.rb --source X --reference "$ref" --workdir "$workdir" --command "$command" --min "$mincosts" --max "$maxcosts" --ini "$initcosts"

