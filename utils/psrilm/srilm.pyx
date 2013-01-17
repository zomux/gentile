# srilm.pyx
# David Chiang <chiang@isi.edu>

# Copyright (c) 2004-2006 University of Maryland. All rights
# reserved. Do not redistribute without permission from the
# author. Not for commercial use.

cimport srilmwrap

cdef extern from "stdlib.h":
   void *malloc(int size)
   void *calloc(int nelem, int size)
   void *realloc(void *buf, int size)
   void free(void *ptr)

cdef class Vocab:
    cdef srilmwrap.Vocab *vocab

    def __cinit__(self, is_unk_word):
        self.vocab = srilmwrap.new_vocab(is_unk_word)

    def __dealloc__(self):
        srilmwrap.vocab_delete(self.vocab)
        
    def word(self, int i):
        return srilmwrap.vocab_word(self.vocab, i)

    def index(self, char *s):
        return srilmwrap.vocab_index(self.vocab, s)

# temporary area
cdef int bufsize
cdef int *buf
bufsize = 5
buf = <int *>malloc(bufsize)

cdef int NONE
NONE = -1 # magic value

cdef class Ngram:
    cdef srilmwrap.Ngram *ngram
    cdef Vocab vocab
    cdef int order
    
    def __cinit__(self, Vocab vocab, int order):
        self.vocab = vocab # do this to increment reference count
        self.ngram = srilmwrap.new_ngram(vocab.vocab, order)
        self.order = order

    def __init__(self, vocab, order):
        pass

    def __dealloc__(self):
        srilmwrap.ngram_delete(self.ngram)

    def read(self, filename, limit_vocab=False):
        if not srilmwrap.ngram_read(self.ngram, filename, limit_vocab):
            raise IOError, "Couldn't read LM file"

    def wordprob(self, int word, context):
        global buf, bufsize
        cdef int length, i
        length = len(context)
        while length+1 > bufsize:
            bufsize = bufsize * 2
            buf = <int *>realloc(buf, bufsize*sizeof(int))
        # Fill in buffer in reverse order
        buf[length] = NONE
        for i from 0 <= i < length:
            buf[length-i-1] = context[i]
        return srilmwrap.ngram_wordProb(self.ngram, word, buf)
