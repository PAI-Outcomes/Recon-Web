#______________________________________________________________________________
#
# Jay Herder
# Date: 05/14/2012
# index.cgi
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/MyData/Common_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

#$uberdebug++;
if ($uberdebug) {
  $incdebug++;
  $debug++;
  $verbose++;
}

#####$dbitrace++;

if ( $prog =~ /^index/i ) { $title = "Home"; } else { $title = "$prog"; }
$title = qq#${RECONRXCOMPANY} - $title# if ( $RECONRXCOMPANY );
$title =~ s/_/ /g;

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
$isAdmin    = $in{'isAdmin'};
$CUSTOMERID = $in{'CUSTOMERID'};
$LTYPE      = $in{'LTYPE'};
$LDATEADDED = $in{'LDATEADDED'};

($USER) = &StripJunk($USER);
($PASS) = &StripJunk($PASS);

$debug++ if ( $verbose );
$in{'debug'}++    if ( $debug );
$in{'verbose'}++  if ( $verbose );
$in{'incdebug'}++ if ( $incdebug );
#
my $submitvalue = "SAVE";
$CUSTOMERID = "" if ( !$CUSTOMERID );

#______________________________________________________________________________

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

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$TODAY  = sprintf("%04d02d02d000000", $year, $month, $day);
#______________________________________________________________________________

($isMember, $VALID) = &isReconRxMember($USER, $PASS);

# print qq#USER: $USER, PASS: $PASS, VALID: $VALID, isMember: $isMember\n# if ($debug);

if ( $isMember && $VALID ) {

   &MyReconRxHeader;
   &ReconRxHeaderBlock;

} else {

#  &ReconRxHeaderBlock("No Side Nav");
#  &ReconRxMembersLogin;
   &ReconRxGotoNewLogin;

   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
#______________________________________________________________________________

&readPharmacies;
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
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
   my $key;
   foreach $key (sort keys %in) {
      print "key: $key, val: $in{$key}<br>\n";
   }
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
#  print "inNPI: $inNPI, dispNPI: $dispNPI<br>\n";
#  print "inNCPDP: $inNCPDP, dispNCPDP: $dispNCPDP<br>\n";
   print "<hr size=4 noshade color=blue>\n";
}

&displayWebPage($dispNCPDP, $dispNPI);

#______________________________________________________________________________
print "<br>cookie_server: $cookie_server<br>\n" if ($debug);

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

   my ($jNCPDP, $jNPI) = @_;
   print qq#<!-- displayWebPage -->\n#;
   print "sub displayWebPage: Entry. jNCPDP: $jNCPDP, jNPI: $jNPI<br>\n" if ($debug);

   $SERVER_NAME = $ENV{"SERVER_NAME"};
   print "SERVER_NAME: $SERVER_NAME<br>\n" if ($debug);

   print "<table border=3 cellpadding=3 cellspacing=3>\n";
   foreach $env_var (sort keys %ENV) {
     $value = $ENV{$env_var};
     if (! $value) { $value = "(null)"; }
     print "<TR>\n";
     print "<TD><FONT COLOR=red >$env_var </FONT></TD>\n";
     print "<TD><FONT COLOR=blue>$value   </FONT></TD>\n";
     print "</TR>\n";
   }
   print "</table>\n";

######################################
   print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________
