require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp\;";

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

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

($ENV) = &What_Env_am_I_in;


#----------------------------------------------------------------#
print qq#<link type="text/css" media="screen" rel="stylesheet" href="/css/recon_style_members.css" /#;
print qq#<div>\n#;

  print qq#
  <div class="BusinessTools">
  <img src="/images/icons/pill.png" style="vertical-align: middle;" />
  <span class="BusinessTools_Text"><a href="/cgi-bin/psp.cgi">Prescription Savings Program</a></span>
  </div>
  #;
  print qq#
  <div class="BusinessTools">
  <img src="/images/icons/bwmedsync.png" style="vertical-align: middle;" />
  <span class="BusinessTools_Text"><a href="/cgi-bin/MedSync_Rpt.cgi">Med Sync Report</a></span>
  </div>
  #;
  print qq#
  <div class="BusinessTools">
  <img src="/images/icons/verified7.png" style="vertical-align: middle;" />
  <span class="BusinessTools_Text"><a href="/cgi-bin/Inventory_Rpt.cgi">  Inventory Management Report</a></span>
  </div>
  #;
 


print qq#</div>\n#;


##&MyPharmassessMembersTrailer;

exit(0);
