require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

my $USER       = $in{'USER'};
my $PASS       = $in{'PASS'};
my $RUSER      = $in{'RUSER'};
my $RPASS      = $in{'RPASS'};
my $VALID      = $in{'VALID'};
my $isAdmin    = $in{'isAdmin'};
my $isMember   = $in{'isMember'};
my $CUSTOMERID = $in{'CUSTOMERID'};
my $LTYPE      = $in{'LTYPE'};
my $JPHNPI     = $in{'JPHNPI'};
my $JPHLoginID = $in{'JPHLoginID'};
my $WHICHDB      = $in{'WHICHDB'};
my $OWNER      = $in{'OWNER'};
my $OWNERPASS      = $in{'OWNERPASS'};
my $LPERMISSIONLEVEL = $in{'LPERMISSIONLEVEL'};
my $LDATEADDED = $in{'LDATEADDED'};

($USER) = &StripJunk($USER);
($PASS) = &StripJunk($PASS);

my $submitvalue = "SAVE";

if ( $prog =~ /^index/i ) { $title = "Home"; } else { $title = "Log Out"; }
$title = qq#${RECONRXCOMPANY} - $title# if ( $RECONRXCOMPANY );
$title =~ s/_/ /g;

$USER    = "";
$PASS    = "";
$RUSER   = "";
$RPASS   = "";
$VALID   = 0;
$isAdmin = 0;
$isMember= 0;
$CUSTOMERID = "";
$LTYPE      = "";
$JPHNPI     =  0;
$JPHLoginID =  0;
$WHICHDB    = "";
$OWNER      = "";
$OWNERPASS  = "";
$LPERMISSIONLEVEL = "";
$LDATEADDED = "";
$PH_ID = "";

print qq#Set-Cookie:USER=$USER;             path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:PASS=$PASS;             path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:RUSER=$RUSER;           path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:RPASS=$RPASS;           path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:VALID=$VALID;           path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:isAdmin=$isAdmin;       path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:isMember=$isMember;     path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:CUSTOMERID=$CUSTOMERID; path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:LTYPE=$LTYPE;           path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:JPHNPI=$JPHNPI;         path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:JPHLoginID=$JPHLoginID; path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:WHICHDB=$WHICHDB;       path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:OWNER=$OWNER;           path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:OWNERPASS=$OWNERPASS;   path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:LPERMISSIONLEVEL=$LPERMISSIONLEVEL; path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:LDATEADDED=$LDATEADDED; path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:PH_ID=$PH_ID;           path=/; domain=$cookie_server;\n#;

print qq#Set-Cookie:USER_LoginID=$USER;     path=/; domain=$cookie_server;\n#;

print "Location: ../Login.html\n\n";

#______________________________________________________________________________

exit(0);
