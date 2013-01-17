cdef extern from "srilmwrap.h":
    ctypedef struct Vocab # not true, actually a C++ object
    Vocab * new_vocab(int is_unk_word)
    void vocab_delete(Vocab *vocab)
    int vocab_index(Vocab *vocab, char *s)
    char * vocab_word(Vocab *vocab, int i)

    ctypedef struct Ngram # not true, actually a C++ object
    Ngram * new_ngram(Vocab *vocab, int order)
    void ngram_delete(Ngram *ngram)
    int ngram_read(Ngram *ngram, char *filename, int limit_vocab)
    float ngram_wordProb(Ngram *ngram, int w, int *context)
