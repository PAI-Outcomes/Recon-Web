require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

&readsetCookies;
&readPharmacies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported as 0-11, 0==January, so add one!
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$TODAY  = sprintf("%04d02d02d000000", $year, $month, $day);

$curyear = $year;
$cym1    = $curyear - 1;

if ( $month >= 10 ) {
   $curQTR  = 4;
} elsif ( $month >= 7 ) {
   $curQTR  = 3;
} elsif ( $month >= 4 ) {
   $curQTR  = 2;
} else {
   $curQTR  = 1;
}
#______________________________________________________________________________

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
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

#______________________________________________________________________________

&readInterventions;
&readAffiliates;
&readVendors;
&readThirdPartyPayers;

$FMT = "%0.02f";

#______________________________________________________________________________

&displayWebPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
   print qq#<!-- displayWebPage -->\n#;

   ($PROG = $prog) =~ s/_/ /g;

   $report = "PRT_Int_Success_Stories_${USER}";
   &Do_Interventions_Report($report);

   $report = "PRT_Int_Success_Stories_ALL";
   &Do_Interventions_Report($report);
}
#______________________________________________________________________________

sub Do_Interventions_Report {
  my ($report) = @_;


  my $jrep = "";
  my $dorep = "";

  if ( $report =~ /ALL$/i ) {
     $dorep   = "ALL";
     $DOINTSS = "ALL";
     $jrep = $dorep;
  } 
  elsif ($PH_ID eq 'Aggregated') {
     $dorep   = $PH_ID;
     $jrep = "Aggregated";
  }
  else {
     $dorep   = $PH_ID;
     $DOINTSS = $PH_ID;
     $jrep = $Pharmacy_Name;
  }

  print qq#<table class="main">\n#;
  print "<tr>\n";

  print "<th colspan=1 align=left><h1 class=\"page_title\">$jrep Success Stories</h1></th>\n";
  print "<th colspan=2 align=right><font size=-2><i>* Current year to date and, if first quarter, previous year too</i></font></th>\n";

  print "</tr>\n";
  print "<tr>\n";
  print qq#<th class="align_left"  width=50%>Third Party</th> \n#;
  print qq#<th class="align_right" width=25%>Amount</th> \n#;
  print qq#<th class="align_left">Recovered</th> \n#;
  print qq#</tr>\n#;

  my @sortit = sort { $Int_Closed_Date{$b} cmp $Int_Closed_Date{$a} } keys %Intervention_IDs;

  $processedcount = 0;
  $Total_Success_Story = 0;

  foreach $Int_ID (@sortit) {
     my $Int_Pharmacy_ID   = $Int_Pharmacy_ID{$Int_ID};
     my $Int_Pharmacy_Name = $Pharmacy_Names{$Int_Pharmacy_ID};
     next if ( !$Int_Pharmacy_Name );
     my $Int_Success_Story = $Int_Recon_Success_Story{$Int_ID};

     next if ( $Int_Success_Story <= 0 );

     next if ( $PH_ID != $Int_Pharmacy_ID && $dorep !~ /ALL/i && $PH_ID ne 'Aggregated');
     next if ($PH_ID eq 'Aggregated' && $Agg_String !~ $Int_Pharmacy_ID && $dorep !~ /ALL/i);
     

     my $Int_Status          = $Int_Status{$Int_ID};
	 
     my ($Int_Closed_Date, $p2) = split(" ", $Int_Closed_Date{$Int_ID}, 2);

     $Int_Closed_Date_Year = substr($Int_Closed_Date, 0, 4);
     $Int_Closed_Date_Mon  = substr($Int_Closed_Date, 5, 2);
     $Int_Closed_Date_Day  = substr($Int_Closed_Date, 8, 2);

     my $display = 0;
     $display++ if ( $Int_Closed_Date_Year == $curyear );
     $display++ if ( $Int_Closed_Date_Year == $cym1 && $curQTR == 1 );
     next if ( !$display );

     $Int_Closed_Date = $Int_Closed_Date_Mon ."/" . $Int_Closed_Date_Day . "/" . $Int_Closed_Date_Year;
 
     $Int_Type            = $Int_Type{$Int_ID};
     $Int_Type_ID         = $Int_Type_ID{$Int_ID};
 
     if ( $Int_Type =~ /Pharmacy/i ) {
        $what = $Pharmacy_Names{$Int_Type_ID};
        $ITYPE = "$what";
     } elsif ( $Int_Type =~ /Vendor/i ) {
        $what = $Vendor_Names{$Int_Type_ID};
        $ITYPE = "$what";
     } elsif ( $Int_Type =~ /ThirdPartyPayer/i ) {
        $what = $TPP_Names{$Int_Type_ID};
        $ITYPE = "$what";
     } elsif ( $Int_Type =~ /Affiliate/i ) {
        $what = $Affiliate_Names{$Int_Type_ID};
        $ITYPE = "$what";
     } else {
        $what = "$Int_Type - $Int_Type_ID";
        $ITYPE = "???: $what";
     }
     
     $processedcount++;

     if ( $dorep =~ /ALL$/i ) {
        $Total_Success_Story += $Int_Success_Story;
     } elsif ( $Int_Pharmacy_ID =~ /^$dorep$/ ) {
        $Total_Success_Story += $Int_Success_Story;
     } elsif ($Agg_String =~ $Int_Pharmacy_ID) {
        $Total_Success_Story += $Int_Success_Story;
     }
 
     print "<tr>";
     print qq#<td>$ITYPE</td>#;
     $SSamt = "\$" . &commify(sprintf("$FMT", $Int_Success_Story));
     print qq#<td nowrap class="align_right grey">$SSamt</td>#;
     print qq#<td>$Int_Closed_Date</td>#;
     print qq#</tr>\n#;
  }
  if ( $processedcount) {
     my $plural = "s" if ( $processedcount > 1 );
     if ( $dorep =~ /^ALL$/i ) {
        $msg = "$processedcount Success Stories found";
     } else {
        $msg = "$processedcount $jrep Success Stories found";
     } 
  } else {
     $msg = "No $jrep Success Stories found yet";
  }
  print qq#<tr>#;
  print qq#<th class="align_left lj_blue text_white">Total Success Stories</th>\n#;

  $SSamt = "\$" . &commify(sprintf("$FMT", $Total_Success_Story));
  print qq#<th class="align_right lj_blue text_white">$SSamt</th>#;
  print qq#<th class="align_right lj_blue text_white">$nbsp</th>#;
  print qq#</tr>\n#;
  print qq#<tr><th colspan=3 class="align_left">$msg</th></tr>#;
  print "</table>\n";

  print "<br>\n";
}

#______________________________________________________________________________
