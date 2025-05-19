
##use strict;
##use warnings;

use JSON; #if not already installed, just run "cpan JSON"
use CGI;
use DBI;
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/MyData/RBSReporting_routines.pl";

my $cgi = CGI->new;

print $cgi->header('application/json;charset=UTF-8');

my $ncpdp        = $cgi->param('ncpdp');    
my @row;

my $db_office        = 'officedb';
my $tbl_pharmacy     = 'pharmacy';
my $tbl_pharmacy_coo = 'pharmacy_coo';


&Get_Pharmacy_Data;

#convert  data to JSON
my $op = JSON -> new -> utf8 -> pretty(1);
my $json = $op -> encode({
    result           => $ncpdp,
    name             => $row[0], 
    npi              => $row[1],
    legal            => $row[2],
    taxcls           => $row[3],
    taxid            => $row[4],
    address          => $row[5],
    city             => $row[6],
    state            => $row[7],
    zip              => $row[8],
    mail_addr        => $row[9],
    mail_city        => $row[10],
    mail_state       => $row[11],
    mail_zip         => $row[12],
    recon_sts        => $row[13],
    med_num          => $row[14],
    prim_swtch       => $row[15],
    sec_swtch        => $row[16],
    swvendor         => $row[17],
    phone            => $row[18],
    fax              => $row[19],
    email            => $row[20],
    comm_pref        => $row[21],
    eoy              => $row[34],
    recon_sts_cl     => $row[35]

});

print $json;;

sub Get_Pharmacy_Data {

my %attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error_batch );
my $dbx = DBI->connect("DBI:mysql:$RIDBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error_batch;

  my $sql;
  my $sthx;
  my $row_cnt;

  $sql = " 
   SELECT Pharmacy_Name, NPI, Legal_Name, Fed_Tax_Classification, FEIN, Address, City, State, Zip, Mailing_Address, Mailing_City, Mailing_State, Mailing_Zip,status_reconrx,
          Medicaid_Primary_Num, Primary_Switch, Secondary_Switch, Software_Vendor, Business_Phone, Fax_Number, Email_Address, Comm_Pref, EOY_Report_Date, Status_ReconRx_Clinic
     FROM $db_office.$tbl_pharmacy
    WHERE NCPDP = $ncpdp
      AND Status_ReconRx = 'Active'
    UNION
   SELECT Pharmacy_Name, NPI, Legal_Name, Fed_Tax_Classification, FEIN, Address, City, State, Zip, Mailing_Address, Mailing_City, Mailing_State, Mailing_Zip,status_reconrx,
          Medicaid_Primary_Num, Primary_Switch, Secondary_Switch, Software_Vendor, Business_Phone, Fax_Number, Email_Address, Comm_Pref, EOY_Report_Date, Status_ReconRx_Clinic
     FROM $db_office.$tbl_pharmacy_coo
    WHERE NCPDP = $ncpdp 
      AND Status_ReconRx = 'Active'
    LIMIT 1
  "; 

  $sthx    = $dbx->prepare("$sql");
  $row_cnt = $sthx->execute;

##  print "SQL:\n$sql\n\n" ;

  if ( $row_cnt > 0 ) { 
    @row = $sthx->fetchrow_array();
    
  }
  $sthx->finish;
}

