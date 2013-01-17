#coding:utf-8
import srilm_wrapper
import math

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
    
    def __init__(self, lm_directory='', vocab_file='', lm_file=None, n=3):
        """Create a LanguageModel.
        lm_directory - location of language model files
        vocab_file - vocabulary file to use
        lm_file - language model file
        n - order of model
        """
        if not self._initialised:
            self.lm_directory = lm_directory
            self.vocab_file = vocab_file
            self.lm_file = lm_file
            self.n = n
            self.load()
            self.vocab = {}
            self._initialised = True

    def load(self):
        srilm_wrapper.readVocab(self.vocab_file)
        self.model = srilm_wrapper.initLM(self.n)
        srilm_wrapper.readLM(self.model, self.lm_file)
        return

    def create_history(self, items):
        """Simple wrapper to convert a python of ints into an array of ints"""
        iarray = srilm_wrapper.new_intArray(len(items)+1)
        for i, item in enumerate(items):
            srilm_wrapper.intArray_setitem(iarray, i, item)
        srilm_wrapper.intArray_setitem(iarray, len(items), 0)
        return iarray
 
    def number_ngrams(self, size):
        """Returns the number of ngrams for a given order."""
        return srilm_wrapper.howManyNgrams(self.model, size)

    def word_id(self, word):
        """Get the word id of a given string."""
        if isinstance(word, unicode):
            strword = word.encode('utf-8')
        else:
            strword = word
        try:
            return self.vocab[word]
        except KeyError:
            #print 'index for word', word, type(word)
            i = srilm_wrapper.getIndexForWord(strword)
            self.vocab[word] = i
            return i

    def ngram(self, wid, *history):
        """Return the ngram probability (log10) of a word given history."""
        iarray = self.create_history(history)
        prob = srilm_wrapper.wordProb(self.model, wid, iarray)
        srilm_wrapper.delete_intArray(iarray)
        return prob

    def bigram_ids(self, wid1, wid2):
        return self.ngram(wid2, wid1)

    def trigram_ids(self, wid1, wid2, wid3):
        return self.ngram(wid3, wid2, wid1)

    def bigram(self, w1, w2):
        """Return the probability of a given bigram.
        Words should be strings."""
        return self.bigram_ids(self.word_id(w1),self. word_id(w2))
    
    def trigram(self, w1, w2, w3):
        """Return the probability of a given trigram.  
        Words should be strings.

        p (w3 | w2 w1)
        trigram('<s>', 'the', 'new') = p(new | <s> the)
        """
        return self.trigram_ids(self.word_id(w1), self.word_id(w2), self.word_id(w3))
    
    def sentence_probability(self, sentence):
        """Return the probability of a sentence.
        sentence - string of sentence without start and end tokens."""
        return srilm_wrapper.getSentenceProb(self.model, sentence, len(sentence.split()))

    def sentenceProbability(self, sentence):
        if not sentence:
            return 0.0
        return srilm_wrapper.getSentenceProb(self.model, sentence, len(sentence.split()))

    def tokensProbability(self, tokens):
      if not tokens:
        return 0.0

      prob = srilm_wrapper.getSentenceProb(self.model, ' '.join(tokens) , len(tokens))

      if prob < -999 or prob == 0 : prob = -999.0
      return prob

    def readNGram(self,words):
      """
      @type words: list of string
      @rtype: float
      """
      if len(words) == 0 : return 0.0
      #words = [self.word_id(w) for w in words]
      #words.reverse()

      #iarray = self.create_history(words[1:])
      prob = srilm_wrapper.getSentenceProb(self.model, ' '.join(words) , len(words))
      #srilm_wrapper.delete_intArray(iarray)

      #if prob < -999999 : prob = 0.0
      #prob = math.exp(prob)

      if prob < -99 : prob = -99.0
      return prob

if __name__ == "__main__":
    print "-- test --"
    lm = LanguageModel(lm_file="/home/raphael/ntcir10/lm/ja.full.lm",n=5)
    print lm.sentenceProbability("発生 した 石 は ない")