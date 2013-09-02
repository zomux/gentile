#!/usr/bin/env ruby

done = {}
while line = gets
  id, cand, scores = line.chomp.split(" ||| ")
  key = [id, scores].join(' ')
  next if done[key]
  done[key] = true
  puts line
end
