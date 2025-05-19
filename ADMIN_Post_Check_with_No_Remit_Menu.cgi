require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp\;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

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

#______________________________________________________________________________

&hasAccess($USER);

if ( $ReconRx_Admin_Post_Check_with_No_Remit_Menu !~ /^Yes/i ) {
   print qq#<p class="yellow"><font size=+1><strong>\n#;
   print qq#$prog<br><br>\n#;
   print qq#<i>You do not have access to this page.</i>\n#;
   print qq#</strong></font>\n#;
   print qq#</p><br>\n#;
   print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

   &trailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

($progname = $prog) =~ s/_/ /gi;
$ntitle = "<i>ReconRx $progname</i>";

# Name found already in isMember subroutine
#print qq#<h3>$ntitle - $LFirstName $LLastName ( $USER )</h3>\n#;
print qq#<h3>$ntitle</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {
  print qq#<!-- displayAdminPage -->\n#;

  $actions{"Archive/Status Tool Menu"} = "ADMIN_Post_Check_with_No_Remit_Archive_Status_Menu.cgi";
  $actions{"Posting Tool"}        = "ADMIN_PCWNR_Posting_Tool.cgi";
  $actions{"Request 835 Tool"}        = "ADMIN_PCWNR_Request.cgi";

  $actionorder{"Posting Tool"}             = 1;
  $actionorder{"Archive/Status Tool Menu"} = 2;
  $actionorder{"Request 835 Tool"} = 3;

# print qq#<div id="textarea2" style="padding-bottom:40px;" class="notices">\n#;

  print qq#<table cellpadding=3 cellspacing=3 border=0>\n#;
  foreach $action ( sort {$actionorder{$a} <=> $actionorder{$b} } keys %actions ) {
     print qq#<tr> <td><a href="$actions{$action}">$action</a></td> </tr>\n#;
  }
  print qq#</table>\n#;

  print qq#      <li><i><font color=red>165 Pharmacies needed. Current: $ReconPharmaciesCount</font></i></a></li>\n# if ($ReconPharmaciesCount);
# print qq#</div>\n#;
# print qq#<!-- end  textarea2 --> \n#;
}

#______________________________________________________________________________
