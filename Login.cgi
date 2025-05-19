require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

$| = 1; 

my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$AUTHKEY    = $in{'AuthKey'};

$WHICHDB = 'LIVE';
$PROGRAM = 'ReconRx';

if ( $AUTHKEY ) {
  ($isMember, $USER_ID, $TYPE, $PH_ID, $USER, $LEVEL, $PharmacyCount) = &isAuthorizedArete($AUTHKEY, $PROGRAM);
}
else {
  ($isMember, $USER_ID, $TYPE, $PH_ID, $LEVEL, $PharmacyCount, $aggregated, $arete, $whichdb) = &isAuthorizedMember($USER, $PASS, $PROGRAM);
}

if ($whichdb =~ /Webinar/i) {
  $WHICHDB = 'Webinar';
}

if ($isMember) {
  print "Set-Cookie:USER=$USER_ID;           path=/; domain=$cookie_server;\n";
  print "Set-Cookie:LOGIN=$USER;             path=/; domain=$cookie_server;\n";
  print "Set-Cookie:TYPE=$TYPE;              path=/; domain=$cookie_server;\n";
  print "Set-Cookie:Aggregated=$aggregated;  path=/; domain=$cookie_server;\n";
  print "Set-Cookie:PROGRAM=$PROGRAM;        path=/; domain=$cookie_server;\n";
  print "Set-Cookie:PH_ID=$PH_ID;            path=/; domain=$cookie_server;\n" if ($TYPE =~ /User/i);
  print "Set-Cookie:PH_COUNT=$PharmacyCount; path=/; domain=$cookie_server;\n";
  print "Set-Cookie:WHICHDB=$WHICHDB;        path=/; domain=$cookie_server;\n";
  print "Set-Cookie:AreteMember=$arete;      path=/; domain=$cookie_server;\n";
}
else {
   print "Location: ../Login.html\n\n";
   exit(0);
}

if ( $TYPE =~ /Admin|Affiliate/i || $PharmacyCount > 1 ) {
  &logActivity($USER, "SuperUser Logged in to ReconRx", NULL);
  if($USER_ID != '1694') {
    print "Location: MyReconRx_Super.cgi\n\n";
  }
  else {
    print "Location: MyArete_Super.cgi\n\n";
  }
} else {
  &logActivity($USER, "Logged in to ReconRx", $PH_ID);
  print "Location: MyReconRx.cgi?\n\n";
}

exit(0);

