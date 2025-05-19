
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

my $Agg;
my $Agg2;

$| = 1; # don't buffer output

&readsetCookies;
&readPharmacies;

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    $Agg  = "\\Aggregated";
    $Agg2 = "/Aggregated";
    $inNCPDP = $USER;
    &ReconRxAggregatedHeaderBlock;
  }
  else {
  }

  $ID = $Reverse_Pharmacy_NCPDPs{$inNCPDP};
} 
else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;
  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

($ENV) = &What_Env_am_I_in;

$ntitle = "Reconciled Claims Report";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

&displayWebPage;
&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;

  print qq#<a href="YTD_Reconciled_Claims_Summary.cgi" target="_blank">YTD Reconciled Claims Summary</a>\n#;

}
