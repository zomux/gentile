#ifndef SRILMWRAP_H
#define SRILMWRAP_H

#ifdef __cplusplus
  extern "C" {
#else
    typedef struct Ngram Ngram; /* dummy type to stand in for class */
    typedef struct Vocab Vocab; /* dummy type to stand in for class */
#endif

Vocab * new_vocab(int is_unk_word);
void vocab_delete(Vocab *vocab);
int vocab_index(Vocab *vocab, const char *s);
const char * vocab_word(Vocab *vocab, int i);
Ngram * new_ngram(Vocab *vocab, int order);
void ngram_delete(Ngram * ngram);
int ngram_read(Ngram * ngram, const char *filename, int limit_vocab);
float ngram_wordProb(Ngram * ngram, unsigned w, unsigned *context);

#ifdef __cplusplus
  }
#endif

#endif

