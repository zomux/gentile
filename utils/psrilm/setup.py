from distutils.core import setup, Extension
import os.path

#srilm_prefix = "/users/chiang/pkg/srilm"
#srilm_prefix = "/home/hpc-22/dmarcu/nlg/blobs/srilm/latest"
srilm_prefix = "/Volumes/DATA/Library/srilm"
srilm_include = srilm_prefix + "/include"
srilm_lib = srilm_prefix + "/lib/i686-m64_c"

srilm_module = Extension('srilm',
                         sources = ['srilm.c', 'srilmwrap.cc'],
                         include_dirs = [srilm_include],
                         libraries = ['oolm', 'dstruct', 'misc'],
                         library_dirs = [srilm_lib],
                         extra_compile_args = ['-DUSE_SARRAY', '-DUSE_SARRAY_TRIE', '-DUSE_SARRAY_MAP2'])

setup (name = 'SRI-LM',
              version = '1.0',
              description = 'Interface to SRI-LM',
              ext_modules = [srilm_module])

