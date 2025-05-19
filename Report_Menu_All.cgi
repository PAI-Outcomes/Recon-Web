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

if ( $USER && $PH_ID ne "Aggregated") {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} elsif ( $USER && $PH_ID eq "Aggregated") {
  &MyReconRxHeader;
  &ReconRxAggregatedHeaderBlock_New;
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

&readPharmacies;
&login_rpt_ctl;

#print "PH_ID: $PH_ID\n";
#print "USER: $USER\n";

if ($PH_ID ne "Aggregated") {
	$NCPDP = $Pharmacy_NCPDPs{$PH_ID};
	$EOYACFName = "ReconRx_End_of_Fiscal_Year_Accounts_Receivable_${NCPDP}_${PH_ID}_$fileyear.xlsx";
	$ReimTrkng  = "ReimbursementTracking_${NCPDP}_${PH_ID}_$dispmonth.xlsx";
	$ReimTrkng2 = "ReimbursementTracking_${NCPDP}_${PH_ID}_$dispmonth2.xlsx";
	$EOYFName   = "ReconRx_End_of_Fiscal_Year_Reconciled_Claims_Summary_${NCPDP}_${PH_ID}_$fileyear.xlsx";
} else {
	$NCPDP = $Pharmacy_NCPDPs{$PH_ID};
	$EOYACFName = "ReconRx_End_of_Fiscal_Year_Accounts_Receivable_${USER}_Aggregated_$fileyear.xlsx";
	$EOYFName   = "ReconRx_End_of_Fiscal_Year_Reconciled_Claims_Summary_${USER}_Aggregated_$fileyear.xlsx";
}

my $outdir    = qq#D:\\WWW\\members.recon-rx.com\\WebShare\\#;
if ($PH_ID ne "Aggregated") {
	$webpathRec = "$outdir\\End_of_Fiscal_Year_Reconciled_Claims\\$EOYFName";
	$webpathAC  = "$outdir\\End_of_Fiscal_Year$testing\\$EOYACFName";
	$webpathRT  = "$outdir\\ReimbursementTracking\\$ReimTrkng";
	$webpathRT2 = "$outdir\\ReimbursementTracking\\$ReimTrkng2";
} else {
	$webpathRec = "$outdir\\End_of_Fiscal_Year_Reconciled_Claims\\Aggregated\\$EOYFName";
	$webpathAC  = "$outdir\\End_of_Fiscal_Year$testing\\Aggregated\\$EOYACFName";
}

 #print "webpathRec: $webpathRec\n";
 #print "webpathAC: $webpathAC\n";

#______________________________________________________________________________

$Pharmacy_Name = $Pharmacy_Names{$PH_ID};
$ntitle = " All Reports Menu";

print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

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
        print qq# <div class='ReportDivHeader'>Accounts Receivable</div>#;
        print qq# <ul class='ReportUL'>#;
        print qq# <li><div><a href="Review_My_Accounts_Receivable_Monthly.cgi" $Target>End Of Month</a></div> \n#;
        if (-e $webpathAC) {
          print qq# <li><div><a href="Review_My_Accounts_Receivable_Yearly.cgi">End Of Year</a></div> \n#;
        }
		if ($PH_ID ne "Aggregated") {
			print qq# <li><div><a href="Review_My_Aging_Detailed.cgi" $Target>Current Aging Detail</a></div> \n#;
		}
        print qq#</ul></div>\n#; 
    print qq#</td>#;
    print qq#<td>#;	
	print qq#<div class='ReportMenuDivs' >\n#;
        print qq# <div class='ReportDivHeader'>Reconciled Claims</div>#;
        print qq# <ul class='ReportUL'>#;
        print qq# <li><div><a href="Review_My_Reconciled_Claims_Monthly.cgi" $Target>End Of Month</a></div> \n#;
        print qq# <li><div><a href="Review_My_Reconciled_Claims_Yearly.cgi">End Of Year</a></div> \n#;
		print qq# <li><div><a href="YTD_Reconciled_Claims_Summary.cgi" $Target>YTD Reconciled Claims</a></div> \n#;
        if ($PH_ID ne "Aggregated") {		
		   #print qq# <li><div><a href="Review_My_PLB_Monthly.cgi" $Target>Monthly PLB</a></div> \n#;
        } else {
           #print qq# <li><div><a href="Review_My_PLB_Monthly_Aggregated.cgi" $Target>Monthly PLB</a></div> \n#;
        }		
		print qq# <li><div><a href="Reconciled_Detail_Remittance.cgi" $Target>Remittance Detail</a></div>\n#;
        print qq#</ul></div>\n#; 
    print qq#</td></tr>#;
    print qq#<tr><td>#;   		
      print qq#<div class='ReportMenuDivs' >\n#;
      print qq# <div class='ReportDivHeader'>Special</div>#;
      print qq# <ul class='ReportUL'>#;
      print qq# <li><div><a href="M3P.cgi" $Target>M3P</a></div></li> \n#;
      if ($PH_ID eq "Aggregated" && $nrid_rpt{$USER}) {
        print qq# <li><div><a href="NRID.cgi" $Target>NRID</a></div></li> \n#;
      }
      if ($PH_ID eq "Aggregated" && $copay_rpt{$USER}) {
        print qq# <li><div><a href="Copay_Menu_All.cgi" $Target>COPAY</a></div></li> \n#;
      }
      print qq#</ul></div>\n#;	  
    print qq#</td>#;	  
	print qq#<td>#;
      print qq#<div class='ReportMenuDivs' >\n#;
        print qq# <div class='ReportDivHeader'>Total Sales</div>#;
        print qq# <ul class='ReportUL'>#;
		if ($PH_ID ne "Aggregated") {
			print qq# <li><div><a href="TotalSalesRpt_Summary.cgi" $Target>Summary</a></div></li> #;
			print qq# <li><div><a href="TotalSalesRpt_Dtl.cgi" $Target>Detail</a></div></li> \n#;						
		} else {
			print qq# <li><div><a href="Total_Sales_Report_Aggregated.cgi" $Target>End Of Month</a></div></li> #;
		}
        print qq#</ul></div>\n#;
	print qq#</td></tr>#;
	
    if ($Pharmacy_Arete{$PH_ID} =~ /^B|E$/) {
      $tmpdate = $Pharmacy_Active_Date_ReconRxs{$PH_ID};
      $tmpdate =~ s/-//g;
      if ($tmpdate > 20200630) {
        $areteBT = 1;
        print qq#<tr><td>#;
        print qq#<div class='ReportMenuDivs'>\n#;
        print qq# <div class='ReportDivHeader'>Business</div>#;
        print qq# <ul class='ReportUL'>#;
		print qq# <li><div><a href="psp.cgi"$Target>Prescription Savings Program</div> \n#;
		print qq# <li><div><a href="MedSync_Rpt.cgi"$Target>Med Sync Report</div> \n#;
		print qq# <li><div><a href="Inventory_Rpt.cgi"$Target>Inventory Management Report</div> \n#;
        print qq#</ul></div>\n#;
        print qq#</td></tr>#;
      }
    } 
	
	if ($PH_ID ne "Aggregated") {
		if (-e $webpathRT || -e $webpathRT2) {
			if (!$areteBT) {
				print qq#<tr>#;
			}
			print qq#<td>#;
			print qq#<div class='ReportMenuDivs'>\n#;
			print qq# <div class='ReportDivHeader'>Reimbursement Tracking</div>#;
			print qq# <ul class='ReportUL'>#;
			print qq# <li><div><a href="ReimbursementTracking.cgi"$Target>End Of Month</div> \n#;				
			print qq#</ul></div>\n#;
			print qq#</td>#;
			if (!$areteBT) {
				print qq#</tr>#;
			}
		}
	}
       

  print qq#</table>\n#;

  print "sub displayAdminPage: Exit.<br>\n" if ($debug);

}

#______________________________________________________________________________
