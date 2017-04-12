#!/usr/bin/perl

use strict;
use warnings;

use Fcntl ':mode';

my $phys = $ENV{'DOCUMENT_ROOT'};
my $virt = '/'.$ENV{'PATH_INFO'};

my @hidden = (                            # hide these files - never consider them
  qr!^/releases/\d\d\.\d\d-SNAPSHOT/?$!,
  qr!^/releases/faillogs/?$!,
  qr!^/packages-\d\d\.\d\d/?$!,
  qr/.DS_Store/,                          # ignore OSX .DS_Store file
  qr/index.html/                          # test script generates test.html in the SampleData directory
);

my $hidden_re = join '|', @hidden;        # build the master regex for hidden files
   $hidden_re = qr/$hidden_re/o;

my @metafiles = (                         # files to be displayed as "meta files" at the top of the page
  qr/packages/,
  qr/config.seed/,
  qr/manifest/,
  qr/lede-imagebuilder/,
  qr/lede-sdk/,
  qr/sha256sums/
  );

my $metafiles_re = join '|', @metafiles;  # build the master regex for meta files
   $metafiles_re = qr/$metafiles_re/o;

print "Content-type:text/html\n\n";
print '<html><head><style type="text/css">';

print <<EOT;
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
}
body {
  color: #333;
  padding-top: 2em;
  font-family: Helvetica,Arial,sans-serif;
  width: 90%;
  min-width: 700px;
  max-width: 1100px;
  margin: auto;
  font-size: 120%;
  background-color: #ddd;
}
h1 {
  font-size: 120%;
  line-height: 1em;
}
table {
  width: 100%;
  box-shadow: 0 0 0.5em #999;
  margin: 0;
  border: none !important;
  margin-bottom: 2em;
  border-collapse: collapse;
  border-spacing: 0;
}
th {
  background: #000;
  background: -webkit-linear-gradient(top, #444, #000);
  background: -moz-linear-gradient(top, #444, #000);
  background: -ms-linear-gradient(top, #444, #000);
  background: -o-linear-gradient(top, #444, #000);
  background: linear-gradient(top, #444, #000);
  font-size: 14px;
  line-height: 24px;
  border: none;
  text-align: left;
  color: #fff;
}
tr {
  background: rgba(255, 255, 255, 0.8);
}
tr:hover {
  background: rgba(255, 255, 255, 0.6); 
}
th, td {
  font-size: 14px;
  height: 20px;
  vertical-align: middle;
  white-space: nowrap;
  padding: 0.2em 0.5em;
  border: 1px solid #ccc;
}
a:link, a:visited {
  color: #337ab7;
  font-weight: bold;
  text-decoration: none;
}
a:hover, a:active, a:focus {
  color: #23527c;
  text-decoration: underline;
}
.s {
  text-align: right;
  width: 15%;
}
.d {
  text-align: center;
  width: 15%;
}
EOT

print '</style>';
printf "<title>Index of %s</title></head><body><h1>Index of %s</h1>\n", $virt, $virt;
print "<hr><table>";
print '<tr><th class="n">File Name</th><th class="s">File Size</th><th class="d">Date</th></tr>';
print "\n";

my @entries;

if (opendir(D, $phys)) {
  while (defined(my $entry = readdir D)) {
    my $vpath = $virt . $entry;
    next if $entry eq '.' || $vpath =~ $hidden_re;
    push @entries, $phys . $entry;
  }
  closedir D;
}

@entries = sort {
  my $d1 = !-d $a;
  my $d2 = !-d $b;
  return (($d1 <=> $d2) || ($a cmp $b));
} @entries;

sub htmlenc {
  my $s = shift;

  if (defined($s) && length($s)) {
    $s =~ s!([<>"])!sprintf '&#%u;', $1!eg; # " 
  }

  return $s;
}

sub printentry {
  my $entry = shift;

}

my @metas;
my @images;

foreach my $entry (@entries) {                # separate meta-files from image files
  if ($entry =~ $metafiles_re) { 
    push @metas, $entry;
  }
  else {
    push @images, $entry;
  }
}

foreach my $entry (@entries) {
  my ($basename) = $entry =~ m!([^/]+)$!; # / 

  print "<tr>";

  my @s = stat $entry;
  my $link = (-l $entry)
    ? sprintf('<var> -&#62; %s</var>', htmlenc(readlink($entry)))
    : '';

  if (S_ISDIR($s[2])) {
    printf '<td class="n"><a href="%s">%s</a>/%s</td>',
      htmlenc($basename),
      htmlenc($basename),
      $link;
    printf '<td class="s">-</td>';
    printf '<td class="d">%s</td>', scalar localtime $s[9];
  }
  else {
    printf '<td class="n"><a href="%s">%s</a>%s</td>',
      htmlenc($basename),
      htmlenc($basename),
      $link;
    printf '<td class="s">%.1f KB</td>', $s[7] / 1024;
    printf '<td class="d">%s</td>', scalar localtime $s[9];
  }

  print "</tr>\n";
}

print "</table>";
print "</body></html>";