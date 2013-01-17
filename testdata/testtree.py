from gentile.sense import SenseTree

pcfg = "( (S (SBAR (WHADVP (WRB when)) (S (NP (NP (DT the) (JJ fluid) (NN pressure)) (NP (NNP cylinder) (CD 31))) (VP (VBZ is) (VP (VBN used))))) (, ,) (NP (NN fluid)) (VP (VBZ is) (VP (ADVP (RB gradually)) (VBN applied))) (. .)) )"
dep = """advmod(used-8, when-1)
det(pressure-4, the-2)
amod(pressure-4, fluid-3)
nsubjpass(used-8, pressure-4)
dep(pressure-4, cylinder-5)
num(cylinder-5, 31-6)
auxpass(used-8, is-7)
advcl(applied-13, used-8)
nsubjpass(applied-13, fluid-10)
auxpass(applied-13, is-11)
advmod(applied-13, gradually-12)
root(ROOT-0, applied-13)"""
testtree = SenseTree(pcfg, dep)