#______________________________________________________________________________
#
# Steve Downing 
# Date: 01/15/2018
# Review_My_Reconciled_Claims_Monthly.cgi
#
#
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

#$uberdebug++;
if ($uberdebug) {
# $incdebug++;
  $debug++;
  $verbose++;
}

#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#

$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$debug   = $in{'debug'}   if (!$debug);
$verbose = $in{'verbose'} if (!$verbose);

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$VALID      = $in{'VALID'};
$SORT       = $in{'SORT'};

($USER)  = &StripJunk($USER);
($PASS)  = &StripJunk($PASS);

$debug++ if ( $verbose );
$in{'debug'}++    if ( $debug );
$in{'verbose'}++  if ( $verbose );
$in{'incdebug'}++ if ( $incdebug );
#
my $submitvalue = "SAVE";

#______________________________________________________________________________

&readsetCookies;
&readPharmacies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

#______________________________________________________________________________

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    $Agg  = "\\Aggregated";
    $Agg2 = "/Aggregated";
    $inNCPDP = $USER;
    &ReconRxAggregatedHeaderBlock_New;
  }
  else { 
    &ReconRxHeaderBlock;
  }
} else {

   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

print "\nProg: $prog &nbsp; &nbsp; \nDate: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);
print "cookie_server: $cookie_server<br>\n" if ($debug);

if ( $debug ) {
   print "dol0: $0<br>\n";
   print "prog: $prog, dir: $dir, ext: $ext<br>\n" if ($verbose);
   print "<hr size=4 noshade color=blue>\n";
   print "PROG: $PROG<br>\n";
   print "<br>\n";
   my $key;
   foreach $key (sort keys %in) {
      print "key: $key, val: $in{$key}<br>\n";
   }
   print "<hr size=4 noshade color=blue>\n";
}

$testing = '_TEST' if ($ENV eq 'dev');

$ntitle = "Accounts Receivable Reports for $inNCPDP";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;
  print "sub displayWebPage: Entry.<br>\n" if ($debug);
  &readPharmacies;

  ($PROG = $prog) =~ s/_/ /g;

# Look for End_of_Month file
  if ( $ENV =~ /Dev/i ) {
     $outdir    = qq#D:\\WWW\\www.recon-rx.com\\WebShare\\End_of_Month$Agg_Reconciled_Claims$Agg#;
  } else {
     $outdir    = qq#\\\\$WBSERVER\\Webshare (ReconRx)\\End_of_Month${testing}$Agg#;
  }
  
  #print "outdir: $outdir\n";


  %EOMfiles  = ();
  %EOMFNAMES = ();

  $ID = $Reverse_Pharmacy_NCPDPs{$inNCPDP};
  $ID = "Aggregated"  if ( $PH_ID  eq 'Aggregated');

  opendir(DIR, "$outdir") or die $!;
  @files = grep(/\.xlsx$/,readdir(DIR));
  @files = grep(/${inNCPDP}_${ID}/,@files);
  $file = @files;

  closedir(DIR);
  if ($#files < 0) {
    print qq#<h3>No files to display at this time</h3>\n#;
    exit(0);
  }

  foreach $fname (@files) {
     my @pcs = split("_", $fname);
     my $ptr = @pcs;
        $ptr--;
     my $ptrM1 = $ptr -1 ;
     $pcs[$ptr] =~ s/\.xlsx//gi;
     my $threechar = substr($pcs[$ptr], 0, 3);

     next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
     next if ( $fname !~ /${inNCPDP}_/ );
   
     $ptrmonth = $months{$threechar};
     $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
     $dofiles{$key} = $fname;
  }

  foreach $key (sort { $b <=> $a } keys %dofiles) {

     $fname = $dofiles{$key};
     next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
     next if ( $fname !~ /${inNCPDP}_/ );

     print "fname: $fname<br>\n" if ( $debug );

     $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Month${testing}$Agg2/$fname";
     $thisfile       = "$outdir\\$fname";
     $EOMfiles{$key} = "$webpath";

     $EOMFNAMES{$key} = $fname;
  }

  $ptr = 0;
  $max = 12;
  $max = 18 if ($Pharmacy_Arete{$ID});
  foreach $key (reverse sort keys %EOMFNAMES) {
    if ( $debug ) {
       print "EOMFNAME: $EOMFNAMES{$key}<br>\n";
       print "EOMfiles: $EOMfiles{$key}<hr>\n";
    }
    if ( $ptr < $max ) {
       print qq#<a href="$EOMfiles{$key}">$EOMFNAMES{$key}</a><br>\n#;
    }
    $ptr++;
  }
  print "<hr size=8>\n" if ($debug);

  print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________
