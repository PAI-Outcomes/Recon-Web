
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
($prog, $dir, $ext) = fileparse($0, '\..*');

&readsetCookies;
&readPharmacies;

if ( $USER ) {
  $inNCPDP = $Pharmacy_NCPDPs{$PH_ID};
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    $inNCPDP = $USER;
    &ReconRxAggregatedHeaderBlock_New;
  }
  else {
    &ReconRxHeaderBlock;
  }
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

$ntitle = "Watch a Web Training Session";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebTraining;
&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebTraining {
  $training = 'https://www.youtube.com/embed/1PeUwiXDf7g';
  print qq#<!-- displayWebTraining -->\n#;
  print <<WEB;
	
    <p>Watch the video below for more information about utilizing the ReconRx members section.</p>
    <iframe width="480" height="320" src="$training?rel=0" frameborder="0" allowfullscreen></iframe>
WEB
}
