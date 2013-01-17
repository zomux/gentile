#include "Prob.h"
#include "Ngram.h"
#include "Vocab.h"

#include "srilmwrap.h"

#include <iostream>

Vocab * new_vocab(int is_unk_word) {
  Vocab *v = new Vocab;
  v->is_unk_word = is_unk_word;
  return v;
}

void vocab_delete(Vocab *vocab) {
  delete vocab;
}

int vocab_index(Vocab *vocab, const char *s) {
  return vocab->addWord((VocabString)s);
}

const char * vocab_word(Vocab *vocab, int i) {
  return vocab->getWord((VocabIndex)i);
}

Ngram * new_ngram(Vocab *vocab, int order) {
  return new Ngram(*vocab, order);
}

void ngram_delete(Ngram * ngram) {
  cerr << "Warning: leaking Ngram instance instead of deleting\n";
  //delete ngram;
}

int ngram_read(Ngram * ngram, const char *filename, int limit_vocab) {
  File file(filename, "r", 0);
  if (!file) {
    return 0;
  }
  return ngram->read(file, limit_vocab);
}

float ngram_wordProb(Ngram * ngram, unsigned w, unsigned *context) {
  return (float)ngram->wordProb(w, context);
}
