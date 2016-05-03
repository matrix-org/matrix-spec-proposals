#!/usr/bin/perl

use strict;
use warnings;

use File::Slurp qw/read_file/;

if (scalar(@ARGV) < 1) {
    die "Usage: $0 include_dir file_to_replace...";
}

my $include_dir = $ARGV[0];
if (! -d $include_dir) {
    die "'$include_dir' is not a directory";
}

my $header = read_file("${include_dir}/head.html");
my $nav = read_file("${include_dir}/nav.html");
my $footer = read_file("${include_dir}/footer.html");

$header .= "<link rel=\"stylesheet\" href=\"/docs/guides/css/docs_overrides.css\">\n";

$nav = <<EOT;
  <div id="page-wrapper">
    <div class="page-content" id="page-container">
      $nav
       <div id="main-content">
         <div class="wrapper" id="wrapper">
           <div class="document_foo" id="document">
EOT

$footer = <<EOT;
            </div>
          </div>
          <div class="push">
          </div>
        </div>
      </div>
        $footer
      </div>
    </div>
EOT

my $oldargv;
while(<>) {
    if (!$oldargv || $ARGV ne $oldargv) {
        # new file: open output file
        unlink($ARGV);
        open(ARGVOUT, ">", $ARGV);
        select(ARGVOUT);
        $oldargv = $ARGV;
    }

    s/<head>/$&$header/;

    if (/<body.*?>/) {
        my $match = $&;
        my $classes = "blog et_fixed_nav et_cover_background et_right_sidebar";
        if ($match =~ / class=/) {
            $match =~ s/ class="([^"]*)"/ class="$1 $classes"/;
        } else {
            $match =~ s/>/ class=\"$classes\">/;
        }

        s/<body.*?>/$match$nav/;
    }

    s#</body>#$footer$&#;

    print;
}
