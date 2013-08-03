decoder = ARGV.shift
defaultini = ARGV.shift
option = ARGV.shift

srcfile = File.expand_path(ARGV.shift)
outfile = File.expand_path(ARGV.shift)
lbds = ARGV.shift
lambdas = lbds.split.map{|l| l.to_f} #l, w, ssx, tの順であると仮定。

tunedir = File.dirname(outfile)
tmpini = "#{tunedir}/demotic.#{File.basename(outfile)}.ini"

lambdaflag = false

$stderr.puts "Generating #{tmpini}."
open(tmpini,"w"){|outfp|
	open(defaultini){|infp| #l, w, ssx, tの順であると仮定。
		while infp.gets
			$_.chomp!
			if $_ =~ /^\[weight-.*\]$/
				lambdaflag = true
				outfp.puts $_
			elsif lambdaflag == true
				if $_ =~ /^(\d|\.)+$/
					outfp.puts lambdas.shift
				elsif not $_ =~ /^\[weight-.*\]$/
					lambdaflag = false
					outfp.puts $_
				else
					outfp.puts $_
				end
			else
					outfp.puts $_
			end
		end
	}
}

$stderr.puts "Translate Source File: #{srcfile}"
$stderr.puts "n-best File: #{outfile}"
system("LC_ALL=C #{decoder} #{tmpini} #{option} < #{srcfile} > #{outfile}") or abort

