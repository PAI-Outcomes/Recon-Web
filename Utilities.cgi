#______________________________________________________________________________
#
# Jay Herder
# Date: 12/02/2011
##
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
my ($prog, $dir, $ext) = fileparse($0, '\..*');
#####print "dol0: $0\nprog: $prog, dir: $dir, ext: $ext\n";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
my $submitvalue = "Open the Database";
$nbsp = "&nbsp\;";

#$uberdebug++;
if ( $uberdebug ) {
  $incdebug++;
  $debug++;
  $verbose++;
}
#####$dbitrace++;

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

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
$USER    = $in{'USER'};
$PASS    = $in{'PASS'};
$VALID   = $in{'VALID'};
$CUSTOMERID = $in{'CUSTOMERID'};
$isAdmin = $in{'isAdmin'};

$debug++ if ( $verbose );

#______________________________________________________________________________

&readsetCookies;

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


print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);

if ( $debug ) {
  print "<hr size=4 noshade color=blue>\n";
  my $key;
  foreach $key (sort keys %in) {
     next if ( $key =~ /^PASS\s*$/ );	# skip printing out the password...
     print "key: $key, val: $in{$key}<br>\n";
  }
  print "<hr size=4 noshade color=blue>\n";
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

print "\nProg: $prog &nbsp; &nbsp;<br>Date: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
#______________________________________________________________________________
&readLogins;

$LFirstName = $LFirstNames{$USER};
$LLastName  = $LLastNames{$USER};

#______________________________________________________________________________
#
print qq#<table class="main" border=0 cellpadding=1 cellspacing=1>\n#;
print qq#<tr><td align=left><strong>$ntitle</strong></td></tr>\n#;

if ( $CUSTOMERID && $USER && $PASS && $VALID ) {
   print qq#<tr><th align=left>Logged in as $CUSTOMERID - $USER ($LFirstName $LLastName)</th></tr>\n#;
}
print qq#<tr valign=top><td>\n#;
&dispHeadings;
print qq#</td></tr>\n#;

print qq#<tr><th align=left><font size=+1>Utilities</font></th></tr>\n#;

print qq#<tr valign=top><td>\n#;
print qq#<a href="Tori_Report.cgi">Tori Report</a><br>\n#;
print qq#</td></tr>\n#;

print qq#<tr valign=top><td>\n#;
print qq#<a href="http://www.RBSDesktop.com/cgi-bin/PHP_info.php">PHP Info</a><br>\n#;
print qq#</td></tr>\n#;

print qq#<tr valign=top><td>\n#;
print qq#<a href="http://www.RBSDesktop.com/cgi-bin/MySQL_info.cgi">MySQL Info</a><br>\n#;
print qq#</td></tr>\n#;

print qq#<tr valign=top><td>\n#;
print qq#<a href="http://www.RBSDesktop.com/cgi-bin/serverinfo.cgi">Display Server Information</a><br>\n#;
print qq#</td></tr>\n#;

print qq#</table>\n#;

#______________________________________________________________________________

&trailer;

print qq#</BODY>\n#;
print qq#</HTML>\n#;

exit(0);
