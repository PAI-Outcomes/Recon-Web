
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Excel::Writer::XLSX;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

#####################$| = 1; # don't buffer output
($prog, $dir, $ext) = fileparse($0, '\..*');

&readsetCookies;
&readPharmacies;

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


#------------------------------------------------------------------------------
### Log Access

$Pharmacy_Name = $Pharmacy_Names{$PH_ID};
&logActivity($LOGIN, "ReconRx: Review My Aging Detailed", $PH_ID);
#------------------------------------------------------------------------------

$ntitle = "Aging Report - Excel Spreadsheet";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

&displayWebPage;
&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  print qq#
  <div id="loading">
    <p>We are creating your Detailed Aging report. This could take several minutes to generate,<br />please do not leave this page until the report is complete.</p>
	<br />
	<p><strong>A download link will be provided here when the report is ready.</strong></p>
    <img src="/images/loader_large.gif">
  </div>
  #;
  
print qq#
<script>
\$(document).ready(function() {
	\$.ajax({
		dataType: "html", 
		//type: "POST", 
		url: "/cgi-bin/Review_My_Aging_to_Excel.cgi", 
		data: { 
			jsNCPDP: "$PH_ID"
		}, 
		success: function(data, responseStatus) { 
			var file_csv = data.csv;
			\$('\#loading').html(data);
		}
	}).error(function() {
		\$('\#loading').html('<p>Error loading file, please contact us for assistance.</p><br />');
	});
});
</script>
#;
}


sub StripIt_local {
  my ($value) = @_;

  $value =~ s/^\s*(.*?)\s*$/$1/;
  $value =~ s/\/\s+\///g;

  return($value);
}

