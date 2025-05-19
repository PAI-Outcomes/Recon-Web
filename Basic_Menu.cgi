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
$ntitle = "<i>Basic Pharmacy ADMIN menu</i>";

print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {
  my $border = '';

  print qq#<!-- displayAdminPage -->\n#;
  print "sub displayAdminPage: Entry.<br>\n" if ($debug);

  print "<hr>\n";

  if($USER == 1694 && !$PH_ID ) { 
    $actions{"Total Sales Report"} = "";
    $border = 'class = noborders'; 
  }
  else {
    $actions{"Claim Research Tool"} = "Basic_Claim_Research_Tool.cgi";
    $actions{"Payment Research Tool"} = "Basic_Payment_Research_Tool.cgi";
  }
##  $actions{"835: 835 Not Set Up Reporting"}= "ADMIN_835_Not_Set_Up.cgi";
##  $actions{"835 Authorization Forms"}= "/tools/authorization_forms.php";
##  $actions{"Review TPP Aging by Pharmacy"} = "ADMIN_Review_TPP_Aging_by_Pharmacy.cgi";
##  $actions{"Detailed DB Search (office only)"} = "/tools/claimsearch.php";
##  $actions{"Post Check with No Remit Menu"} = "ADMIN_Post_Check_with_No_Remit_Menu.cgi";

  my $Target;
  print qq#<table $border cellpadding=3 cellspacing=3 border=0>\n#;
  foreach $action ( sort keys %actions ) {
     if ( $actions{$action} =~ /tools/i ) {
        $Target = qq#target="_Blank"#;
     } else {
        $Target = "";
     }
     print qq#<tr> <td><a href="$actions{$action}" $Target>$action</a></td> </tr>\n#;
  }
  print qq#</table>\n#;

##  print qq#      <li><i><font color=red>165 Pharmacies needed. Current: $ReconPharmaciesCount</font></i></a></li>\n# if ($ReconPharmaciesCount);

  print "sub displayAdminPage: Exit.<br>\n" if ($debug);

}

#______________________________________________________________________________
