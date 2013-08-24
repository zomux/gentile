#!/bin/sh

command="python MertScripts/brinner.py gentile.m.py MertScripts/config.template.yaml"
mincosts="-10 -10 -10 -10 -10 -10 -10 -10 -10"
maxcosts="10 10 10 10 10 10 10 10 10"
initcosts="0.00596950305498102 0.0702448396785429 0.0544369594255997 0.135654037244263 0.157281527993101 -0.0436228192716449 -0.144734369757711 -0.024341215018477 0.363714728555679"
ref="/poisson2/home2/raphael/ntcir10/data.dev.full/data.ja"
workdir="/now03/raphael/ntcir10/gentile.full.model/tuning.forcerc2"
LC_ALL=C MertScripts/mert-1.33/mert.rb --source X --reference "$ref" --workdir "$workdir" --command "$command" --min "$mincosts" --max "$maxcosts" --ini "$initcosts"

