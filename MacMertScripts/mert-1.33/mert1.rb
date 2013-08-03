#!/usr/bin/env ruby
#
# mert1.rb --ref reference_translation --nbest nbest_file --out lambda
#          --min "list of minimum weights" --max "list of maximum weights"
#          --ini "list of initial weights"
#
#

require 'getopts'
require 'mertlib'

getopts(nil, "ref:", "nbest:", "out:", 
	"min:", "max:", "ini:",
	"n:4", "stepSize:0.3", "simplexSize:0.01", "numItr:100",
	"numItr2:500", "optimization:linear", "maxKeepBest:50",
	"rhobeg:0.2", "rhoend:0.0001", "iprint:0", "maxfun:5000") or raise

ref = $OPT_ref
nbest = $OPT_nbest
out = $OPT_out
min = $OPT_min.split.map{|x| x.to_f}
max = $OPT_max.split.map{|x| x.to_f}
ini = $OPT_ini.split.map{|x| x.to_f}
n = $OPT_n.to_i
stepSize = $OPT_stepSize.to_f
simplexSize = $OPT_simplexSize.to_f
numItr = $OPT_numItr.to_i
numItr2 = $OPT_numItr2.to_i
optimization = $OPT_optimization
rhobeg = $OPT_rhobeg.to_f
rhoend = $OPT_rhoend.to_f
iprint = $OPT_iprint.to_i
maxfun = $OPT_maxfun.to_i
maxKeepBest = $OPT_maxKeepBest.to_i

STDERR.puts "ref = #{ref}"
STDERR.puts "nbest = #{nbest}"
STDERR.puts "out = #{out}"
STDERR.puts "min = #{min.inspect}"
STDERR.puts "max = #{max.inspect}"
STDERR.puts "ini = #{ini.inspect}"
STDERR.puts "n = #{n}"
STDERR.puts "optimization = #{optimization}"
STDERR.puts "numItr = #{numItr}"
STDERR.puts "maxKeepBest = #{maxKeepBest}"

mert = MertLib.new
mert.readRefs(ref)
mert.readNbests(nbest, n)
mert.setRange(min, max)
case optimization
when 'linear'
  STDERR.puts "numItr2 = #{numItr2}"
  bleu, lambda = mert.linear(ini, numItr, numItr2, maxKeepBest);
when 'uobyqa'
  STDERR.puts "rhobeg = #{rhobeg}"
  STDERR.puts "rhoend = #{rhoend}"
  STDERR.puts "iprint = #{iprint}"
  STDERR.puts "maxfun = #{maxfun}"
  bleu, lambda =
    mert.uobyqa(ini, rhobeg, rhoend, iprint, maxfun, numItr, maxKeepBest)
when 'simplex'
  STDERR.puts "stepSize = #{stepSize}"
  STDERR.puts "simplexSize = #{simplexSize}"
  STDERR.puts "numItr2 = #{numItr2}"
  bleu, lambda =
    mert.estimate(ini, stepSize, simplexSize, numItr, numItr2, maxKeepBest)
else
  raise "unknown optimization option"
end

STDERR.puts "BLEU = #{bleu}"
STDERR.puts "lambda = #{lambda.inspect}"

open(out, "w").puts lambda.join(' ')
