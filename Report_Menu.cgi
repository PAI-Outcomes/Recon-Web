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

print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {

  print qq#<!-- displayAdminPage -->\n#;
  print "sub displayAdminPage: Entry.<br>\n" if ($debug);

  print "<hr>\n";

  $actions{"Total Sales"} = "TotalSalesRpt_Summary.cgi";
  $actions{"Total Sales Detail"} = "TotalSalesRpt_Dtl.cgi";
  #$actions{"YTD Reconciled Claims Detail"} = "YTD_Reconciled_Claims_Dtl.cgi";
  $actions{"YTD Reconciled Claims"} = "YTD_Reconciled_Claims_Summary.cgi";
  

  my $Target;

  print qq#Third Party Payer Reports\n#;
  print "<hr>\n";
  print qq#<table class='noborders' cellpadding=3 cellspacing=3 border=0>\n#;
  foreach $action ( sort keys %actions ) {
     if ( $actions{$action} =~ /tools/i ) {
        $Target = qq#target="_Blank"#;
     } else {
        $Target = "";
     }
     print qq#<tr> <td><a href="$actions{$action}" $Target>$action</a></td> </tr>\n#;
  }
  print qq#</table>\n#;
  
  &BAC_Report;

  print "sub displayAdminPage: Exit.<br>\n" if ($debug);

}

sub BAC_Report {

  $ID = $Reverse_Pharmacy_NCPDPs{$inNCPDP};
  
  print "<br>\n";
  print "<br>\n";
  print "<hr>\n";
  print qq#Billed And Adjudicated Comparison Reports\n#;
  print "<hr>\n";
  print qq#<table class='noborders' cellpadding=3 cellspacing=3 border=0>\n#;
  foreach $action ( sort keys %actions ) {
    ## print qq#<tr> <td><a href="$actions{$action}" $Target>$action</a></td> </tr>\n#;
  }
  print qq#</table>\n#;
  $outdir    = qq#\\\\$WBSERVER\\Webshare (ReconRx)\\End_of_Month_BAC#;

  %EOMfiles  = ();
  %EOMFNAMES = ();

  opendir(DIR, "$outdir") or die $!;
  my @files = sort readdir(DIR);
  closedir(DIR);
  foreach $fname (@files) {
    my @pcs = split("_", $fname);
    my $ptr = @pcs;
    $ptr--;
    my $ptrM1 = $ptr -1 ;
    $pcs[$ptr] =~ s/\.xlsx//gi;
    my $threechar = substr($pcs[$ptr], 0, 3);

    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    if ( $PH_ID  ne 'Aggregated') {
      next if ( $fname !~ /${inNCPDP}_${ID}_/ ); 
    }
    else {
      next if ( $fname !~ /_${inNCPDP}_/ );
    }

    $ptrmonth = $months{$threechar};
    $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
    $dofiles{$key} = $fname;
  }

  foreach $key (sort { $b <=> $a } keys %dofiles) {

    $fname = $dofiles{$key};
    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /${inNCPDP}_/ );

    $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Month_BAC/$fname";
    $thisfile       = "$outdir\\$fname";
    $EOMfiles{$key} = "$webpath";
    $EOMFNAMES{$key} = $fname;
  }

  $ptr = 0;
  $max = 12;
  $max = 18 if ($Pharmacy_Arete{$ID});
  foreach $key (reverse sort keys %EOMFNAMES) {
    if ( $ptr < $max ) {
       print qq#<a href="$EOMfiles{$key}">$EOMFNAMES{$key}</a><br>\n#;
    }
    $ptr++;
  }
}

#______________________________________________________________________________
