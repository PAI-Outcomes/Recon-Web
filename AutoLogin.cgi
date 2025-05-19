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

#$USER       = $in{'USER'};
#$PASS       = $in{'PASS'};
$email  =  $in{'Email'};
$access =  $in{'Access'};

#convert  data to JSON
my $op = JSON -> new -> utf8 -> pretty(1);
my $json = $op -> encode({
    IsSuccess        => 1,
    AuthKey          => 'XXXXXXXXXXXXXX',
    ExpiresIn        => '7 Days'
});

exit;


print "
<HTML>
<HEAD>
  <TITLE>TEST</TITLE>
</HEAD>

<BODY>
  EMAIL: $email<br>
  ACCESS: $access
</BODY>

</HTML>";

exit;

if ($USER =~ /^demo|^1111111/i) {
  $WHICHDB = 'Webinar';
}
else {
  $WHICHDB = 'LIVE';
}

$PROGRAM = 'ReconRx';

($isMember, $USER_ID, $TYPE, $PH_ID, $LEVEL, $PharmacyCount) = &isAuthorizedMember($USER, $PASS, $PROGRAM);

if ($isMember) {
  print "Set-Cookie:USER=$USER_ID;           path=/; domain=$cookie_server;\n";
  print "Set-Cookie:LOGIN=$USER;             path=/; domain=$cookie_server;\n";
  print "Set-Cookie:TYPE=$TYPE;              path=/; domain=$cookie_server;\n";
  print "Set-Cookie:PROGRAM=$PROGRAM;        path=/; domain=$cookie_server;\n";
  print "Set-Cookie:PH_ID=$PH_ID;            path=/; domain=$cookie_server;\n" if ($TYPE =~ /User/i);
  print "Set-Cookie:PH_COUNT=$PharmacyCount; path=/; domain=$cookie_server;\n";
}
else {
   print "Location: ../Login.html\n\n";
   exit(0);
}

#if ( $TYPE =~ /Admin/i || ($TYPE =~ /SuperUser/i && $PharmacyCount > 1) ) {
if ( $TYPE =~ /Admin/i || $PharmacyCount > 1 ) {
  &logActivity($USER, "SuperUser Logged in to ReconRx", NULL);
  print "Location: MyReconRx_Super.cgi\n\n";
} else {
  &logActivity($USER, "Logged in to ReconRx", $PH_ID);
  print "Location: MyReconRx.cgi?WHICHDB=$WHICHDB\n\n";
}

exit(0);

