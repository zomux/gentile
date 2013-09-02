#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <glib.h>
#include <ruby.h>
#include <gsl/gsl_math.h>
#include <gsl/gsl_sum.h>
#include <gsl/gsl_multimin.h>

#define DEBUG 0
#define DEBUG2 0

typedef struct {
  int numSnts;
  int refsLen;
  int *offset;		/* offset[i] = i-th ref start from here
			   offset[numSnts] = sum_snt (sntlen + 1) */
  GQuark *text;		/* text[offset[i]+j] = j-th w. of i-th s. (0<=j<sl)
			   text[offset[i]+sl] = -1  (sl=sntlen) */
  int *suf;		/* suf[offset[i]+j] = suffix of i-th s (0<=j<sl)
			   suf[offset[i]+sl] = -1 */
} Refs;

typedef struct {
  int length;		/* length of the candidate translation (in words) */
  int *correct;		/* correct[i] = number of correct (i+1)-gram */
  int *total;		/* total[i] = number of running (i+1)-gram */
  double *score;	/* score[i] = score of i-th feature */
} Candidate;

typedef struct {
  double x;
  double y;
  int cand;
} Point;

typedef struct {
  double th;
  int dCorrect[10];	/* 10 is large enough */
  int dTotal[10];
  int dLength;
} Threshold;

typedef struct {
  int numSnts;		/* number of sentences */
  int refsLen;		/* \sum_ref length(ref) */
  int N;		/* maximum n (usually 4)*/
  int numFeatures;	/* number of features (usually 8)*/
  int numCandidates;	/* \sum_trans no. of candidates of trans */
  int *offset;		/* offset[i] = start of i-th translation
			   offfset[numSnts] = numCandidates (guard) */
  Candidate *candidate;	/* candidate[offset[i]+j] = j-th candidate of
			   i-th translation */

  double *lambdaMin;	/* lambdaMin[i] = minimum value of lambda[i] */
  double *lambdaMax;	/* lambdaMax[i] = maximum value of lambda[i] */

  /* for optimization */
  Point *point;		/* point[i] = i-th point in the dual space */
  int numPoints;
  Threshold *threshold;	/* threshold[i] = i-th threshold */
  int numThresholds;
  int *start;		/* start[i] = left most candidate of snt. i*/
} Nbest;

typedef struct {
  Refs *refs;
  Nbest *nbest;
} Mert;

#define GET_Mert(obj,dat) Data_Get_Struct(obj, Mert, dat)

static GQuark SNTDEL = -1;
static GQuark CANDDEL = -2;
static GQuark *textptr;
static Nbest *tmpNbest;

extern void __powell_optimize__uobyqa(int *n, double *x, double *rhobeg, double *rhoend, int *iprint, int *maxfun);

void
refsFree(Refs *refs)
{
  if(refs){
    g_free(refs->offset);
    g_free(refs->text);
    g_free(refs->suf);
    g_free(refs);
  }
}

void
nbestFree(Nbest *nbest)
{
  int i;
  if(nbest){
    g_free(nbest->offset);
    for(i=0; i<nbest->numCandidates; i++){
      g_free(nbest->candidate[i].correct);
      g_free(nbest->candidate[i].total);
      g_free(nbest->candidate[i].score);
    }
    g_free(nbest->candidate);
    g_free(nbest->lambdaMin);
    g_free(nbest->lambdaMax);
    g_free(nbest->point);
    g_free(nbest->threshold);
    g_free(nbest->start);
    g_free(nbest);
  }
}

Mert *
mertNew()
{
  Mert *mert = g_new(Mert, 1);
  mert->refs = g_new0(Refs, 1);
  mert->nbest = g_new0(Nbest, 1);
  return mert;
}

void
mertFree(Mert *mert)
{
  if(mert){
    refsFree(mert->refs);
    nbestFree(mert->nbest);
    g_free(mert);
  }
}

static VALUE
rb_mert_new(VALUE klass)
{
  Mert *mert = mertNew();
  return Data_Wrap_Struct(klass, 0, mertFree, mert);
}

int
suffix_compare(int *a, int *b)
{
  GQuark *texta = textptr + *a;
  GQuark *textb = textptr + *b;
  while(1){
    if(texta[0] < textb[0]){
      return -1;
    }else if(texta[0] > textb[0]){
      return +1;
    }else{
      texta++;
      textb++;
    }
  }
  return 0;
}

static VALUE
rb_mert_readrefs(VALUE klass, VALUE rb_path)
{
  Mert *mert;
  Refs *refs;
  char *path = StringValuePtr(rb_path), *buf = NULL, **strv;
  FILE *fp = fopen(path, "r");
	size_t bufsize = 0;
  int i, numTokens = 0, windex, numSnts = 0, wid, s, len;
  GArray *offset = g_array_new(FALSE, FALSE, sizeof(int));
  GArray *text = g_array_new(FALSE, FALSE, sizeof(GQuark));
  GArray *suf = g_array_new(FALSE, FALSE, sizeof(int));
  int *sufptr;
  
  GET_Mert(klass, mert);
  refs = mert->refs;
  g_assert(fp!=NULL);
  
  fprintf(stderr, "Reading reference: %s ...\n", path);
  g_array_append_val(offset, numTokens);
  while(getline(&buf, &bufsize, fp) != -1){
    g_strdelimit(buf, " \t\n", ' ');
    strv = g_strsplit(buf, " ", 0);
    windex = 0;
    for(i=0; strv[i]; i++){
      if(strlen(strv[i])>0){
	wid = g_quark_from_string(strv[i]);
	g_array_append_val(text, wid);
	g_array_append_val(suf, windex);
	windex++;
	numTokens++;
      }
    }
    g_array_append_val(text, SNTDEL);
    g_array_append_val(suf, SNTDEL);
    numTokens++;
    g_array_append_val(offset, numTokens);
    g_strfreev(strv);
    numSnts++;
  }
  
  refs->numSnts = numSnts;
  refs->refsLen = numTokens - numSnts;
  refs->offset = (int*) g_array_free(offset, FALSE);
  refs->text = (GQuark*) g_array_free(text, FALSE);
  refs->suf = (int*) g_array_free(suf, FALSE);

  for(s=0; s<numSnts; s++){
    sufptr = refs->suf + refs->offset[s];
    textptr = refs->text + refs->offset[s];
    len = refs->offset[s+1] - refs->offset[s] - 1;
    qsort(sufptr, len, sizeof(int),
	  (int (*)(const void *,const void *))suffix_compare);
  }
  
  fclose(fp);
  g_free(buf);

  fprintf(stderr, "numSnts = %d\n", refs->numSnts);
  fprintf(stderr, "refsLen = %d\n", refs->refsLen);

  return Qnil;
}

static void
refsPrint(Refs *refs)
{
  int s,w,len,i,j;
  int *sufptr;
  
  printf("==== refs ====\n");
  printf("numSnts = %d\n", refs->numSnts);
  printf("refsLen = %d\n", refs->refsLen);
  for(s=0; s<refs->numSnts; s++){
    len = refs->offset[s+1] - refs->offset[s] - 1;
    printf("**** s=%d, len=%d ****\n", s, len);
    i = 0;
    for(w=refs->offset[s]; w<refs->offset[s+1]; w++){
      printf("%d, %d: %d %d %s\n", i,
	     w, refs->suf[w], refs->text[w],
	     g_quark_to_string(refs->text[w]));
      i++;
    }
    printf("================\n");
    i = 0;
    textptr = refs->text + refs->offset[s];
    sufptr = refs->suf + refs->offset[s];
    for(i=0; i<len; i++){
      printf("%d: ", i);
      for(j=sufptr[i]; j<len; j++){
	printf("%d ", textptr[j]);
      }
      printf("\n");
    }
  }
}

static VALUE
rb_mert_printrefs(VALUE klass)
{
  Mert *mert;
  GET_Mert(klass, mert);
  refsPrint(mert->refs);
  return Qnil;
}

int
nbestCountDup(GQuark *ref, int *refsuf, int reflen,
	      GQuark *cand, int *candsuf, int candlen, int n)
{
  int i;
  int refindex, candindex, cmp, r, c, correct;
  
  correct = 0;
  refindex = 0;
  candindex = 0;
  while(refindex < reflen && candindex < candlen){
    cmp = 0;
    for(i=0; i<n; i++){
      r = ref[refsuf[refindex]+i];
      c = cand[candsuf[candindex]+i];
      if(r < c){
	cmp = -1;
	break;
      }else if(r > c){
	cmp = +1;
	break;
      }
    }
    if(cmp == -1){
      refindex++;
    }else if(cmp == +1){
      candindex++;
    }else{
      correct++;
      refindex++;
      candindex++;
    }
  }
  return correct;
}

void
mertReadNbests(Mert *mert, char *path, int N)
{
  Refs *refs = mert->refs;
  Nbest *nbest;
  char *buf = NULL, **strv, **strv2;
	size_t bufsize=0;
  int prev, sid, i, wid, suf[4096], windex, len, n, numFeatures;
  int numCandidates=0;
  GQuark text[4096];
  FILE *fp = fopen(path, "r");
  double score[4096];
  Candidate *cand;
  GArray *candidate = g_array_new(FALSE, FALSE, sizeof(Candidate));
  int maxCandidates;

  if(mert->nbest){
    nbestFree(mert->nbest);
    mert->nbest = g_new0(Nbest, 1);
  }
  nbest = mert->nbest;
  
  nbest->numSnts = refs->numSnts;
  nbest->refsLen = refs->refsLen;
  nbest->N = N;
  nbest->numFeatures = 0;
  nbest->numCandidates = 0;
  nbest->offset = g_new(int, nbest->numSnts+1);
  
  fprintf(stderr, "Up to %d-gram\n", N);
  fprintf(stderr, "Reading nbests: %s ...\n", path);
  prev=-1;
  while(getline(&buf, &bufsize, fp) != -1){
    buf[strlen(buf)-1] = '\0';
    strv = g_strsplit(buf, " ||| ", 0);
    if(!strv[0] || !strv[1] || !strv[2]){
      fprintf(stderr, "Format error: %s", buf);
      exit(1);
    }else{
      sid = g_ascii_strtod(strv[0], NULL);
      g_assert(sid == prev || sid == prev+1);
      if(sid == prev+1){
	nbest->offset[sid] = numCandidates;
      }
      
      strv2 = g_strsplit(strv[1], " ", 0);
      windex = 0;
      for(i=0; strv2[i]; i++){
	if(strlen(strv2[i])>0){
	  wid = g_quark_from_string(strv2[i]);
	  text[windex] = wid;
	  suf[windex] = windex;
	  windex++;
	}
      }
      g_strfreev(strv2);
      text[windex] = CANDDEL;
      suf[windex] = CANDDEL;
      len = windex;
      
      textptr = text;
      qsort(suf, len, sizeof(int),
	    (int (*)(const void *,const void *))suffix_compare);
      
      cand = g_new(Candidate, 1);
      cand->length = len;
      cand->correct = g_new(int, N);
      cand->total = g_new(int, N);
      for(n=1; n<=N; n++){
	cand->total[n-1] = len - n + 1;
	cand->correct[n-1] = 
	  nbestCountDup(refs->text + refs->offset[sid],
			refs->suf + refs->offset[sid],
			refs->offset[sid+1] - refs->offset[sid] - 1,
			text, suf, len, n);
      }
      
      strv2 = g_strsplit(strv[2], " ", 0);
      numFeatures = 0;
      for(i=0; strv2[i]; i++){
	if(strlen(strv2[i])>0){
	  score[numFeatures] = g_ascii_strtod(strv2[i], NULL);
	  numFeatures++;
	}
      }
      g_strfreev(strv2);
      if(nbest->numFeatures==0){
	nbest->numFeatures = numFeatures;
      }else{
	g_assert(nbest->numFeatures == numFeatures);
      }
      cand->score = g_new(double, numFeatures);
      for(i=0; i<numFeatures; i++){
	cand->score[i] = score[i];
      }
      g_array_append_val(candidate, *cand);
      numCandidates++;
      prev=sid;
    }
    g_strfreev(strv);
  }
  g_assert(sid == nbest->numSnts-1);
  
  nbest->numCandidates = numCandidates;
  nbest->offset[nbest->numSnts] = numCandidates;
  nbest->candidate = (Candidate*)g_array_free(candidate, FALSE);
  nbest->lambdaMin = g_new(double, nbest->numFeatures);
  nbest->lambdaMax = g_new(double, nbest->numFeatures);
  for(i=0; i<nbest->numFeatures; i++){
    nbest->lambdaMin[i] = -1.0;
    nbest->lambdaMax[i] = 1.0;
  }
  
  fprintf(stderr, "numFeatures = %d\n", nbest->numFeatures);
  fprintf(stderr, "numCandidates = %d\n", nbest->numCandidates);

  /* data structure for optimization */
  maxCandidates = 0;
  for(i=0; i<nbest->numSnts; i++){
    numCandidates = nbest->offset[i+1] - nbest->offset[i];
    if(numCandidates > maxCandidates){
      maxCandidates = numCandidates;
    }
  }
  nbest->point = g_new(Point, maxCandidates+1);
  nbest->threshold = g_new(Threshold, nbest->numCandidates+1); /* add guard */
  nbest->start = g_new(int, nbest->numSnts);
  fprintf(stderr, "maxCandidates=%d\n", maxCandidates);

  fclose(fp);
}

static VALUE
rb_mert_readnbests(VALUE klass, VALUE rb_path, VALUE rb_n)
{
  Mert *mert;
  GET_Mert(klass, mert);
  mertReadNbests(mert, StringValuePtr(rb_path), NUM2INT(rb_n));
  return Qnil;
}

void
nbestPrint(Nbest *nbest)
{
  int s, c,i;
  Candidate *cand;

  printf("**************** nbest ****************\n");
  printf("numSnts = %d\n", nbest->numSnts);
  printf("refsLen = %d\n", nbest->refsLen);
  printf("N = %d\n", nbest->N);
  printf("numFeatures = %d\n", nbest->numFeatures);
  printf("numCandidates = %d\n", nbest->numCandidates);

  for(s=0; s<nbest->numSnts; s++){
    printf("**** sentence=%d ****\n", s);
    for(c=nbest->offset[s]; c<nbest->offset[s+1]; c++){
      cand = nbest->candidate + c;
      printf("==== c=%d ====\n", c);
      printf("length=%d\n", cand->length);
      printf("correct=");
      for(i=0; i<nbest->N; i++){
	printf("%d ", cand->correct[i]);
      }
      printf("\ntotal=");
      for(i=0; i<nbest->N; i++){
	printf("%d ", cand->total[i]);
      }
      printf("\nscore=");
      for(i=0; i<nbest->numFeatures; i++){
	printf("%f ", cand->score[i]);
      }
      printf("\n");
    }
  }

  for(i=0; i<nbest->numFeatures; i++){
    printf("%d: min=%e, max=%e\n",
	   i, nbest->lambdaMin[i], nbest->lambdaMax[i]);
  }

}

void
nbestAdjustRange(Nbest *nbest, double *lambda)
{
  int i;

  return;			/* not adjust */

  for(i=0; i<nbest->numFeatures; i++){
    if(lambda[i] < nbest->lambdaMin[i]){
      lambda[i] = nbest->lambdaMin[i];
    }else if(nbest->lambdaMax[i] < lambda[i]){
      lambda[i] = nbest->lambdaMax[i];
    }
  }
}

int 
nbestBestCandidate(Nbest *nbest, double *lambda, int s)
{
  int c, i, bestCandidate;
  double score, bestScore=-DBL_MAX;
  Candidate *cand;

  for(c=nbest->offset[s]; c<nbest->offset[s+1]; c++){
    cand = nbest->candidate + c;
    score = 0;
    for(i=0; i<nbest->numFeatures; i++){
      score += cand->score[i] * lambda[i];
    }
    if(score > bestScore){
      bestScore = score;
      bestCandidate = c;
    }
  }
  return bestCandidate;
}

double
calBLEU(Nbest *nbest, int *correct, int *total, int length)
{
  int i;
  double bp, prec, bleu;
  
  if(length < nbest->refsLen){
    bp = exp(1 - (float)nbest->refsLen/length);
  }else{
    bp = 1.0;
  }
  
  prec = 0;
  for(i=0; i<nbest->N; i++){
    if(correct[i]==0){
      return 0;
    }else{
      prec += log((float)correct[i]/total[i]);
    }
  }
  
  bleu = bp * exp(prec/nbest->N);

  return bleu;
}

double
nbestBLEU(Nbest *nbest, double *lambda)
{
  int s,c,i;
  int correct[nbest->N];
  int total[nbest->N];
  int length=0;
  Candidate *cand;
  
  nbestAdjustRange(nbest, lambda);

  for(i=0; i<nbest->N; i++){
    correct[i] = total[i] = 0;
  }
  
  for(s=0; s<nbest->numSnts; s++){
    c = nbestBestCandidate(nbest, lambda, s);
    cand = nbest->candidate + c;
    for(i=0; i<nbest->N; i++){
      correct[i] += cand->correct[i];
      total[i] += cand->total[i];
    }
    length += cand->length;
  }
  
  return calBLEU(nbest, correct, total, length);
}

double
nbestInvBLEU(const gsl_vector *x, void *params)
{
  Nbest *nbest = (Nbest*)params;
  double lambda[((Nbest*)params)->numFeatures];
  double bleu;
  int i;

  for(i=0; i<nbest->numFeatures; i++){
    lambda[i] = gsl_vector_get(x, i);
  }

  bleu = nbestBLEU(nbest, lambda);
  
  return (1-bleu);
}

double 
nbestEstimate(Nbest *nbest, double *lambda,
	      double stepSize, double simplexSize, int numItr2)
{
  size_t np = nbest->numFeatures;
  const gsl_multimin_fminimizer_type *T =
    gsl_multimin_fminimizer_nmsimplex;
  gsl_multimin_fminimizer *s=NULL;
  gsl_vector *ss, *x;
  gsl_multimin_function minex_func;
  size_t iter=0, i;
  int status;
  double size;

  if(DEBUG2){fprintf(stderr, "**************** Estimation  ****************\n");}

  /* Initialize vertex size vector and set all step sizes to 0.1 */
  ss = gsl_vector_alloc(np);
  gsl_vector_set_all(ss, stepSize);
  /* Starting point */
  x = gsl_vector_alloc(np);
  for(i=0; i<np; i++){
    if(DEBUG2){
      fprintf(stderr, "lambda[%zd]=%f, min[%zd]=%f, max[%zd]=%f\n", i,
	      lambda[i], i, nbest->lambdaMin[i], i, nbest->lambdaMax[i]);
    }
    gsl_vector_set(x, i, lambda[i]);
  }
  
  /* Initialize method and iterate */
  minex_func.f = &nbestInvBLEU;
  minex_func.n = np;
  minex_func.params = (void *)nbest;
  
  s = gsl_multimin_fminimizer_alloc(T, np);
  gsl_multimin_fminimizer_set(s, &minex_func, x, ss);
  if(DEBUG2){
    fprintf(stderr, "stepSize=%f, simplexSize=%f\n", stepSize, simplexSize);
    fprintf(stderr, "  ITR     BLEU    SIZE  LAMBDA\n");
  }
  do {
    iter++;
    status = gsl_multimin_fminimizer_iterate(s);
    if(status)break;
    for(i=0; i<np; i++){
      lambda[i] = gsl_vector_get(s->x, i);
    }
    nbestAdjustRange(nbest, lambda);

    size = gsl_multimin_fminimizer_size(s);
    status = gsl_multimin_test_size(size, simplexSize);

    if(DEBUG2){
      if(status == GSL_SUCCESS){
	fprintf(stderr, "converged to minimum at\n");
      }
      if(iter%10==0){
	fprintf(stderr, "%5zd ", iter);
	fprintf(stderr, "%.6f %.6f ", (1 - s->fval), size);
	for(i=0; i<np; i++){fprintf(stderr, "%.6f ", lambda[i]);}
	fprintf(stderr, "\n");
      }
    }
  } while (status == GSL_CONTINUE && iter < numItr2);
  
  gsl_vector_free(x);
  gsl_vector_free(ss);
  gsl_multimin_fminimizer_free(s);
  
  nbestAdjustRange(nbest, lambda);
  
  return (1 - s->fval);
}

static VALUE
rb_mert_printnbests(VALUE klass)
{
  Mert *mert;
  GET_Mert(klass, mert);
  nbestPrint(mert->nbest);
  return Qnil;
}


static VALUE
rb_mert_set_range(VALUE klass, VALUE rb_min, VALUE rb_max)
{
  Mert *mert;
  Nbest *nbest;
  int i;

  GET_Mert(klass, mert);
  nbest = mert->nbest;
  
  g_assert(nbest->numFeatures == RARRAY(rb_min)->len);
  g_assert(nbest->numFeatures == RARRAY(rb_max)->len);

  for(i=0; i<nbest->numFeatures; i++){
    nbest->lambdaMin[i] = NUM2DBL(RARRAY(rb_min)->ptr[i]);
    nbest->lambdaMax[i] = NUM2DBL(RARRAY(rb_max)->ptr[i]);
  }
  
  return Qnil;
}

static VALUE
rb_mert_bleu(VALUE klass, VALUE rb_lambda)
{
  Mert *mert;
  Nbest *nbest;
  int i;
  double lambda[RARRAY(rb_lambda)->len];
  
  GET_Mert(klass, mert);
  nbest = mert->nbest;

  g_assert(nbest->numFeatures == RARRAY(rb_lambda)->len);

  for(i=0; i<nbest->numFeatures; i++){
    lambda[i] = NUM2DBL(RARRAY(rb_lambda)->ptr[i]);
  }

  return rb_float_new(nbestBLEU(nbest, lambda));
}

static void
printArray(double *array, int n, char *label)
{
  int i;
  fprintf(stderr, "%s= ", label);
  for(i=0; i<n; i++){
    fprintf(stderr, "%f ", array[i]);
  }
  fprintf(stderr, "\n");
}

static VALUE
rb_mert_estimate(VALUE klass, VALUE rb_lambda, VALUE rb_stepSize,
		 VALUE rb_simplexSize, VALUE rb_numItr, VALUE rb_numItr2, VALUE rb_maxKeepBest)
{
  Mert *mert;
  Nbest *nbest;
  int i, itr, numItr = NUM2INT(rb_numItr), numItr2=NUM2INT(rb_numItr2);
  double lambda[RARRAY(rb_lambda)->len], bleu, ini[RARRAY(rb_lambda)->len];
  double bestLambda[RARRAY(rb_lambda)->len], bestBLEU=0;
  double stepSize = NUM2DBL(rb_stepSize);
  double simplexSize = NUM2DBL(rb_simplexSize);
  int maxKeepBest=NUM2INT(rb_maxKeepBest), keepBest=0;
  VALUE rb_bestLambda = rb_ary_new();
  
  GET_Mert(klass, mert);
  nbest = mert->nbest;
  g_assert(nbest->numFeatures == RARRAY(rb_lambda)->len);

  for(i=0; i<nbest->numFeatures; i++){
    lambda[i] = ini[i] = NUM2DBL(RARRAY(rb_lambda)->ptr[i]);
  }

  fprintf(stderr, "numItr=%d, numItr2=%d, maxKeepBest=%d\n", numItr, numItr2, maxKeepBest);
  for(itr=0; itr<numItr && keepBest<maxKeepBest; itr++){
    fprintf(stderr, "**** itr=%d ****\n", itr+1);
    printArray(lambda, nbest->numFeatures, " lambdaBeg ");
    bleu = nbestEstimate(nbest, lambda, stepSize,
			 simplexSize, numItr2);
    if(bleu >= bestBLEU){
      bestBLEU = bleu;
      for(i=0; i<nbest->numFeatures; i++){bestLambda[i] = lambda[i];}
      keepBest=0;
    }else{
      keepBest++;
    }
    printArray(lambda, nbest->numFeatures, " lambdaEnd ");
    fprintf(stderr, "bleu=%f, bestBLEU=%f, keepBest=%d\n",
	    bleu, bestBLEU, keepBest);
    printArray(bestLambda, nbest->numFeatures, "bestLambda ");
    for(i=0; i<nbest->numFeatures; i++){
      lambda[i] = nbest->lambdaMin[i] +
	((nbest->lambdaMax[i] - nbest->lambdaMin[i])*rand())/RAND_MAX;
    }
  }

  for(i=0; i<nbest->numFeatures; i++){
    rb_ary_push(rb_bestLambda, rb_float_new(bestLambda[i]));
  }

  return rb_ary_new3(2, rb_float_new(bestBLEU), rb_bestLambda);
}

void
calfun_(int *n, double *x, double *invBleu)
{
  double lambda[tmpNbest->numFeatures];
  int i;
  for(i=0; i<tmpNbest->numFeatures; i++){
    lambda[i] = x[i];		/* protect x from modification */
  }
  *invBleu = 1 - nbestBLEU(tmpNbest, lambda);
}

static VALUE
rb_mert_uobyqa(VALUE klass, VALUE rb_lambda, VALUE rb_rhobeg,
	       VALUE rb_rhoend, VALUE rb_iprint,
	       VALUE rb_maxfun, VALUE rb_numItr, VALUE rb_maxKeepBest)
{
  Mert *mert;
  Nbest *nbest;
  double rhobeg = NUM2DBL(rb_rhobeg), rhoend = NUM2DBL(rb_rhoend);
  int iprint = NUM2INT(rb_iprint),  maxfun = NUM2INT(rb_maxfun), i;
  double lambda[RARRAY(rb_lambda)->len], bleu, bestBLEU=0;
  double bestLambda[RARRAY(rb_lambda)->len];
  int numItr = NUM2INT(rb_numItr), itr;
  int maxKeepBest=NUM2INT(rb_maxKeepBest), keepBest=0;
  VALUE rb_bestLambda = rb_ary_new();
  
  GET_Mert(klass, mert);
  nbest = mert->nbest;
  g_assert(nbest->numFeatures == RARRAY(rb_lambda)->len);
  for(i=0; i<nbest->numFeatures; i++){
    lambda[i] = NUM2DBL(RARRAY(rb_lambda)->ptr[i]);
  }
  fprintf(stderr,"rhobeg=%f, rhoend=%f, iprint=%d, maxfun=%d, numItr=%d, maxKeepBest=%d\n", rhobeg, rhoend, iprint, maxfun, numItr, maxKeepBest);
  printArray(nbest->lambdaMin, nbest->numFeatures, "min");
  printArray(nbest->lambdaMax, nbest->numFeatures, "max");
  
  tmpNbest = nbest;
  for(itr=0; itr<numItr && keepBest<maxKeepBest; itr++){
    fprintf(stderr, "**** itr=%d ****\n", itr+1);
    printArray(lambda, nbest->numFeatures, " lambdaBeg ");
    __powell_optimize__uobyqa(&(nbest->numFeatures), lambda,
			      &rhobeg, &rhoend, &iprint, &maxfun);
    bleu = nbestBLEU(nbest, lambda);
    if(bleu > bestBLEU){
      bestBLEU = bleu;
      for(i=0; i<nbest->numFeatures; i++){bestLambda[i] = lambda[i];}
      keepBest=0;
    }else{
      keepBest++;
    }
    printArray(lambda, nbest->numFeatures, " lambdaEnd ");
    fprintf(stderr, "bleu=%f, bestBLEU=%f, keepBest=%d\n",
	    bleu, bestBLEU, keepBest);
    printArray(bestLambda, nbest->numFeatures, "bestLambda ");
    for(i=0; i<nbest->numFeatures; i++){
      lambda[i] = nbest->lambdaMin[i] +
	((nbest->lambdaMax[i] - nbest->lambdaMin[i])*rand())/RAND_MAX;
    }
  }
  for(i=0; i<nbest->numFeatures; i++){
    rb_ary_push(rb_bestLambda, rb_float_new(bestLambda[i]));
  }
  return rb_ary_new3(2, rb_float_new(bestBLEU), rb_bestLambda);
}

/* Get Points in the dual space:
   Each candidate represents a line
   y = score[feature] x + fixed_score
   in the primary space. x is the weight of the feature and
   y is the total score of the candidate.
   This line corresponds to the point
   (score[feature], -fixed_score) in the dual space */
void
getPoints(Nbest *nbest, int s, double *lambda, int feature)
{
  int numPoints, c, i;
  Point *point;
  Candidate *cand;
  
  numPoints = 0;
  for(c=nbest->offset[s]; c<nbest->offset[s+1]; c++){ /* for cand */
    cand = nbest->candidate + c;
    point = nbest->point + numPoints;
    point->x = cand->score[feature];
    point->y = 0;
    for(i=0; i<nbest->numFeatures; i++){
      if(i!=feature){
	point->y -= cand->score[i]*lambda[i];
      }
    }
    point->cand = c;
    numPoints++;
  }
  nbest->numPoints = numPoints;
}

int
point_compare(Point *a, Point *b)
{
  if(a->x < b->x){
    return -1;
  }else if(a->x > b->x){
    return +1;
  }else if(a->y > b->y){
    return -1;
  }else if(a->y < b->y){
    return +1;
  }else{
    return 0;
  }
}

int
threshold_compare(Threshold *a, Threshold *b)
{
  if(a->th < b->th){
    return -1;
  }else if(a->th > b->th){
    return +1;
  }else{
    return 0;
  }
}

/* true if points i, j, k counterclockwise */
int
ccw(Point *i, Point *j, Point *k){
  double a = i->x - j->x,
    b = i->y - j->y,
    c = k->x - j->x,
    d = k->y - j->y;
  return (a*d <= b*c);
}

/* See 2dch.c */
void
getLowerHull(Nbest *nbest)
{
  int i, j, s, numPoints = nbest->numPoints;
  Point *point = nbest->point;
  
  qsort(point, numPoints, sizeof(Point),
	(int (*)(const void *,const void *))point_compare);

  point[numPoints].x = point[numPoints-1].x + 1; /* guard */
  s = -1;
  for(i=0; i<numPoints; i++){
    if(point[i].x == point[i+1].x){
      /*fprintf(stderr, "   skip %d,%d: (%f,%f)\n",
	i, point[i].cand, point[i].x, point[i].y);*/
      continue;
    }
    /*fprintf(stderr, "process %d,%d: (%f,%f)\n", i,
      point[i].cand, point[i].x, point[i].y);*/
    if(s>=1){
      for(j=s; j>=1 && ccw(point+i, point+j, point+j-1); j--){}
      s=j+1;
    }else{
      s++;
    }
    point[s].x = point[i].x;
    point[s].y = point[i].y;
    point[s].cand = point[i].cand;
  }
  nbest->numPoints = s+1; /* No. of points of the lower hull */
}

void
addThresholds(Nbest *nbest)
{
  Threshold *thr;
  Candidate *this, *prev;
  int i, n;
  
  for(i=1; i<nbest->numPoints; i++){
    thr = nbest->threshold + nbest->numThresholds;
    thr->th = (nbest->point[i-1].y - nbest->point[i].y)/
      (nbest->point[i-1].x - nbest->point[i].x);

    this = nbest->candidate + nbest->point[i].cand;
    prev = nbest->candidate + nbest->point[i-1].cand;
    for(n=0; n<nbest->N; n++){
      thr->dCorrect[n] = this->correct[n] - prev->correct[n];
      thr->dTotal[n] = this->total[n] - prev->total[n];
      thr->dLength = this->length - prev->length;
    }
    if(DEBUG){
      fprintf(stderr, "%d: th=%f, cand0=%d, cand1=%d\n",
	      nbest->numThresholds, thr->th,
	      nbest->point[i-1].cand, nbest->point[i].cand);
    }
    nbest->numThresholds++;
  }
}

void
findThresholdPoints(Nbest *nbest, double *lambda, int feature)
{
  int s,i;
  double th;
  Point *point = nbest->point;
  
  nbest->numThresholds=0;
  for(s=0; s<nbest->numSnts; s++){
    getPoints(nbest, s, lambda, feature);
    getLowerHull(nbest);
    nbest->start[s] = point[0].cand;
    addThresholds(nbest);
    if(DEBUG){
      fprintf(stderr, "s=%d, numPoints=%d, start=%d\n",
	      s, nbest->numPoints, nbest->start[s] - nbest->offset[s]);
      for(i=0; i<nbest->numPoints; i++){
	if(i>0){
	  th = (point[i-1].y - point[i].y)/ (point[i-1].x - point[i].x);
	}else{
	  th = -100000;
	}
	fprintf(stderr, "%d: x=%f, y=%f, c=%d (%d), th=%f\n",i,
		point[i].x, point[i].y, point[i].cand - nbest->offset[s],
		point[i].cand,th);
      }
    }
  }
  if(DEBUG){
    fprintf(stderr, "nbest->numThresholds=%d\n", nbest->numThresholds);
    fprintf(stderr, "**************** thresholds ****************\n");
    for(i=0; i<nbest->numThresholds; i++){
      fprintf(stderr, "%d: th=%f\n", i, nbest->threshold[i].th);
    }
  }
  qsort(nbest->threshold, nbest->numThresholds, sizeof(Threshold),
	(int (*)(const void *,const void *))threshold_compare);
}

double
initBLEU(Nbest *nbest, int *correct, int *total, int *length)
{
  int i,s;
  Candidate *cand;

  for(i=0; i<nbest->N; i++){
    correct[i] = total[i] = 0;
  }

  for(s=0; s<nbest->numSnts; s++){
    cand = nbest->candidate + nbest->start[s];
    for(i=0; i<nbest->N; i++){
      correct[i] += cand->correct[i];
      total[i] += cand->total[i];
    }
    *length += cand->length;
  }
  
  return calBLEU(nbest, correct, total, *length);
}

void
findMaxBLEU(Nbest *nbest, double *weight)
{
  int N=nbest->N, numThresholds=nbest->numThresholds;
  int correct[N], total[N], length=0, t, i;
  double maxBLEU, bleu;
  Threshold *thr = nbest->threshold;
  
  thr[numThresholds].th = thr[numThresholds-1].th + 0.1;
  
  maxBLEU = initBLEU(nbest, correct, total, &length);
  *weight = thr[0].th - 0.1;
  
  for(t=0; t<numThresholds; t++){
    for(i=0; i<N; i++){
      correct[i] += thr[t].dCorrect[i];
      total[i] += thr[t].dTotal[i];
    }
    length += thr[t].dLength;
    if(thr[t].th < thr[t+1].th){ /* not tie */
      bleu = calBLEU(nbest, correct, total, length);
      if(bleu > maxBLEU){
	maxBLEU = bleu;
	*weight = (thr[t].th + thr[t+1].th)/2;
      }
    }
  }
}

double
calWeight(Nbest *nbest, double *lambda, int feature, double *weight)
{
  double currentWeight = lambda[feature]; /* save the current weight*/
  double bleu;
  
  findThresholdPoints(nbest, lambda, feature);
  findMaxBLEU(nbest, weight);
  lambda[feature] = *weight;
  bleu = nbestBLEU(nbest, lambda);
  lambda[feature] = currentWeight; /* restore the weight */
  return bleu;
}

double
nbestLinear(Nbest *nbest, double *lambda, int numItr2, int *innerIteration)
{
  double bestBLEU, bleu, bestWeight, weight, sum;
  int prevBestFeature, itr, bestFeature, feature, i;
  
  bestBLEU = nbestBLEU(nbest, lambda);
  if(DEBUG2){
    fprintf(stderr, "nbestLinear: bestBLEU=%f, numItr2=%d\n",
	    bestBLEU, numItr2);
  }
  
  prevBestFeature = -1;		/* best feature of the previous itr */
  for(itr=0; itr<numItr2; itr++){
    /* optimize in each feature (direction), choose the best feature */
    if(DEBUG2){printArray(lambda, nbest->numFeatures, "lambda ");}
    bestFeature = -1;		/* current best feature */
    for(feature=0; feature<nbest->numFeatures; feature++){
      if(feature==prevBestFeature)continue; /* has been optimized */
      bleu = calWeight(nbest, lambda, feature, &weight);
      if(bleu > bestBLEU){
	bestBLEU = bleu;
	bestFeature = feature;
	bestWeight = weight;
      }
      if(DEBUG2){
	fprintf(stderr, "itr=%d, feature=%d, weight=%f, bleu=%f\n",
		itr, feature, weight, bleu);
      }
    }
    if(bestFeature==-1) break;	/* no improvement */
    lambda[bestFeature] = bestWeight;
    prevBestFeature = bestFeature;
    if(DEBUG2){
      fprintf(stderr, "bestBLEU=%f, bestFeature=%d, bestWeight=%f\n",
	      bestBLEU, bestFeature, bestWeight);
    }
  }
  *innerIteration = itr;

  /* normalize lambda */
  sum = 0;
  for(i=0; i<nbest->numFeatures; i++){
    sum += fabs(lambda[i]);
  }
  for(i=0; i<nbest->numFeatures; i++){
    lambda[i] /= sum;
  }
  
  return bestBLEU;
}

static VALUE
rb_mert_linear(VALUE klass, VALUE rb_lambda, VALUE rb_numItr,
	       VALUE rb_numItr2, VALUE rb_maxKeepBest)
{
  Mert *mert;
  Nbest *nbest;
  int numItr = NUM2INT(rb_numItr), numItr2 = NUM2INT(rb_numItr2), i, itr;
  double lambda[RARRAY(rb_lambda)->len], bestBLEU=0, bleu;
  double bestLambda[RARRAY(rb_lambda)->len];
  VALUE rb_bestLambda = rb_ary_new();
  int maxKeepBest=NUM2INT(rb_maxKeepBest), keepBest=0, innerIteration;

  GET_Mert(klass, mert);
  nbest = mert->nbest;
  g_assert(nbest->numFeatures == RARRAY(rb_lambda)->len);
  for(i=0; i<nbest->numFeatures; i++){
    lambda[i] = NUM2DBL(RARRAY(rb_lambda)->ptr[i]);
  }
  fprintf(stderr, "numItr=%d, numItr2=%d, maxKeepBest=%d\n", numItr, numItr2, maxKeepBest);
  printArray(nbest->lambdaMin, nbest->numFeatures, "min");
  printArray(nbest->lambdaMax, nbest->numFeatures, "max");
  
  for(itr=0; itr<numItr && keepBest<maxKeepBest; itr++){
    fprintf(stderr, "**** itr=%d ****\n", itr+1);
    printArray(lambda, nbest->numFeatures, " lambdaBeg ");
    bleu = nbestLinear(nbest, lambda, numItr2, &innerIteration);
    if(bleu > bestBLEU){
      bestBLEU = bleu;
      for(i=0; i<nbest->numFeatures; i++){bestLambda[i] = lambda[i];}
      keepBest=0;
    }else{
      keepBest++;
    }

    printArray(lambda, nbest->numFeatures, " lambdaEnd ");
    fprintf(stderr, "bleu=%f, bestBLEU=%f, innerIteration=%d, keepBest=%d\n", bleu, bestBLEU, innerIteration, keepBest);
    printArray(bestLambda, nbest->numFeatures, "bestLambda ");
    for(i=0; i<nbest->numFeatures; i++){
      lambda[i] = nbest->lambdaMin[i] +
	((nbest->lambdaMax[i] - nbest->lambdaMin[i])*rand())/RAND_MAX;
    }
  }
  
  for(i=0; i<nbest->numFeatures; i++){
    rb_ary_push(rb_bestLambda, rb_float_new(bestLambda[i]));
  }
  return rb_ary_new3(2, rb_float_new(bestBLEU), rb_bestLambda);
}

void
Init_mertlib()
{
  static VALUE mert;

  mert = rb_define_class("MertLib", rb_cObject);
  
  rb_define_singleton_method(mert, "new", rb_mert_new, 0);
  rb_define_method(mert, "readRefs", rb_mert_readrefs, 1);
  rb_define_method(mert, "printRefs", rb_mert_printrefs, 0);
  rb_define_method(mert, "readNbests", rb_mert_readnbests, 2);
  rb_define_method(mert, "printNbests", rb_mert_printnbests, 0);
  rb_define_method(mert, "setRange", rb_mert_set_range, 2);
  rb_define_method(mert, "bleu", rb_mert_bleu, 1);
  rb_define_method(mert, "estimate", rb_mert_estimate, 6);
  rb_define_method(mert, "uobyqa", rb_mert_uobyqa, 7);
  rb_define_method(mert, "linear", rb_mert_linear, 4);
}
