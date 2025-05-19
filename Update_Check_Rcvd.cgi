# Post_Payment_to_Remits.cgi
#
require "D:/RedeemRx/MyData/vars.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DBI;

$| = 1; # don't buffer output
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________
#______________________________________________________________________________

my $cgi = CGI->new;

$DBNAME   = 'ReconRxDB';
$TABLE    = 'checks_rcvd';

print "DBNAME: $DBNAME, DBHOST:$dbhost, USER: $dbuser, PWD: $dbpwd,\n";

$dbz = DBI->connect("DBI:mysql:$DBNAME:$dbhost",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

$sql  = "REPLACE INTO $DBNAME.$TABLE (Pharmacy_ID, NCPDP, TPP, payment_method, check_number, check_amount, check_date, pendrecv) 
         VALUES ($in{Pharmacy_ID}, '$in{NCPDP}', '$in{TPP}', '$in{pay_meth}', '$in{chk_num}', '$in{chk_amt}', '$in{chk_date}', '$in{pendrecv}')";

$sth98 = $dbz->prepare($sql) || die "Error preparing query" . $dbz->errstr;
$sth98->execute() or die $DBI::errstr;
$NumOfRows = $sth98->rows;
$sth98->finish();

if ($NumOfRows > 0) {
  $retval = 'success';
}
else {
  $retval = 'failed';
}

print $cgi->header(-type => "application/json", -charset => "utf-8");
print $sql;

#______________________________________________________________________________

$dbz->disconnect;

exit(0);

#______________________________________________________________________________

