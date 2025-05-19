require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$dbin     = "TPDBNAME";
$db       = $dbin;
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBTPNDS{"$dbin"};
$FIELDS2  = $DBTPNDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

#______________________________________________________________________________

&readsetCookies;
&readPharmacies;

#______________________________________________________________________________

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

#______________________________________________________________________________

$ntitle = "ReconRx Vendors";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayVendors;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayVendors {
  if (!$dbx) {
    $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

    DBI->trace(1) if ($dbitrace);
  }

  my $sql  = "SELECT Vendor_Name, Business_Phone, Website, Email_Address, Logo, Documents_Path, Documents
                FROM officedb.vendor 
               WHERE Status = 'Active' 
                  && inReconRx = 'Yes' 
            ORDER BY inReconRxWeight";

  my $vendors = $dbx->prepare("$sql");
  $vendors->execute;

  my $NumOfRows = $vendors->rows;

  if ($NumOfRows > 0) {
    print "<div class='vendor_block'>";
    print "<div class='lj_blue_bb lj_blue_header'>Vendors</div>\n";

    while ( my ($Vendor_Name, $Business_Phone, $Website, $Email_Address, $Logo, $Documents_Path, $Documents) = $vendors->fetchrow_array() ) {
       my $Name_Link = "";
       my $img = '';

       if ($Logo !~ /^\s*$/) {
         $img = '<img src="data:image/jpeg;base64, '. $Logo .'" style="max-width: 192px;"/>';
       }
 
       if ($Website !~ /^\s*$/) {
         if ($Website !~ /^http/) {
           $Website = "http://".$Website;
	 }
         $Name_Link = qq#<a href="$Website" target="_blank">$img</a>#;
       } else {
         $Name_Link = qq#$Vendor_Name#;
       }
	   
       print "<div class='vendor_link'>$Name_Link</div>";
    }
    print "</div>\n";
  }
  
  $vendors->finish;
  $dbx->disconnect;
}

#______________________________________________________________________________
