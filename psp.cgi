require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp\;";

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

&readsetCookies;

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
   
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}


$ntitle = "Prescription Savings Program";
print qq#<h1>$ntitle</h1>\n\n#;

&printPSPInfo($PH_ID, "RBS");

&logActivity($LOGIN, "Accessed PSP Report in ReconRx", $PH_ID);

&MyReconRxTrailer;

exit(0);

