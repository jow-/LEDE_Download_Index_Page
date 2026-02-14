#!/usr/bin/perl

# dir-index.cgi - print a "directory index" for LEDE download pages.
#
# It distinguishes two kinds of directories:
#
# "targets" - which contain firmware image files, plus a few meta-files (sha256sums, gpg info, image builder, SDK)
# "Other directories" - contain any set of files.

use strict;
use warnings;
use Compress::Zlib;

use Fcntl ':mode';
use JSON;

my $htmlcachedir;
my $cache_compress = 1;
my $debug = 0;

if ( !$debug ) {
    $htmlcachedir = "/var/www/cgi-cache";
}
else {
    $htmlcachedir = "/var/tmp/cgi-cache-test";
}

my $stylecss = <<EOT;
  <style type="text/css">
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
  h2 {
    font-size: 100%;
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
  p, th, td {
    font-size: 14px;
  }
  th, td {
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
  .sh {
    font-family: monospace;
  }
  </style>
EOT

# htmlenc - html-encode the argument
sub htmlenc {
  my $s = shift;

  if (defined($s) && length($s)) {
    $s =~ s!([<>"])!sprintf '&#%u;', ord $1!eg; # "
  }

  return $s;
}

# getchecksums - read the checksum file and return a hash for all the named files and their checksums
sub getchecksums {
  my $filename = shift;
  my %sums;
  if (open(my $fh, '<:encoding(UTF-8)', $filename)) {
    while (my $row = <$fh>) {
      chomp $row;
      if ($row =~ m!^([a-f0-9]+) [ *](.+)$!) {
        $sums{$2} = $1;
      }
      elsif ($row =~ m!SHA256\((.+)\)= ([a-f0-9]+)$!) {
        $sums{$1} = $2;
      }
    }
  }
  return %sums;
}

# printentry - print a <tr> row for a target file (not in an ordinary directory)
#   $entry - full path to the file
#   $prefix - empty string if it's a meta-file;
#       otherwise, it's the prefix to remove from the displayed file name
#   $checksums - reference to the checksums for this directory
sub printentry {
  my $entry = shift;
  my $prefix = shift;
  my $checksums = shift;
  my ($basename) = $entry =~ m!([^/]+)$!; # / strip off path info
  my $size = "-";
  my $checksum = $checksums->{$basename};
  my $html;

  if (!$checksum) {                                              # if not present in hash, use "-"
    $checksum = "-";
  }

  my @s = stat $entry;
  my $link = (-l $entry)                                          # if it's a symlink
    ? sprintf('<var> -&#62; %s</var>', htmlenc(readlink($entry))) # add '->' to the link
    : '';                                                         # (is this ever used?)
  my $date = scalar localtime $s[9];

  if (S_ISDIR($s[2])) {
    $size = "-";
    $checksum = "-";
    $basename = $basename."/";
  }
  else {
    $size = sprintf('%.1f KB', $s[7] / 1024);
  }
  my $imagename = $basename;
  if ($prefix && (index($basename, $prefix) == 0)) {              # if there's a prefix, and it matches at front
    $imagename = substr($basename, length($prefix));              # trim it off
  }

# All preparatory work complete: here are the variables
#   $entry:     "./SampleData/config.seed"
#   $basename:  "config.seed"
#   $imagename: $basename, or shortened version of image name
#   $link:      "" or "-> actual-file-following-link"
#   $checksum:  the sum, or "-"
#   $size:      the size ("1234.5 KB") or "-"
#   $date:      in the form "Tue Feb 21 04:03:38 2017"

  # Output the html for the row
  $html .= '  <tr>';
  $html .= sprintf '<td class="n"><a href="%s">%s</a>%s</td>',
    htmlenc($basename),
    htmlenc($imagename),
    $link;
  $html .= sprintf '<td class="sh">%s</td>', $checksum;
  $html .= sprintf '<td class="s">%s</td>', $size;
  $html .= sprintf '<td class="d">%s</td>', $date;
  $html .= "</tr>\n";

  return $html;
}

sub printh1 {
  my $virt = shift;
  my @parts = split /\//, $virt;
  my $s = '';

  if (@parts == 0) {
    @parts = ('');
  }

  for (my $i = 0; $i < @parts; $i++) {
    $s .= sprintf '<a href="%s/">%s</a> / ',
	htmlenc(join('/', @parts[0..$i])),
	$i ? htmlenc($parts[$i]) : '<em>(root)</em>';
  }

  if ( !$debug ) {
     return sprintf "<h1>Index of %s</h1>\n", $s;
  }
  else {
      return sprintf "<h1>Index of test %s</h1>\n", $s;
  }
}

sub print404 {
    my $virt = shift;
    my $html;
    $html .= "Status: 404 Not found\n";
    $html .= "Content-type: text/html\n\n";
    $html .= "<!-- This directory index page generated on the fly by dir-index.cgi -->\n";
    $html .= "<html><head>\n";
    $html .= $stylecss;
    $html .= "<title>Not found: %s</title></head>\n<body>\n", htmlenc($virt);
    $html .= sprintf "<h1>Not found: %s</h1>\n", htmlenc($virt);
    $html .= "<hr>";
    $html .= "<p>The requested resource could not be found on the server.</p>";
    $html .= "<p>Try returning to the <a href=\"/\">root directory</a> to browse available directories.</p>";
    $html .= "</body></html>";
    return $html;
}

sub printheader {
    my $virt = shift;
    my $html;
    $html .= "Content-type:text/html\n\n";
    $html .= "<!-- This directory index page generated on the fly by dir-index.cgi -->\n";
    $html .= "<html><head>\n";
    $html .= $stylecss;
    $html .= sprintf "<title>Index of %s</title></head>\n<body>\n", htmlenc($virt);
    $html .= printh1($virt);
    $html .= "<hr>";
    return $html;
}

# printtargets - print 'targets' directories
#   This special cases directories of LEDE image files and their associated meta-files
sub printtargets {
  my $entries = shift;
  my $phys = shift;
  my $virt = shift;
  my $html;
  my @metafiles = (                         # names of files to be displayed as "meta files" at the top of the page
    qr/packages/,
    qr/config.seed/,
    qr/manifest/,
    qr/lede-imagebuilder/,
    qr/lede-sdk/,
    qr/[Oo]pen[Ww]rt-[Ii]mage[Bb]uilder/,
    qr/[Oo]pen[Ww]rt-[Ss][Dd][Kk]/,
    qr/[Oo]pen[Ww]rt-[Tt]oolchain/,
    qr/md5sums/,
    qr/sha256sums/,
    );

  my $metafiles_re = join '|', @metafiles;  # build the master regex for meta files
     $metafiles_re = qr/$metafiles_re/o;

  # Parse checksum files to get a hash of the file names/sums
  my $checktype = "sha256sum";
  my %checksums = getchecksums($phys.$checktype."s");

  if (!keys %checksums) {
    $checktype = "md5sum";
    %checksums = getchecksums($phys.$checktype."s");
  }

  # To trim image file names intelligently, factor in the following:
  #   $virt e.g.,          "releases/17.01.0/targets/ar71xx/generic/"
  #   $phys e.g.,          "./SampleData/" and
  #   typical entry, e.g., "./SampleData/lede-17.01.0-r3205-59508e3-ar71xx-generic-archer-c7-v2-squashfs-sysupgrade.bin"

  # $trimmedprefix is derived from the last two items of $virt, e.g., "ar71xx-generic-"
  # $prefix comes from the first of @images array that begins with "lede" after ignoring the $phys string

  my ($target, $subtarget, $tuple, %prefixes, $prefix);

  ($target, $subtarget) = $virt =~ m!/([^0-9][^/]+)/([^/]+)/?$!;
  ($target, $subtarget) = ($virt =~ m!/([^/]+)/?$!, '') unless $target;

  $tuple = $target . ($subtarget ? '/' . $subtarget : '');


  # Build a mapping table (prefix => number of occurences)
  # For each image basename, try to find a prefix that either ends in -$target-$subtarget- or in -$target-
  # and if found, use it as key in the %prefixes dictionary and countits value up by one.
  foreach my $image (@$entries) {
    my ($base) = $image =~ m!/([^/]+)$!;
    my $i1 = $subtarget ? index($base, "-$target-$subtarget-") : 0;
    my $i2 = index($base, "-$target-");

    if ($i1 > 0) {
      my $s = substr($base, 0, $i1 + length("-$target-$subtarget-"));
      $prefixes{$s}++;
    }
    elsif ($i2 > 0) {
      my $s = substr($base, 0, $i2 + length("-$target-"));
      $prefixes{$s}++;
    }
  }

  # Sort the found prefix substrings descending by number of occurences and put the first (most used)
  # one into $prefix.
  ($prefix) = sort { $prefixes{$b} <=> $prefixes{$a} } keys %prefixes;


  my @metas;                                    # contains meta-file names
  my @images;                                   # contains image files that could be flashed

  foreach my $entry (@$entries) {               # push files into the proper array
    if ($entry =~ m!/$prefix!o && $entry !~ $metafiles_re) {
      push @images, $entry;
    }
    else {
      push @metas, $entry;
    }
  }

  # Begin to print the page
  $html .= printheader($virt);

  $html .= <<EOT;
  <h2>Image Files</h2>
  <p>These are the image files for the <b>$tuple</b> target.
  Check that the $checktype of the file you downloaded matches the $checktype below.<br />
  <i>Shortened image file names below have the same prefix: <code>$prefix...</code></i>
  </p>
EOT
  # /

  $html .= "<table>\n";
  $html .= '  <tr><th class="n">Image for your Device</th><th>'.$checktype.'</th><th class="s">File Size</th><th class="d">Date</th></tr>'."\n";
  foreach my $entry (@images) {
    $html .= printentry($entry, $prefix, \%checksums)
  }
  $html .= "</table>\n";

  $html .= <<EOT;
  <h2>Supplementary Files</h2>
  <p>These are supplementary resources for the <b>$tuple</b> target.
  They include build tools, the imagebuilder, $checktype, GPG signature file, and other useful files. </p>
EOT
  # /

  $html .= "<table>\n";
  $html .= '  <tr><th class="n">Filename</th><th>'.$checktype.'</th><th class="s">File Size</th><th class="d">Date</th></tr>'."\n";
  foreach my $entry (@metas) {
    $html .= printentry($entry, "", \%checksums)
  }
  $html .= "</table>\n";

  $html .= "</body></html>\n";

  return $html;
}

# printdirectory - print any directory in a pleasing format
#   This substantially copies the format used by downloads.lede-project.org in early 2017
sub printdirectory {
  my $entries = shift;
  my $phys = shift;
  my $virt = shift;
  my $html;

  $html .= printheader($virt);
  $html .= "<table>\n";
  $html .= '  <tr><th class="n">File Name</th><th class="s">File Size</th><th class="d">Date</th></tr>'."\n";

  foreach my $entry (@$entries) {
    my ($basename) = $entry =~ m!([^/]+)$!; # /

    $html .= "  <tr>";

    my @s = stat $entry;
    my $link = (-l $entry)
      ? sprintf('<var> -&#62; %s</var>', htmlenc(readlink($entry)))
      : '';

    if (S_ISDIR($s[2])) {
      $html .= sprintf '<td class="n"><a href="%s/">%s</a>/%s</td>',
        htmlenc($basename),
        htmlenc($basename),
        $link;
      $html .= sprintf '<td class="s">-</td>';
      $html .= sprintf '<td class="d">%s</td>', scalar localtime $s[9];
    }
    else {
      $html .= sprintf '<td class="n"><a href="%s">%s</a>%s</td>',
        htmlenc($basename),
        htmlenc($basename),
        $link;
      $html .= sprintf '<td class="s">%.1f KB</td>', $s[7] / 1024;
      $html .= sprintf '<td class="d">%s</td>', scalar localtime $s[9];
    }

    $html .= "</tr>\n";
  }

  $html .= "</table>\n";
  $html .= "</body></html>\n";

  return $html;
}

# ====== Main Routine ======

my $phys = $ENV{'DOCUMENT_ROOT'};
my $virt = '/'.$ENV{'PATH_INFO'};
my $printout;
my $statcache;
my $dirstat;

# add caching function
my $sanitized_virt = $virt;
$sanitized_virt =~ s/\//_/g;
my $htmlcachefile = $htmlcachedir."/".$sanitized_virt.".cache";
my $fstatcache = $htmlcachedir."/".$sanitized_virt.".stat";

# this is mtime, which gets updated if the rsync run
# pulls additional files i.e. packages
my @tmp = stat($phys);
$dirstat = $tmp[9];

if ( -e $fstatcache ) {
    open(STAT, "<$fstatcache") or die ("Unable to open $fstatcache due to $!\n");
    read STAT, $statcache, -s STAT;
    close STAT;


    if ( $statcache eq $dirstat ) {
        # if the .cache file exists, print it out and exit
        if ( -e $htmlcachefile ) {
	    open(CACHE, "<$htmlcachefile") or die ("Unable to open $htmlcachefile due to $!\n");
            read CACHE, $printout, -s CACHE;
            close CACHE;

            if ( $cache_compress ) {
                print uncompress($printout);
            }
            else {
	        print $printout;
            }
	    print "stat: $dirstat";
            exit 0;
	}
    }
    else {
	# updating cache
    }
}

my @hidden = (                            # hide these files - never consider them
  qr!^/releases/\d\d\.\d\d-SNAPSHOT/?$!,
  qr!^/releases/faillogs/?$!,
  qr!^/packages-\d\d\.\d\d/?$!,
  qr!/\.[^/]+$!,                          # ignore hidden files and directories
  qr!index\.html!                         # test script generates index.html in the SampleData directory
);

my $hidden_re = join '|', @hidden;        # build the master regex for hidden files
   $hidden_re = qr/$hidden_re/o;

my @entries;                              # holds all files in the directory, except hidden files

if (opendir(D, $phys)) {                  # read all the files from the directory
  while (defined(my $entry = readdir D)) {
    my $vpath = $virt . $entry;
    next if $entry eq '.' || $entry eq '..' || $vpath =~ $hidden_re;  # ignore filenames "." or in $hidden_re
    push @entries, $phys . $entry;
  }
  closedir D;
}
else {
  $printout .= print404($virt);
  exit 0;
}

@entries = sort {
  my $d1 = !-d $a;
  my $d2 = !-d $b;
  return (($d1 <=> $d2) || ($a cmp $b));
} @entries;

# @entries contains list of files from the directory that should be processed

if ($virt =~ m!/targets/$! && $ENV{'QUERY_STRING'} =~ m!^json\b!) {
  my ($type, $mindepth, $maxdepth) = ('f', 0, 3);

  if ($ENV{'QUERY_STRING'} =~ m!\btargets!) {
    ($type, $mindepth, $maxdepth) = ('d', 2, 2);
  }

  if (open F, '-|', 'find', $phys, '-mindepth', $mindepth, '-maxdepth', $maxdepth, '-type', $type) {
    my @list;

    while (defined(my $line = readline F)) {
      chomp $line;
      push @list, substr $line, length $phys;
    }
    close F;

    $printout .= "Content-Type: application/json\n\n";
    $printout .= JSON::encode_json(\@list);
  }
}
elsif ($virt =~ m!/targets/[^/]+/[^/]+/?$! || # special handling for 'targets' - LEDE image file directories
       $virt =~ m!/(backfire|kamikaze)/[^/]+/[^/]+/?$! ||
       $virt =~ m!/(attitude_adjustment|barrier_breaker|chaos_calmer)/[^/]+/[^/]+/[^/]+/?$!) {
  $printout .= printtargets(\@entries, $phys, $virt)
}
else {                                        # otherwise use standard directory display format
  $printout .= printdirectory(\@entries, $phys, $virt)
}

# put the generated html into a cache file
open(WCACHE, ">$htmlcachefile") or die ("Unable to write cache file $htmlcachefile due to $!\n");
open(SCACHE, ">$fstatcache") or die ("Unable to write stat cache file $fstatcache due to $!\n");
if ( $cache_compress ) {
    print WCACHE compress($printout, 9);
}
else {
    print WCACHE $printout;
}
print SCACHE $dirstat;
close WCACHE;
close SCACHE;

print $printout;
