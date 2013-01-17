require "mkmf"
$CFLAGS = "-Wall " + `pkg-config --cflags glib-2.0`.chomp
$LOCAL_LIBS = `pkg-config --libs glib-2.0`.chomp + " -lc -lgsl -lgslcblas -lgfortran"
$objs = "mertlib.o uobyqa.o".split
create_makefile("mertlib")
