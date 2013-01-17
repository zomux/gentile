#coding:utf-8
import kenlm

class Borg(object):
    """From the 2nd edition of the Python cookbook.
       Ensures that all instances share the same state and behaviour.
    """
    _shared_state={}
    def __new__(cls, *a, **k):
        obj = object.__new__(cls, *a, **k)
        obj.__dict__ = cls._shared_state
        return obj

class LanguageModel(Borg):
    
    _initialised = False
    
    def __init__(self, lm_file=None, n=5):
        """Create a LanguageModel.
        lm_file - file name of language model without extension
        n - order of model
        """
        if not self._initialised:
            self.pathFile = lm_file
            self.n = n
            self.model = None
            self.load()
            self._initialised = True

    def load(self):
        self.model = kenlm.LanguageModel(self.pathFile)

    def tokensProbability(self, tokens):
      if not tokens:
        return 0.0

      # HACK 2012/10/25
      prob = self.model.simpleScore(' '.join(tokens))
      # prob = self.model.score(' '.join(tokens))

      if prob < -999 or prob == 0 : prob = -999.0
      return prob

    def sentenceProbability(self, sentence):
      if not sentence: return 0.0

      prob = self.model.score(sentence)

      if prob < -999 or prob == 0 : prob = -999.0
      return prob

    def readNGram(self,words):
      """
      @type words: list of string
      @rtype: float
      """
      if len(words) == 0 : return 0.0

      prob = self.model.score(' '.join(words))

      if prob < -999 or prob == 0 : prob = -999.0
      return prob

if __name__ == "__main__":
    print "-- test --"
    lm = LanguageModel(lm_file="/home/raphael/ntcir10/lm/ja.full.binary",n=5)
    print lm.sentenceProbability("発生 した 石 は ない")
