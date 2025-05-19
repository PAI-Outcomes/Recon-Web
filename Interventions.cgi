#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');

$title = "$prog";
$title = qq#${RECONRXCOMPANY} - $title# if ( $RECONRXCOMPANY );

$NowMinus30Days = time() - ( 30 * 24 * 60 * 60 );	# 30 days * 24 hours * 60 minutes * 60 seconds for Epoch time

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$dbin     = "INDBNAME";
$db       = $dbin;
$DBNAME   = $DBNAMES{"$dbin"};

#______________________________________________________________________________

&readsetCookies;
&readPharmacies;

if ($USER) {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} else {

  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January

# Connect to the Pharmacy database

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
DBI->trace(1) if ($dbitrace);
 
#______________________________________________________________________________

&displayInterventionsGlobal($PH_ID, "ReconRx");

#______________________________________________________________________________

# Close the Database
$dbx->disconnect;

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
