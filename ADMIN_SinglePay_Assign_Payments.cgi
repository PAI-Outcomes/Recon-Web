use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   exit(0);
}

#______________________________________________________________________________

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

#______________________________________________________________________________

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&getSinglePayCustomers;
&showPending;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
sub showPending {
  my $DBNAME = "reconrxdb";
  my $TABLE  = "singlepay";

  my $sql = "SELECT Status, TransferDate, DepositDate, PaymentType, CheckInfo, Amount, PharmacyName, NCPDPSelected, SPGroup
               FROM $DBNAME.$TABLE sp
              WHERE Status = 'Pending'";

  my $sthp  = $dbx->prepare("$sql");
  $sthp->execute;
  
  print qq#<p>The following transactions have not yet been assigned to a pharmacy/group:</p>#;
  print qq#<table class="borders">#;
  print qq#
  <tr>
  <th>Transfer</th>
  <th>Deposited</th>
  <th>Payment Type</th>
  <th>Check</th>
  <th>Amount</th>
  <th class="align_right">Select Store</th>
  </tr>
  \n#;
  
  while ( my ($Status, $TransferDate, $DepositDate, $PaymentType, $Check, $Amount, $PharmacyName, $NCPDPSelected, $SPGroup) = $sthp->fetchrow_array() ) {
    print qq#
	<tr>
	<td>$TransferDate</td>
	<td>$DepositDate</td>
	<td>$PaymentType</td>
	<td>$Check</td>
	<td class="money">$Amount</td>
	<td class="align_center">
	  <form action="ADMIN_SinglePay_Process_Payment.cgi" method="post">
	  <INPUT name='Check'  TYPE="hidden" VALUE="$Check">
	  <INPUT name='Amount' TYPE="hidden" VALUE="$Amount">
          <INPUT name='Condition' TYPE="hidden" VALUE="Assign">
	  <INPUT class="button-form" TYPE="submit" VALUE="Process">
	  </form>
	</td>
	</tr>\n#;	
  }
  print qq#</table>#;
  $sthp->finish;
}

#______________________________________________________________________________

sub getSinglePayCustomers {
  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";
  
  %SP_NCPDPs = ();
  %SP_NAMEs  = ();

  my $sql = "SELECT NCPDP, Pharmacy_Name 
               FROM $DBNAME.$TABLE
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                AND Single_Pay = 'Yes'";
  my $sthsp  = $dbx->prepare("$sql");
  $sthsp->execute;
  my $numofrows = $sthsp->rows;

  if ($numofrows > 0) {
    while ( my ($ncpdp, $name) = $sthsp->fetchrow_array() ) {
	  my $key = "$ncpdp##$name";
	  $SP_NCPDPs{$key} = $ncpdp;
	  $SP_NAMEs{$key}  = $name;	  
    }
  }
  $sthsp->finish;
}

#______________________________________________________________________________
#______________________________________________________________________________
