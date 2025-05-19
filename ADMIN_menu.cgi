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

&readsetCookies;

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
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

#______________________________________________________________________________

$Pharmacy_Name = $Pharmacy_Names{$PH_ID};
$ntitle = "<i>ReconRx ADMIN menu</i>";

print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {

  print qq#<TABLE border="1">#;
  print qq#<TR>#;
  print qq#<TD style="vertical-align:top">#;
  print qq#<TABLE width="100%">#;
  print qq#<TR>#;
  print qq#<TD style="text-align:center;font-weight: bold;font-size:15px;background-color:powderblue;">Daily</TD>#;  
  print qq#</TR>#;
  print qq#<TR>#;
  print qq#<TD>#;
  print qq#<a href="ADMIN_Aging_Research.cgi">Aging Research</a><BR>#;
  print qq#<a href="ADMIN_Claim_Research_Request.cgi">Claim Research Request</a><BR>#;
  print qq#<a href="ADMIN_Payment_Research.cgi">Payment Research</a><BR>#;
  print qq#<a href="ADMIN_Missing_Payment_Request.cgi">Missing Payment Request</a><BR>#;
  print qq#<a href="/tools/datatracking.php" target="_Blank">First/Last Remit</a><BR>#;
  print qq#<a href="ADMIN_Post_Check_with_No_Remit_Menu.cgi">Post Check with no Remit</a><BR>#;
  print qq#<a href="/tools/authorization_forms.php" target="_Blank">Authorization Forms</a><BR>#;
  print qq#<a href="ADMIN_835_Setup_Request.cgi">835 Setup Request<a><BR>#;
  print qq#</TD>#;
  print qq#</TR>#;
  print qq#</TABLE>#;
  print qq#</TD>#;
  print qq#<TD style="vertical-align:top">#;
  print qq#<TABLE width="100%">#;
  print qq#<TR>#;
  print qq#<TD style="text-align:center;font-weight: bold;font-size:15px;background-color:powderblue;">Specialty</TD>#;  
  print qq#</TR>#;
  print qq#<TR>#;
  print qq#<TD>#;
  if ( $USER =~ /66|70|74|69|2387/ ) {
    print qq#<a href="ADMIN_SinglePay.cgi">Single Pay</a><BR>#;
  }
  if ( $USER =~ /66|70|74|69/ ) {
    print qq#<a href="TPP_835_File_Inventory.cgi">TPP Inventory</a><BR>#;
    print qq#<a href="ADMIN_Dashboard_Pending_Remits_Tool.cgi">Dashboard Pending Remits</a><BR>#;
    print qq#<a href="ADMIN_Dashboard_Aging_Tool.cgi">Dashboard Aging</a><BR>#;
    print qq#<a href="ADMIN_835_Not_Set_Up.cgi">835 Not Set Up</a><BR>#;
    print qq#<a href="ADMIN_All_Stores_Aging.cgi">All pharmacy aging</a><BR>#;
    print qq#<a href="ADMIN_All_TPP_Aging.cgi">All TPP aging</a><BR>#;
    print qq#<a href="ADMIN_Review_TPP_Aging_by_Pharmacy.cgi">TPP Aging By Pharmacy</a><BR>#;
  }
  print qq#</TD>#;
  print qq#</TR>#;
  print qq#</TABLE>#;
  print qq#</TD>#;
  print qq#</TR>#;
  print qq#<TR>#;
  print qq#<TD style="vertical-align:top">#;
  print qq#<TABLE width="100%">#;
  print qq#<TR>#;
  print qq#<TD style="text-align:center;font-weight: bold;font-size:15px;background-color:powderblue;">Optional</TD>#;  
  print qq#</TR>#;
  print qq#<TR>#;
  print qq#<TD>#;
  print qq#<a href="/tools/claimsearch.php" target="_Blank">Detailed Search</a><BR>#;
  print qq#<a href="ADMIN_835_PSAO_Payers.cgi">Central Pay TPP Sheet</a><BR>#;
  print qq#<a href="ADMIN_TCode_Defs.cgi">TCode</a><BR>#;
  print qq#</TD>#;
  print qq#</TR>#;
  print qq#</TABLE>#;
  print qq#</TD>#;
  print qq#<TD style="vertical-align:top">#;
  print qq#<TABLE width="100%">#;
  print qq#<TR>#;
  print qq#<TD style="text-align:center;font-weight: bold;font-size:15px;background-color:powderblue;">Manager</TD>#;  
  print qq#</TR>#;
  print qq#<TR>#;
  print qq#<TD>#;
  if ( $USER =~ /66|69|2542/ ) {
    print qq#<a href="ADMIN_Auth_Claims.cgi">RAM Archive Request Approval</a><BR>#;
    print qq#<a href="ADMIN_Archiving.cgi">Archive</a><BR>#;
    print qq#<a href="ADMIN_Date_Reconciliation_Archiving.cgi">Date Reconciliation Archive</a><BR>#;
    print qq#<a href="ADMIN_835_Exclusion_List.cgi">835 Setup Exclusion List</a><BR>#;
  }
  print qq#</TD>#;
  print qq#</TR>#;
  print qq#</TABLE>#;
  print qq#</TD>#;
  print qq#</TR>#;
  if ( $USER =~ /^66$|^2542$/ ) {
    print qq#<TR>#;
    print qq#<TD style="vertical-align:top">#;
    print qq#<TABLE width="100%">#;
    print qq#<TR>#;
    print qq#<TD style="text-align:center;font-weight: bold;font-size:15px;background-color:powderblue;">Admin</TD>#;  
    print qq#</TR>#;
    print qq#<TR>#;
    print qq#<TD>#;
    print qq#<a href="/tools/Admin_Form_Setup.php" target="_Blank">Admin Form Setup</a><BR>#;
    print qq#<a href="ADMIN_Add_SuperUser.cgi">Add SuperUser</a><BR>#;
    print qq#<a href="ADMIN_Dashboard_Unreconcile_Remits_Tool.cgi">Unreconcile/Remove Remits</a><BR>#;
    print qq#</TD>#;
    print qq#</TR>#;
    print qq#</TABLE>#;
    print qq#</TD>#;
    print qq#<TD style="vertical-align:top">#;
    print qq#<TABLE width="100%">#;
    print qq#<TR>#;
    print qq#<TD style="text-align:center;font-weight: bold;font-size:15px;background-color:powderblue;">Dump</TD>#;  
    print qq#</TR>#;
    print qq#<TR>#;
    print qq#<TD>#;
    print qq#<a href="ADMIN_Data_Dump.cgi">Data Dump</a><BR>#;
    print qq#</TD>#;
    print qq#</TR>#;
    print qq#</TABLE>#;	
    print qq#</TD>#;
    print qq#</TR>#;
  }
  print qq#</TABLE>#
}

#______________________________________________________________________________
