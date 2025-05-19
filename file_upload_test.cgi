#!/usr/bin/perl

use warnings;
##use strict;
use CGI;
use File::Basename;
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";
require "D:/RedeemRx/MyData/Common_routines.pl";
my $inNCPDP;
my $dispNCPDP;
my $inNPI;
my $dispNPI;
my %in;
my $ret;
my $date;

my ($sec,$min, $hour, $day, $month, $year) = (localtime)[0,1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$date  = sprintf("%04d%02d%02d%02d%02d%02d", $year, $month, $day, $hour, $min, $sec);

&readsetCookies;

if ( $USER ) {
   $inNCPDP   = $USER;
   $dispNCPDP = $USER;
} else {
   $inNCPDP   = $in{'inNCPDP'};
   $dispNCPDP = $in{'dispNCPDP'};
}
if ( $PASS ) {
   $inNPI   = $PASS;
   $dispNPI = $PASS;
} else {
   $inNPI   = $in{'inNPI'};
   $dispNPI = $in{'dispNPI'};
}

my $q = CGI->new;

$CGI::POST_MAX = 1024 * 5000;
my $safe_filename_characters = "a-zA-Z0-9_.-";
my $filename = $q->param("upfile");

  print $q->header ( );
  if ( !$filename ) {
    print "<script>parent.callback('There was a problem uploading your file (try a smaller file).')</script>";
    exit;
  }

  my ( $name, $path, $extension ) = fileparse ( $filename, '..*' );
  $filename = $name . $extension;
  $filename =~ tr/ /_/;
  $filename =~ s/[^$safe_filename_characters]//g;
  
  if ( $filename =~ /^([$safe_filename_characters]+)$/ ) {
    $filename = $1;
  }
  else {
    die "Filename contains invalid characters";
    print "<script>parent.callback('Filename issues')</script>";
  }

my $UPLOAD_FH = $q->upload("upfile");

my $newfilename = "${USER}_${date}_${filename}";

umask 0000; #This is needed to ensure permission in new file
my $upload_dir = 'D:\\WWW\\www.recon-rx.com\\WebShare\\835Upload';

open $NEWFILE_FH, ">$upload_dir/$newfilename"; 

if ($filename =~ /\.zip/) {
 binmode $NEWFILE_FH;
}

while ( <$UPLOAD_FH> ) {
    print $NEWFILE_FH "$_";
}

close $NEWFILE_FH or die "I cannot close filehandle: $!";

##this is the only way to send msg back to the client
print "<script>parent.callback('File Upload: $filename--> Success!')</script>";
alert('test');

exit;


