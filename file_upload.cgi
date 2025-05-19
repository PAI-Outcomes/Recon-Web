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
my $www = 'members';
$www = 'www' if ($ENV{'SERVER_NAME'} =~ /^dev./);
my ($sec,$min, $hour, $day, $month, $year) = (localtime)[0,1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$date  = sprintf("%04d%02d%02d%02d%02d%02d", $year, $month, $day, $hour, $min, $sec);

&readsetCookies;
#&readPharmacies();

my $q = CGI->new;

##$CGI::POST_MAX = 1024 * 5000;
my $safe_filename_characters = "a-zA-Z0-9_.-";
#my $filename = "Test_File.txt";
my $filename = $q->param("upfile");
my $remit_type  = $q->url_param('remit_type');

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
    print "<script>parent.callback('Filename issues')</script>";
    die "Filename contains invalid characters";
  }

  if ( $remit_type =~ /CAMedicaid|Omnysis/i && $filename !~ /pdf$/i ) {
    print "<script>parent.callback('File Upload Failed Due to Incorrect File Type')</script>";
    exit;
  }

my $UPLOAD_FH = $q->upload("upfile");

my $newfilename = "${PH_ID}_${date}_${filename}";

umask 0000; #This is needed to ensure permission in new file
my $upload_dir = "D:\\WWW\\${www}.recon-rx.com\\WebShare\\uploads\\EOBUpload\\";

$upload_dir .= $remit_type;

open $NEWFILE_FH, ">$upload_dir/$newfilename";

if ($filename =~ /\.zip|\.pdf/) {
 binmode $NEWFILE_FH;
}

while ( <$UPLOAD_FH> ) {
    print $NEWFILE_FH "$_";
}

close $NEWFILE_FH or die "I cannot close filehandle: $!";

##this is the only way to send msg back to the client
print "<script>parent.callback('File Upload: $filename--> Success!')</script>";

exit;


