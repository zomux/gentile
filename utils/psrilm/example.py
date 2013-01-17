#!/usr/bin/env python2.4

import srilm
v = srilm.Vocab()

print v.index("foo") # should print some small number
i = v.index("foo")
print v.word(i) # should print foo

n = srilm.Ngram(v, 3)
n.read("/auto/hpc-22/dmarcu/nlg/wwang/resources/AtoE/gale/v1.0/lm/lm.SRI")

words = [v.index(x) for x in "<s> the quick brown fox jumped over the lazy dogs </s>".split()]

for i in xrange(1,len(words)): # start at 1 because you don't want prob of <s>
    print n.wordprob(words[i], words[max(0,i-2):i])
