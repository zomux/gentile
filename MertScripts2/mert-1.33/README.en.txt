
mert --- Minimum Error Rate Training Package for Machine Translation

							Masao Utiyama
                                                        Dec 25 2006

* Introduction

Following

    [1] Franz Josef Och. (2003) 
    Minimum Error Rate Training in Statistical Machine Translation.
    ACL-2003.

this software can be used to obtain maximum BLEU feature
weights. This software implements the algorithm suggested in
[1], UOBYQA (Powell's method) and the Simplex algorithm of
Nelder and Mead to search optimal weights.


* Requirement

    glib-2.0
    GSL (GNU Scientific Library)
    gfortran
    http://users.bigpond.net.au/amiller/uobyqa.f90


* Install

    patch uobyqa.f90 < uobyqa.f90.patch 
    gfortran -c uobyqa.f90
    ruby extconf.rb
    make
    
to compile this software. Append the current directory to PATH
and RUBYLIB in .cshrc or .bashrc.


* Example

set decoder = $HOME/Study/Decoder/bin/SMT/decoder
set command = "ruby sample/applyDecoder.rb $decoder sample/decoder.ini '-v -stack 100 -stack_S 100 -nbest 100 -atleastone -diagbeam_width 100' sample/tmp.ini"
mert.rb --source sample/en.dev.10 --reference sample/ja.dev.10 --workdir work --command "$command" --min "0.0001 -1 -1 0.0001 0.0001 0.0001 0.0001 -1" --max "1 1 1 1 1 1 1 1" --ini "0.1 -0.3 -0.2 0.1 0.1 0.1 0.1 0.1"

cat work/lambda.txt 
0.67270179191285 -0.856588945979106 0.00908125619411177 0.23251714856763 1.0 0.0001 0.0001 0.249727054023162


* Usage

    mert.rb --source SOURCE_FILE --reference REFERENCE_FILE --workdir WORK_DIR --ini "lambda1 lambda2 ... lambdaN" --min "lambda1 lambda2 ... lambdaN" --max "lambda1 lambda2 ... lambdaN" --command COMMAND


** Options (required)

--source SOURCE_FILE

    The source text. One sentence per line.

--reference REFERENCE_FILE

    The reference translation of the source text. One sentence per line.
    Each line is a reference translation of the corresponding line in
    the source text.

--workdir WORK_DIR

    The working directory that is used by mert.rb. This directory
    should not exist before running mert.rb.
    WORK_DIR/run.i contains the n-best translations in the i-th iteration.
    WORK_DIR/nbest.all contains the output of `sort -n WORK_DIR/run.*`
    WORK_DIR/lambda.txt is the estimated weights of the features.

--ini "lambda1 lambda2 ... lambdaN" 

    The initial values of the feature weights. N is the number of features.

--min "lambda1 lambda2 ... lambdaN" 

    The minimum values of the feature weights.

--max "lambda1 lambda2 ... lambdaN" 

    The maximum values of the feature weights.

    Note that min and max specify the ranges of the initial feature
    weights of random seeds. The final feature weights may be out of
    these ranges.

--command COMMAND

    mert.rb executes

        COMMAND SOURCE_FILE WORK_DIR/run.i 'lambda1 lambda2 ... lambdaN'

    at the i-th iteration. COMMAND read the source text from SOURCE_FILE
    and output the nbests to WORK_DIR/run.i using
    'lambda1 lambda2 ... lambdaN' as the feature weights. The format of
    nbests is

        sentence_id ||| translation candidate ||| score1 score2 ... scoreN

    sentence_id starts from 0. sentence_id 0 corresponds to the first
    sentence in SOURCE_FILE.

** Options (optional)


--optimization OPT (default=linear)

  OPT is one of linear, uobyqa, simplex. The 'linear' algorithm
is an implementation of the optimization method suggested in
[1]. It follows the algorithm used in the Phrase model training
code available from
http://www.statmt.org/wmt06/shared-task/baseline.html.

  It seems that --min & --max are very important for getting
better parameter values. 'uobyqa' seems to be more stable than
'linear' with respect to random seeds. Try both methods and
choose better one if you have time.


--numItr NUMBER (default=100)

  Maximum number of seeds used in optimization


--maxKeepBest NUMBER (default=50)

  Quit if a bestBLEU keeps best value maxKeepBest times.


-n NUMBER (default=4)

  The maximum length n-gram used in BLEU calculation.    


* Tips in implementation

This software uses the suffix arrays of candidate and reference
translations to count the duplication of n-grams.

The piecewise linear function described in [1] corresponds to
the upper envelope. The upper envelope corresponds to the lower
hull in the dual space. The lower hull can be calculated in 
O(n log n).


* Copying

Copyright (C) 2006,2007 Masao Utiyama <mutiyama@nict.go.jp>

This program is free software; you can redistribute it
and/or modify it under the terms of the GNU General
Public License as published by the Free Software
Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General
Public License along with this program; if not, write
to the Free Software Foundation, Inc., 59 Temple Place,
Suite 330, Boston, MA 02111-1307 USA
