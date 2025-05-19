
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Excel::Writer::XLSX;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

#####################$| = 1; # don't buffer output
$nbsp = "&nbsp;";

&readsetCookies;

if ( $USER ) {
   print &PrintHeader;
} else {
   exit(0);
}

&readPharmacies;

$workbook  = "";

$dbin    = "RIDBNAME";  # Only database needed for this routine
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

$FILENAME   = "ReconRx_Review_My_Aging_${PH_ID}_${TIMESTMP}.xlsx";
##$FQFILENAME = "D:\\Recon-Rx\\Reports\\$FILENAME";
$FQFILENAME = "D:\\WWW\\members.recon-rx.com\\Webshare\\Reports\\$FILENAME";
##$FQFILENAME = qq#D:/WWW/members.recon-rx.com/Webshare/Reports/$FILENAME#;

&displayWebPage;

#______________________________________________________________________________

#&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  my ($status) = &getData;
  
  ##$URL = qq#https://members.Recon-Rx.com/WebShare/reports/$FILENAME?TS=$now#;
  $URL = qq#https://members.Recon-Rx.com/WebShare/reports/$FILENAME#;
  if ($status > 0) {
    print "<p>Your aging snapshot has been created! In this report you will see all individual unpaid claims that make up your ReconRx 'Review My Aging' totals. Click the link below to download:</p>";
	print qq#<br />#;
    print qq#<p><strong>Download Detailed Aging File: #;
    print qq#<a href="$URL">Excel</a> $nbsp#;
##    print qq#<a href="/Reports/$CSVfilename">CSV</a></strong></p>\n#;
	print qq#<br />#;
	print "<p>(This report will only be available for 5 minutes)</p>";
  }
}

#______________________________________________________________________________
 
sub getData {
  $success = 0;
  $display_esi = 0; 

  my $count = 0;

# Connect to the database

  $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
         { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
  DBI->trace(1) if ($dbitrace);

  if ($Pharmacy_DisplayESI{$PH_ID} =~ /^Y$/) {
     $display_esi = 1;
  }
  
  &setExcel($FQFILENAME);

##  open (CSVEXPORT, "> ${FQCSVfilename}");
##  print CSVEXPORT "Third_Party_Payer_Name,dbBinNumber,dbRxNumber,dbFillNumber, dbDateOfService,dbDateTransmitted,dbTotalAmountPaid,dbCode,F1to44,F45to59,F60to89,Fover90\n";

  $row = 0;
  $col = 0;
  $jout = "Payer Name";        &outExcel($headformat , $jout); $col++;
  $jout = "BIN";               &outExcel($headformatR, $jout); $col++;
  $jout = "Rx#";               &outExcel($headformatR, $jout); $col++;
  $jout = "Fill Number";       &outExcel($headformatR, $jout); $col++;
  $jout = "Date of Service";   &outExcel($headformatR, $jout); $col++;
  $jout = "Date Transmitted";  &outExcel($headformatR, $jout); $col++;
  $jout = "Total Amt Paid";    &outExcel($headformatR, $jout); $col++;
  $jout = "1 to 44";           &outExcel($headformatR, $jout); $col++;
  $jout = "45 to 59";          &outExcel($headformatR, $jout); $col++;
  $jout = "60 to 89";          &outExcel($headformatR, $jout); $col++;
  $jout = "Over 90";           &outExcel($headformatR, $jout); $col++;

  $sql = &get_reconrx_aging_sql($PH_ID,$display_esi);

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;
  
  if ( $numofrows <= 0 ) {
     my $jout = "No records found!";
     $row = 0;
     $col = 0;
     &outExcel($format , $jout); $col++;

##     print CSVEXPORT "$jout\n";
  } else {
    $rowcount = 0;
    while ( my ($Third_Party_Payer_Name, $dbBinNumber, $dbRxNumber, $dbFillNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbCode, $F1to44, $F45to59, $F60to89, $Fover90) = $sthrp->fetchrow_array()) {
       $rowcount++;
  
       $DateTrans = substr($dbDateTransmitted, 0, 8);
       $row++;
       $col = 0;
       &outExcel($format , $Third_Party_Payer_Name);       $col++;
       &outExcel($formatR, $dbBinNumber);                  $col++;
       &outExcel($formatR, $dbRxNumber);                   $col++;
       &outExcel($formatR, $dbFillNumber);                 $col++;
       &outExcel($formatR, $dbDateOfService);              $col++;
       &outExcel($formatR, $DateTrans);                    $col++;
       &outExcel($formatD, $dbTotalAmountPaid_Remaining);  $col++;
       &outExcel($formatD, $F1to44);                       $col++;
       &outExcel($formatD, $F45to59);                      $col++;
       &outExcel($formatD, $F60to89);                      $col++;
       &outExcel($formatD, $Fover90);                      $col++;
  
##       print CSVEXPORT qq#"$Third_Party_Payer_Name",$dbBinNumber,$dbRxNumber,$dbFillNumber, $dbDateOfService,$dbDateTransmitted,$dbTotalAmountPaid_Remaining,$F1to44,$F45to59,$F60to89,$Fover90\n#;
  
       $Grand_RTotals     += $dbTotalAmountPaid_Remaining;
       $Grand_RF1to44s    += $F1to44;
       $Grand_RF45to59s   += $F45to59;
       $Grand_RF60to89s   += $F60to89;
       $Grand_RFover90s   += $Fover90;
  	 
       $count++;
    }

    $row++;
    $col = 0;
    &outExcel($format , "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;
    &outExcel($formatR, "--------"); $col++;

##    print CSVEXPORT qq#"--------","--------","--------","--------","--------","--------","--------","--------","--------","--------"\n#;

    $row++;
    $col = 0;
    &outExcel($format , "Totals" );           $col++;
    $col++;
    $col++;
    $col++;
    $col++;
    $col++;
    &outExcel($formatD, $Grand_RTotals);      $col++;
    &outExcel($formatD, $Grand_RF1to44s);     $col++;
    &outExcel($formatD, $Grand_RF45to59s);    $col++;
    &outExcel($formatD, $Grand_RF60to89s);    $col++;
    &outExcel($formatD, $Grand_RFover90s);    $col++;

##    print CSVEXPORT qq#"Totals","","","","",$Grand_RTotals,$Grand_RF1to44s,$Grand_RF45to59s,$Grand_RF60to89s,$Grand_RFover90s\n#;
  }

  $sthrp->finish;
  
##  close (CSVEXPORT);

  $worksheet->set_column( 0,  0, 34 );	# Payer Name
  $worksheet->set_column( 1,  1,  8 );	# BIN
  $worksheet->set_column( 2,  2, 10 );	# Rx Number
  $worksheet->set_column( 3,  3,  8 );	# Fill Number 
  $worksheet->set_column( 4,  4, 10 );	# Date of Service
  $worksheet->set_column( 5,  5, 13 );	# Date Transmitted
  $worksheet->set_column( 6,  6, 12 );	# Total Amount Paid
  $worksheet->set_column( 7,  7, 12 );	# F1to44
  $worksheet->set_column( 8,  8, 12 );	# F45to59
  $worksheet->set_column( 9,  9, 11 );	# F60to89
  $worksheet->set_column( 10, 10,11 );	# Fover90
  $workbook->close();

  if ($count > 0) {
    $success = 1;
  }
 
  $dbx->disconnect;
  
  return $success;
}

#______________________________________________________________________________

sub setExcel {
  my ($SSName) = @_;

  $headformat = "";
  $format     = "";
  $dolformat  = "";

  unlink "$SSName" if ( -e "$SSName" );

  if ( $debug ) {
     if ( !-e "$SSName" ) {
       print "File Gone! $SSName<br>\n";
     } else {
       print "File still there! $SSName<br>\n";
     }
  }

  $workbook  = Excel::Writer::XLSX->new("$SSName");
  $worksheet = $workbook->add_worksheet();

  foreach $worksheet ($workbook->sheets()) {
     $worksheet->set_landscape();
  }
  my $TITLE = qq#$Pharmacy_Name ($USER)\n$FILENAME#;
  $worksheet->set_header("&C\&11\&\"Calibri,Regular\"$TITLE", 0.20);

  $worksheet->set_footer("\&L&D\&RPage &P of &N");
  $worksheet->repeat_rows(0);
  $worksheet->set_margin_left(0.30);
  $worksheet->set_margin_right(0.30);
 
  $workbook->set_properties(
      title    => "$report",
      author   => "ReconRx",
      comments => "$tdate $ttime",
      subject  => "$report"
  );

# binmode(STDOUT);

  $worksheet->add_write_handler(qr[\w], \&store_string_widths);

  $headformat = $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformat->set_text_wrap();

  $headformatL= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformatL->set_text_wrap();
  $headformatR= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'right');
  $headformatR->set_text_wrap();
  $headformatC= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'center');
  $headformatC->set_text_wrap();
  $headformatD= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'right', num_format => '$#,##0.00');
  $headformatD->set_text_wrap();
  $headformatI= $workbook->add_format(bold => 1, bg_color => 'cyan', font =>'Arial', align => 'left');
  $headformatI->set_italic();
  $headformatI->set_text_wrap();

  $format = $workbook->add_format();
  $format->set_align('left');
  $format->set_font('Arial');
  $format->set_text_wrap();

  $formatL = $workbook->add_format();
  $formatL->set_align('left');
  $formatL->set_font('Arial');
  $formatR = $workbook->add_format();
  $formatR->set_align('right');
  $formatR->set_font('Arial');
  $formatR14 = $workbook->add_format();
  $formatR14->set_align('right');
  $formatR14->set_font('Arial');
  $formatR14->set_num_format('00000000000000');

  $formatC = $workbook->add_format();
  $formatC->set_align('center');
  $formatC->set_font('Arial');
  $formatD = $workbook->add_format();
  $formatD->set_align('right');
  $formatD->set_font('Arial');
  $formatD->set_num_format('$#,##0.00');	# Money!
  $formatGreen = $workbook->add_format();
  $formatGreen->set_align('left');
  $formatGreen->set_bg_color('lime');
  $formatBlue = $workbook->add_format();
  $formatBlue->set_align('right');
  $formatBlue->set_bg_color('cyan');
  $formatBlueD = $workbook->add_format();
  $formatBlueD->set_align('right');
  $formatBlueD->set_bg_color('cyan');
  $formatBlueD->set_bold;
  $formatBlueD->set_num_format('$#,##0.00');	# Money!

  $formatGreenD = $workbook->add_format();
  $formatGreenD->set_align('right');
  $formatGreenD->set_bg_color('lime');
  $formatGreenD->set_num_format('$#,##0.00');	# Money!
}

#______________________________________________________________________________

sub outExcel {
   my ($format, $out) = @_;

   ($out) = &StripIt_local($out);
   if ( $out =~ /^\s*0\s*$/ ) {
      $out = "0.00";
   } elsif ( !$out ) {
      $out = " ";
   }

   if ( $format ) {
     $worksheet->write($row, $col, "$out", $format);
   } else {
     $worksheet->write($row, $col, "$out");
   }
}

#______________________________________________________________________________

sub StripIt_local {
   my ($value) = @_;

   $value =~ s/^\s*(.*?)\s*$/$1/;
   $value =~ s/\/\s+\///g;

   return($value);
}

#______________________________________________________________________________
