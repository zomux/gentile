#!/bin/sh

command="ruby -Ke /home/norimatsu/research/demotic/scripts/mertrbinner.rb /home/norimatsu/tools/pdecoder/pdecoder/myhiero model/demotic/demotic.ini '-v -stack 50 -stack_S 50 -atleastone -cubic 1.0 -cubic_S 1.0 -nbest 50'"
LC_ALL=C mert.rb --source /depot10/norimatsu/demotic_corpus/final_dat/ej_dev.en --reference /depot10/norimatsu/demotic_corpus/final_dat/ej_dev.ja --workdir myhierotune --command "$command" --min "0.0001 -1 -1 0.0001 0.0001 0.0001 0.0001 -1" --max "1 1 1 1 1 1 1 1" --ini "0.1 -0.3 -0.2 0.1 0.1 0.1 0.1 0.1"

