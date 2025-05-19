require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp\;";

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

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

$ntitle = "<i>ReconRx ADMIN menu</i>";

# Name found already in isMember subroutine
print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {
  print qq#<!-- displayAdminPage -->\n#;

  $actions{"Single Pay - Assign  Payments"} = "ADMIN_SinglePay_Assign_Payments.cgi";
  $actions{"Single Pay - Review"}           = "ADMIN_SinglePay_Review.cgi";
  $actions{"Single Pay - Sent"}             = "ADMIN_SinglePay_Sent.cgi";

# Don't include
# $actions{"Single Pay - Process Payments"} = "ADMIN_SinglePay_Process_Payments.cgi";

# print qq#<div id="textarea2" style="padding-bottom:40px;" class="notices">\n#;

  my $Target;

  print qq#<table cellpadding=3 cellspacing=3 border=0>\n#;
  foreach $action ( sort keys %actions ) {
     if ( $actions{$action} =~ /tools/i ) {
        $Target = qq#target="_Blank"#;
     } else {
        $Target = "";
     }
     print qq#<tr> <td><a href="$actions{$action}" $Target>$action</a></td> </tr>\n#;
  }
  print qq#</table>\n#;

  print qq#      <li><i><font color=red>165 Pharmacies needed. Current: $ReconPharmaciesCount</font></i></a></li>\n# if ($ReconPharmaciesCount);
# print qq#</div>\n#;
# print qq#<!-- end  textarea2 --> \n#;
}

#______________________________________________________________________________
