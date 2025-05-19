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

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$fileyear  = $year-1;
$tmpmonth  = $month;
$tmpmonth  = 12 if ($tmpmonth == 0);
$tmpmonth2 = $tmpmonth -1;

$dispmonth  = $FMONTHS{$tmpmonth};
$dispmonth2 = $FMONTHS{$tmpmonth-1};
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$areteBT = 0;
my $webpathAC;

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

$ntitle = " Reports Menu Aggregated";

print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&displayAdminPage;

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {
  print qq#<!-- displayAdminPage -->\n#;
  print "sub displayAdminPage: Entry.<br>\n" if ($debug);

  my $Target = qq#target="_Blank"#;
  print qq#<table class='noborders' cellpadding=3 cellspacing=3 >\n#;
    print qq#<tr><td>#;

      print qq#<div class='ReportMenuDivs' >\n#;
        print qq# <div class='ReportDivHeader'>Third Party Payer</div>#;
        print qq# <ul class='ReportUL'>#;
        print qq# <li><div><a href="Total_Sales_Report_Aggregated.cgi" $Target>Total Sales</a></div></li> #;
        print qq#</ul></div>\n#;
    print qq#</td>#;
    print qq#<td>#;
      print qq#<div class='ReportMenuDivs' >\n#;
        print qq# <div class='ReportDivHeader'>Accounts Receivable</div>#;
        print qq# <ul class='ReportUL'>#;
        print qq# <li><div><a href="Review_My_Accounts_Receivable.cgi">End Of Month</a></div> \n#;
        print qq#</ul></div>\n#;
    print qq#</td></tr>#;

    print qq#<tr><td>#;
      print qq#<div class='ReportMenuDivs' >\n#;
        print qq# <div class='ReportDivHeader'>Reconciled Summary</div>#;
        print qq# <ul class='ReportUL'>#;
        print qq# <li><div><a href="Review_My_Reconciled_Claims_Monthly.cgi" $Target>End Of Month</a></div> \n#;
		print qq# <li><div><a href="YTD_Reconciled_Claims_Summary.cgi">YTD Reconciled Claims Summary</a></div> \n#;
		print qq# <li><div><a href="Review_My_Reconciled_Claims_Quarterly.cgi">QTR Reconciled Claims Summary</a></div> \n#;
        print qq#</ul></div>\n#;
      print qq#</td>#;
      print qq#<td>#;
      print qq#<div class='ReportMenuDivs' >\n#;
      print qq# <div class='ReportDivHeader'>Remittance Detail</div>#;
      print qq# <ul class='ReportUL'>#;
      #print qq# <li><div><a href="Reconciled_Detail_Remittance.cgi" $Target>Reconciled Remittance Detail</a></div>\n#;
      print qq#</ul></div>\n#;
      print qq#</td></tr>#;
       

  print qq#</table>\n#;

  print "sub displayAdminPage: Exit.<br>\n" if ($debug);

}

#______________________________________________________________________________
