#!/usr/bin/env ruby

require 'getopts'
require 'mertlib'

getopts(nil, "source:", "reference:", "workdir:", "command:",
	"min:", "max:", "ini:",
	"n:4", "stepSize:0.3", "simplexSize:0.01", "numItr:100",
	"numItr2:500", "optimization:linear",
	"rhobeg:0.2", "rhoend:0.0001", "iprint:0", "maxfun:5000",
	"restart:0", "maxKeepBest:50") or raise


source = $OPT_source
reference = $OPT_reference

workdir = $OPT_workdir
command = $OPT_command
nbest = "#{workdir}/nbest.all"

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
restart = $OPT_restart.to_i
maxKeepBest = $OPT_maxKeepBest.to_i

STDERR.puts "source = #{source}"
STDERR.puts "reference = #{reference}"
STDERR.puts "workdir = #{workdir}"
STDERR.puts "command = #{command}"
STDERR.puts "nbest = #{nbest}"
STDERR.puts "min = #{min.inspect}"
STDERR.puts "max = #{max.inspect}"
STDERR.puts "ini = #{ini.inspect}"
STDERR.puts "n = #{n}"
STDERR.puts "optimization = #{optimization}"
STDERR.puts "numItr = #{numItr}"
STDERR.puts "maxKeepBest = #{maxKeepBest}"

case optimization
when 'linear'
  STDERR.puts "numItr2 = #{numItr2}"
when 'uobyqa'
  STDERR.puts "rhobeg = #{rhobeg}"
  STDERR.puts "rhoend = #{rhoend}"
  STDERR.puts "iprint = #{iprint}"
  STDERR.puts "maxfun = #{maxfun}"
when 'simplex'
  STDERR.puts "stepSize = #{stepSize}"
  STDERR.puts "simplexSize = #{simplexSize}"
  STDERR.puts "numItr2 = #{numItr2}"
else
  raise "unknown optimization option"
end

STDERR.puts "restart = #{restart}"

if File.exist?(workdir)
  raise "workdir '#{workdir}' exists!"
else
  Dir.mkdir(workdir)
end

def applyDecoder(command, input, output, lambdas)
  dosystem("#{command} #{input} #{output} '#{lambdas.join(' ')}'")
end

def dosystem(command)
  STDERR.puts command
  system(command)
end

def decoding(command, source, output, lambdas, workdir, nbest)
  mertdir = "MertScripts/mert-1.33"
  STDERR.puts "Decoding: " + `date`
  STDERR.puts "lambdas = " + lambdas.inspect
  applyDecoder(command, source, output, lambdas)
  dosystem("#{mertdir}/mert-remove-dup.rb #{workdir}/run.* | sort -n > #{nbest}")
  uniq = `sort #{nbest} | uniq  | wc -l`.chomp.to_i
  uniq
end

mert = MertLib.new
mert.readRefs(reference)

prevUniq = 0
run = "000"
lambdas = ini
prevLambdas = nil
while true
  run.succ!
  STDERR.puts "################ run = #{run} ################"
  output = "#{workdir}/run.#{run}"
  if lambdas != prevLambdas
    uniq = decoding(command, source, output, lambdas, workdir, nbest)
  end
  if uniq == prevUniq || lambdas == prevLambdas
    if restart <= 0
      break
    else
      restart -= 1
      STDERR.puts "#### restart (#{restart}) ####"
      seed = []
      (0...lambdas.length).each{|i|
	seed[i] = min[i] + (max[i]-min[i])*rand
      }
      uniq = decoding(command, source, output, seed, workdir, nbest)
    end
  end
  STDERR.puts "Parameter Estimation: " + `date`
  mert.readNbests(nbest, n)
  mert.setRange(min, max)
  prevLambdas = lambdas
  case optimization
  when 'linear'
    bleu, lambdas = mert.linear(lambdas, numItr, numItr2, maxKeepBest)
  when 'uobyqa'
    bleu, lambdas =
      mert.uobyqa(lambdas, rhobeg, rhoend, iprint, maxfun, numItr,
		  maxKeepBest)
  when 'simplex'
    bleu, lambdas =
      mert.estimate(lambdas, stepSize, simplexSize, numItr, numItr2,
		    maxKeepBest)
  end

  STDERR.puts "uniq = #{uniq}"
  STDERR.puts "BLEU = #{bleu}"
  STDERR.puts "lambdas = #{lambdas.inspect}"
  prevUniq = uniq
end
STDERR.puts "uniq = #{uniq}"
STDERR.puts "BLEU = #{bleu}"
STDERR.puts "lambdas = #{lambdas.inspect}"
open("#{workdir}/lambda.txt", "w"){|fd|
  fd.puts lambdas.join(' ')
}
STDERR.puts "Done: " + `date`
