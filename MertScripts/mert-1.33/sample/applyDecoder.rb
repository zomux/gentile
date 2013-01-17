decoder = ARGV.shift
inifile = ARGV.shift
options = ARGV.shift
tmpinifile = ARGV.shift
input = ARGV.shift
output = ARGV.shift
lambdas = ARGV.shift.split

wl, ww, wssx, *wt = lambdas

open(tmpinifile,"w"){|out|
  open(inifile){|fd|
    while line = fd.gets
      case line.chomp
      when '[weight-l]'
	out.puts line
	out.puts wl
	fd.gets
      when '[weight-w]'
	out.puts line
	out.puts ww
	fd.gets
      when '[weight-ssx]'
	out.puts line
	out.puts wssx
	fd.gets
      when '[weight-t]'
	out.puts line
	out.puts wt
	fd.gets
	fd.gets
	fd.gets
	fd.gets
	fd.gets
      else
	out.puts line
      end
    end
  }
}

command = "#{decoder} #{tmpinifile} #{options} < #{input} > #{output}"
STDERR.puts command
system(command)
