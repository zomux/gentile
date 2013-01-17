#coding:utf-8
from srilm import LanguageModel
lm = LanguageModel(lm_file="../../data100/500k.ja.lm.utf8", n=5)

print lm.readNGram(["私","が"])
print lm.readNGram(["私","く"])