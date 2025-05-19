require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Excel::Writer::XLSX;
use LWP::Simple;

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp  = "&nbsp;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$Q          = $in{'Q'};
$TYPE       = $in{'TYPE'};
$CHK        = $in{'CHK'};
$CD         = $in{'CD'};
$TS         = $in{'TS'};

($TS)   = &StripJunk($TS);
($CHK)  = &StripJunk($CHK);
($CD)   = &StripJunk($CD);
($Q)    = &StripJunk($Q);
($TYPE) = &StripJunk($TYPE);

#______________________________________________________________________________

&readsetCookies;

if ( $USER ) {
   &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    &ReconRxAggregatedHeaderBlock;
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
my $agg_check;
if ( $PH_ID  eq 'Aggregated') {
  $agg_check = 1;
  $PH_ID = $Agg_String;
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
#______________________________________________________________________________

##$outdir = qq#D:/Recon-Rx/Reports#;
$outdir = qq#D:/WWW/members.recon-rx.com/Webshare/Reports#;

$TYPE = "SS" if ( !$SS );
$leftmargin =  20;
$ytop       = 840;
$pagenum    =   1;
#$colwidth   =  80;
$colwidth   =  70;
%font       =  ();
$genFound   = 0;
$key        = 0;
  
my $FMT = "%0.02f";
my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );

%attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error );
$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST", $dbuser,$dbpwd, \%attr) || &handle_error;
DBI->trace(1) if ($dbitrace);

&readPharmacies;
&readThirdPartyPayers;
&read_Other_Sources_835s;
&read_Other_Sources_835s_Lookup;

my $TABLE    = $DBTABN{"$dbin"};

my $R8dbin   = "R8DBNAME";
my $R8DBNAME = $DBNAMES{"$R8dbin"};
my $R8TABLE  = $DBTABN{"$R8dbin"};

my $P8dbin   = "P8DBNAME";
my $P8DBNAME = $DBNAMES{"$P8dbin"};
my $P8TABLE  = $DBTABN{"$P8dbin"};

my $FIELDS   = $DBFLDS{"$R8dbin"};
my $FIELDS2  = $DBFLDS{"$R8dbin"} . "2";
my $fieldcnt = $#${FIELDS2} + 2;
 
my $retval = "";

&displayWebPage;

#______________________________________________________________________________

&MyReconRxTrailer;


# Close the Database
$dbx->disconnect;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  print qq#<a href="javascript:history.go(-1)">Return</a><br>\n#;

  $USEME = $TS | $CD;
  my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($USEME);

  print "TS: $TS, CD: $CD<br>USEME: $USEME<br>\n" if ($debug);

  $year += 1900;
  $date = qq#$abbr[$mon] $mday, $year#; 
  $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
  $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
  $SFDATE2 = sprintf("%04d%02d%02d",   $year, $mon+1, $mday);
  $HEADDATE= sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
  ($PROG = $prog) =~ s/_/ /g;

  $CheckNumber = $CHK;
  $NameSS  = "${CheckNumber}.xlxs";

  my $CHKAMTout = "\$" . &commify(sprintf("$FMT", $CHKAMT));
  
  if ($R_PostedBy =~ /recon/i) {
    $PostedBy_Display = qq#ReconRx <img src="/images/reconrx16px.png" />#;
  } elsif ($R_PostedBy !~ /^\s*$/) {
    $PostedBy_Display = $Pharmacy_Name;
  } else {
    $PostedBy_Display = "Not Recorded";
  }

  print "<hr>TYPE: $TYPE<br>DateAdded: $DateAdded<hr>\n" if ($debug);

  print qq#<table>\n#;
  print qq#<tr><th class="align_left" colspan=3><h1 class="page_title">Retrieve Remit</h1></th></tr>#;

  print qq#<tr><th class="align=left">Pharmacy:     </th><th colspan=2><font style="BACKGROUND-COLOR: yellow">$Pharmacy_Name</font></th></tr>\n#;

  if ( $Q =~ /CD/i ) {
     $Qtitle = "Check Date";
  } else {
     $Qtitle = "Check Received Date";
  }
  print qq#<tr><th class="align=left">$Qtitle</th><th colspan=2><font style="BACKGROUND-COLOR: yellow">$HEADDATE</font></th></tr>\n#;
  print qq#<tr><th class="align=left">Check Number: </th><th colspan=2><font style="BACKGROUND-COLOR: yellow">$CHK</font></th></tr>\n#;

  if ( $TYPE =~ /^SS$/i ) {
    &genreport($TYPE, $TS, $CHK);
  } elsif ( $TYPE ) {
    print qq#<tr><td>Unknown file type selected!</td></tr>\n#;
  }

  print qq#</table>\n#;
}

#______________________________________________________________________________

sub setExcel {

  my ($SSName) = @_;

  print "sub setExcel. Entry. SSName: $SSName<br>\n" if ($debug);

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
     $worksheet->fit_to_pages( 1, 0 ); # Fit all columns on a single page
     $worksheet->hide_gridlines(0); # 0 = Show gridlines
     $worksheet->freeze_panes( 1, 0 ); # Freeze first row
     $worksheet->repeat_rows( 0 ); # Print on each page
  }
#
# my $TITLE = qq#$Pharmacy_Name ($USER)\nReconRx: Retrieve Remit for $TPP - Check: $CHK, \$$CHKAMT, $HEADDATE#;
  $TITLE = qq#$Pharmacy_Name ($USER)\nReconRx: Retrieve All Remits - $HEADDATE#;
  print "YOYO: Display_on_Remits: $Display_on_Remits<br>R_ISA06: $R_ISA06<BR>R_TPP: $R_TPP<hr>\n" if ($debug);

  $worksheet->set_header("&C\&11\&\"Calibri,Regular\"$TITLE", 0.20);
  $worksheet->print_area('A:H' );

  $worksheet->set_footer("\&L&D\&RPage &P of &N");
  $worksheet->repeat_rows(0);
  $worksheet->set_margin_left(0.20);
  $worksheet->set_margin_right(0.20);
 
  $workbook->set_properties(
      title    => "$report",
      author   => "ReconRx - PAI-IT",
      comments => "Created with Perl and Excel::Writer::XLSX\n$tdate $ttime",
      subject  => "$report"
  );

# binmode(STDOUT);

# $worksheet->add_write_handler(qr[\w], \&store_string_widths);

  $headformat = $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformat->set_align('top');
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

  $format     = $workbook->add_format();
  $format->set_align('left');
  $format->set_font('Arial');
  $format->set_text_wrap();

  $formatL     = $workbook->add_format();
  $formatL->set_align('left');
  $formatL->set_font('Arial');
  $formatR    = $workbook->add_format();
  $formatR->set_align('right');
  $formatR->set_font('Arial');
  $formatC    = $workbook->add_format();
  $formatC->set_align('center');
  $formatC->set_font('Arial');
  $formatD    = $workbook->add_format();
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

  $formatN    = $workbook->add_format();
  $formatN->set_align('left');
  $formatN->set_font('Arial');
  $formatN->set_num_format('@');

  print "sub setExcel. Exit.<br>\n" if ($debug);

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
#  print "EXCEL: row: $row, col: $col, format: $format, out: $out<br>\n" if ($debug);
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

sub genreport {
  my ($TYPE, $TS, $CHK) = @_;

  if ( $TYPE =~ /^SS$/i ) {
     $REPORT = "Excel";
     $fname = "${REPORT}_${PH_ID}_${SFDATE2}_${CHK}.xlsx";
     $fname = "${REPORT}_${USER}_${SFDATE2}_${CHK}.xlsx" if($agg_check);
  }

  $FILENAME = "$outdir\\$fname";
  $report = "RetrieveRemit";
  $$report = $FILENAME;

  $FILENAME =~ s/\\/\//g;
  my $DateAdded = 0;

  &setExcel($FILENAME);

  if ( $TYPE =~ /^SS$/i ) {
     ($genFound) = &genFile($TYPE, $TS, $CHK, $REPORT, $fname);
  }

  if ( $genFound <= 0 ) {
     print qq#<tr><td colspan=3>No records found for this Check Number!</td></tr>\n#;
  }
  print qq#<tr><td colspan=3>\n#;
  my $now = time();
 ## $URL = qq#/reports/$fname?TS=$now#;
  $URL = qq#https://members.Recon-Rx.com/WebShare/reports/$fname?TS=$now#;
  
  $URL =~ s/ /\%20/g;
  print "URL: $URL<br><br>\n" if ($debug);

  print qq#$nbsp <a href="$URL" target=new>$fname</a>#;
  print qq#</td></tr>\n#;
}

#______________________________________________________________________________

sub genFile {
   my ($TYPE, $TS, $CHK, $REPORT, $fname) = @_;

   $genFound                = 0;
   my $TOTAL_Amount_Billed  = 0;
   my $TOTAL_Amount_CoPayed = 0;
   my $TOTAL_Amount_Payed   = 0;
   my $TOTAL_Claim_Adjustment_Transaction = 0;
   my $TOTAL_Adjustment_Amount = 0;
   my $TAXES = 0;
   my $TOTAL_DIR_FEE = 0;
   my %checks = (); 

   if ( $Q =~ /CD/i ) {
      # CD  - Check Date
      $sql = "SELECT a.*, SUM(b.Transaction_Amt), SUM(c.Transaction_Amt)
                FROM ( SELECT b.835remitstbID, b.R_TPP, b.R_TPP_PRI, b.Payer_ID, b.R_REF02_Value, b.R_TS3_NCPDP,
                  b.R_CLP01_Rx_Number, b.R_DTM02_Date, b.R_CLP03_Amount_Billed, b.R_CLP04_Amount_Payed, b.R_CLP05_Amount_CoPayed,
                              b.R_AMT02_Tax_Amount, a.R_ISA06_Interchange_Sender_ID, a.R_TRN02_Check_Number, a.R_BPR02_Check_Amount, a.R_BPR16_Date, a.Check_ID
                         FROM $P8DBNAME.Checks a
                         JOIN $P8DBNAME.$P8TABLE b ON (a.Check_ID = b.Check_ID)
                        WHERE a.Pharmacy_ID IN ($PH_ID)
                          AND a.R_BPR16_Date LIKE '%$SFDATE2%'
                          AND a.R_PENDRECV = 'R'
                          #AND (R_TCode is null or R_TCode != 'PLB_Only')
                    UNION ALL
                       SELECT b.835remitstbID, b.R_TPP, b.R_TPP_PRI, b.Payer_ID, b.R_REF02_Value, b.R_TS3_NCPDP,
                        b.R_CLP01_Rx_Number, b.R_DTM02_Date, b.R_CLP03_Amount_Billed, b.R_CLP04_Amount_Payed, b.R_CLP05_Amount_CoPayed,
                              b.R_AMT02_Tax_Amount, a.R_ISA06_Interchange_Sender_ID, a.R_TRN02_Check_Number, a.R_BPR02_Check_Amount, a.R_BPR16_Date, a.Check_ID
                         FROM $R8DBNAME.Checks a
                         JOIN $R8DBNAME.$R8TABLE b ON (a.Check_ID = b.Check_ID)
                        WHERE a.Pharmacy_ID IN ($PH_ID)
                          AND a.R_BPR16_Date LIKE '%$SFDATE2%'
                          AND a.R_PENDRECV = 'R'
                          #AND (R_TCode is null or R_TCode != 'PLB_Only')
                    ) a
          LEFT JOIN reconrxdb.835_cas b 
                 ON (a.835remitstbID = b.Claim_id AND b.Group_Code = 'CO' AND b.Reason_Code = '130')
          LEFT JOIN reconrxdb.835_cas c
                 ON (a.835remitstbID = c.Claim_id AND b.Reason_Code = '105')
           GROUP BY a.835remitstbID
           ORDER BY R_TPP, R_BPR02_Check_Amount+0, R_CLP01_Rx_Number+0";
   } elsif ( $Q =~ /CRD/i ) {
     # CRD - Check Received Date
     $sql = "SELECT a.*, SUM(b.Transaction_Amt), SUM(c.Transaction_Amt)
                FROM (
                  SELECT b.835remitstbID, b.R_TPP, b.R_TPP_PRI, b.Payer_ID, b.R_REF02_Value, b.R_TS3_NCPDP,
                    b.R_CLP01_Rx_Number, b.R_DTM02_Date, b.R_CLP03_Amount_Billed, b.R_CLP04_Amount_Payed, b.R_CLP05_Amount_CoPayed,
                    b.R_AMT02_Tax_Amount, a.R_ISA06_Interchange_Sender_ID, a.R_TRN02_Check_Number, a.R_BPR02_Check_Amount, a.R_BPR16_Date, a.Check_ID
                  FROM $P8DBNAME.Checks a
                  JOIN $P8DBNAME.$P8TABLE b ON (a.Check_ID = b.Check_ID)
                  WHERE a.Pharmacy_ID IN ($PH_ID)
                  AND a.R_CheckReceived_Date LIKE '%$SFDATE%'
                  AND a.R_PENDRECV = 'R'
                  #AND (R_TCode is null or R_TCode != 'PLB_Only')
                UNION ALL
                  SELECT b.835remitstbID, b.R_TPP, b.R_TPP_PRI, b.Payer_ID, b.R_REF02_Value, b.R_TS3_NCPDP,
                    b.R_CLP01_Rx_Number, b.R_DTM02_Date, b.R_CLP03_Amount_Billed, b.R_CLP04_Amount_Payed, b.R_CLP05_Amount_CoPayed,
                    b.R_AMT02_Tax_Amount, a.R_ISA06_Interchange_Sender_ID, a.R_TRN02_Check_Number, a.R_BPR02_Check_Amount, a.R_BPR16_Date, a.Check_ID
                  FROM $R8DBNAME.Checks a
                  JOIN $R8DBNAME.$R8TABLE b ON (a.Check_ID = b.Check_ID)
                  WHERE a.Pharmacy_ID IN ($PH_ID)
                  AND a.R_CheckReceived_Date LIKE '%$SFDATE%'
                  AND a.R_PENDRECV = 'R'
                  #AND (R_TCode is null or R_TCode != 'PLB_Only')
                ) a
          LEFT JOIN reconrxdb.835_cas b 
                 ON (a.835remitstbID = b.Claim_id AND b.Group_Code = 'CO' AND b.Reason_Code = '130')
          LEFT JOIN reconrxdb.835_cas c
                 ON (a.835remitstbID = c.Claim_id AND b.Reason_Code = '105')
           GROUP BY a.835remitstbID
           ORDER BY R_TPP, R_BPR02_Check_Amount+0, R_CLP01_Rx_Number+0";
   }

   (my $sqlout = $sql) =~ s/\n/<br>\n/g;

#   print "$sqlout";
 
   $stb = $dbx->prepare($sql);
   $genFound = $stb->execute;
   $genFound = 0 if ( $genFound =~ /0E0/ );

   if ( $genFound <= 0 ) {
     my $jout = "No records found for this query";
     print "$jout<br>\n";
     if ( $REPORT =~ /Excel/i ) {
        $row = 0;
        $col = 0;
        &outExcel($format , $jout  ); $col++;
     }
   } else {
     if ( $REPORT =~ /Excel/i ) {
       $row--;	# adds one in subroutine, not needed here, this fixes
       &print_Heading_Line;
     }


     my $ptr = 0;
     while (my @row = $stb->fetchrow_array()) {
       ($claim_id, $R_TPP, $R_TPP_PRI, $Payer_ID, $R_REF02_Value, $NCPDP, $R_CLP01_Rx_Number,
          $R_DTM02_Date, $R_CLP03_Amount_Billed, $R_CLP04_Amount_Payed,
          $R_CLP05_Amount_CoPayed, $R_AMT02_Tax_Amount,
          $R_ISA06_Interchange_Sender_ID, $R_TRN02_Check_Number,
          $R_BPR02_Check_Amount, $R_BPR16_Date, $Check_ID, $Trans_Amt, $Tax_Amt) = @row;

       $checks{$Check_ID}++;

       $Amount_Billed        = $R_CLP03_Amount_Billed;
       $Amount_Payed         = $R_CLP04_Amount_Payed;
       $Amount_CoPayed       = $R_CLP05_Amount_CoPayed;

       my $TAXES = 0;
       $R_AMT02_Tax_Amount = $R_AMT02_Tax_Amount || 0;
       $Tax_Amt = $Tax_Amt || 0;

       $TAXES = $R_AMT02_Tax_Amount + $Tax_Amt;
       $TAXES = "\$" . &commify(sprintf("$FMT", $TAXES));

       $TRANS_FEE = $Trans_Amt || 0;
       $TRANS_FEE = "\$" . &commify(sprintf("$FMT", $TRANS_FEE));

       my $RxNumber = $R_CLP01_Rx_Number + 0;
       my $OR_DTM02_Date = substr($R_DTM02_Date, 4, 2) . "/" . substr($R_DTM02_Date, 6, 2). "/" .  substr($R_DTM02_Date, 0, 4);

       print "DIR_FEE: $DIR_FEE<br>\n" if ( $DIR_FEE > 0 && $debug );
       $TOTAL_DIR_FEE += $DIR_FEE;

       if ( $REPORT =~ /Excel/i ) {
          my $checkdate = substr($R_BPR16_Date, 4, 2) . "/" . substr($R_BPR16_Date, 6, 2) . "/" . substr($R_BPR16_Date, 0, 4);
          $row++;
          $col = 0;
          if ($agg_check) {
            $jout = $NCPDP;       &outExcel($formatC, $jout  ); $col++;
          }
          $jout = $RxNumber;       &outExcel($formatC, $jout  ); $col++;
          $jout = $OR_DTM02_Date;  &outExcel($formatC, $jout  ); $col++;
          $jout = $Amount_Billed;  &outExcel($formatD, $jout  ); $col++;
          $jout = $Amount_CoPayed; &outExcel($formatD, $jout  ); $col++;
          $jout = $Amount_Payed;   &outExcel($formatD, $jout  ); $col++;
          $jout = $TAXES;          &outExcel($formatD, $jout  ); $col++;
          $jout = $TRANS_FEE;      &outExcel($formatD, $jout  ); $col++;
          $jout = $DIR_FEE || "";  &outExcel($formatD, $jout  ); $col++;

          if ( $R_TPP_PRI != $Payer_ID ) {
             $jout = "$R_ISA06_Interchange_Sender_ID: $TPP_Names{$Payer_ID}"; &outExcel($format , $jout  ); $col++;
          } else {
             $jout = $TPP_Names{$Payer_ID};                &outExcel($format , $jout  ); $col++;
          }

          $jout = $R_TRN02_Check_Number;
          $worksheet->write_string($row, $col, "$jout", $formatN); $col++;

          $jout = sprintf("%0.2f", $R_BPR02_Check_Amount); &outExcel($formatD, $jout  ); $col++;	# Check Amount
          $jout = $checkdate;      &outExcel($formatR, $jout  ); $col++;	# Check Number
       }

       $TOTAL_Amount_Billed     += $R_CLP03_Amount_Billed;
       $TOTAL_Amount_CoPayed    += $R_CLP05_Amount_CoPayed;
       $TOTAL_Amount_Payed      += $R_CLP04_Amount_Payed;
       $TOTAL_Adjustment_Amount += $R_PLB04_Adjustment_Amount;

       $ptr++;
     }

     my $check_ids = '';

     foreach $check (keys %checks) { 
       $check_ids .= "$check,";
     }

     chop($check_ids);

#     print "Checks: $check_ids<br>";

     #### Do Totals
     if ( $REPORT =~ /Excel/i ) {
        $row++;
        $row++;

        $col = 3;
        $jout = "Prescription Total:";   &outExcel($headformatR, $jout  ); $col++;
        $jout = $TOTAL_Amount_Payed;   &outExcel($headformatD, $jout  ); $col++;

        my $FEES = 0;

        my $plb_sql = "SELECT a.R_TRN02_Check_Number, a.R_TPP_PRI, b.Adjustment_Reason_Code, Adjustment_Reason_Code_Meaning, Adjustment_Description, Adjustment_Amount
                   FROM reconrxdb.checks a
                   JOIN reconrxdb.check_plbs b ON (a.Check_ID = b.Check_ID)
                  WHERE a.Check_ID IN ($check_ids)
               ORDER BY a.R_TRN02_Check_Number";

        print "\n$sel_sql\n";

        my $plb_sth = $dbx->prepare($plb_sql);
        my $rowsfound = $plb_sth->execute;

        if ($rowsfound ne '0E0') {
           while (@row = $plb_sth->fetchrow_array()) {
              my ($Check_Number, $R_TPP_PRI, $Reason_Code, $Reason_Code_Meaning, $Description, $Amount) = @row;

              $row++;
              $col = 1;
              $jout = "Check#";   &outExcel($headformatR, $jout  ); $col++;
              $jout = "$Check_Number";   &outExcel($headformatR, $jout  ); $col++;
              $jout = "$Reason_Code_Meaning:";   &outExcel($headformatR, $jout  ); $col++;
              $Amount_Neg = sprintf("$FMT", -1 * $Amount);
              $jout = $Amount_Neg;   &outExcel($headformatD, $jout  ); $col++;
              $FEES += $Amount;

              $jout = $Description;
              $col2 = $col++;
              $worksheet->merge_range( $row, $col, $row, $col2, $jout, $headformatR ); $col++;
           }
        }

        $plb_sth->finish();

        $row++;
        $col = 4;
        $jout = "----------";   &outExcel($headformatR, $jout  ); $col++;
        $row++;
        $col = 4;
        my $TAPlessFees = $TOTAL_Amount_Payed - $FEES;
        $jout = $TAPlessFees;   &outExcel($headformatD, $jout  ); $col++;

        print "<hr>\n" if ($debug);
#################################### 

     }
   }

   if ( $REPORT =~ /Excel/i ) {	#
      $worksheet->set_column("A:A", 11 );	# Rx Num
      $worksheet->set_column("B:B", 11 );	# Fill Date
      $worksheet->set_column("C:C", 15 );	# Amount Billed
      $worksheet->set_column("D:D", 22 );	# Amount CoPay
      $worksheet->set_column("E:E", 15 );	# Amount Paid
      $worksheet->set_column("F:F", 15 );	# Tax
      $worksheet->set_column("G:G", 11 );	# Trans Fee
      $worksheet->set_column("H:H", 11 );	# DIR Fee
      $worksheet->set_column("I:I", 28 );	# TPP
      $worksheet->set_column("J:J", 21 );	# Check #
      $worksheet->set_column("K:K", 15 );	# Check Amount
      $worksheet->set_column("L:L", 12 );	# Check Date
      $workbook->close();
   }

   $stb->finish;

   print qq#sub genFile: Exit.<br>\n# if ($debug);
   return($genFound);
}

#______________________________________________________________________________

sub print_Heading_Line {

  my $jout = "";

  if ( $REPORT =~ /Excel/i ) {

     $row++;
     $col = 0;
     if ($agg_check) {
       $jout = "NCPDP"; &outExcel($headformatC, $jout); $col++;
     }
     $jout = "Rx Num";        &outExcel($headformatC, $jout); $col++;
     $jout = "Fill Date";     &outExcel($headformatC, $jout); $col++;
     $jout = "Amount Billed"; &outExcel($headformatR, $jout); $col++;
     $jout = "Amount CoPay";  &outExcel($headformatR, $jout); $col++;
     $jout = "Amount Paid";   &outExcel($headformatR, $jout); $col++;
     $jout = "Tax";           &outExcel($headformatR, $jout); $col++;
     $jout = "Trans Fee";     &outExcel($headformatR, $jout); $col++;
     $jout = "DIR Fee";       &outExcel($headformatR, $jout); $col++;
     $jout = "Third Party Payer"; &outExcel($headformat , $jout); $col++;
     $jout = "Check #";       &outExcel($headformat , $jout); $col++;
     $jout = "Check Amount";  &outExcel($headformatR, $jout); $col++;
     $jout = "Check Date";    &outExcel($headformatR, $jout); $col++;

  }
  
}

#______________________________________________________________________________
#_______________________________________________________________________________

sub docmd_local {

  ($cmd) = @_;
  my $out = "";

  print qq#Do: $cmd\n# if ($debug);
  chomp($out = `$cmd 2>&1`);
  $cmd = "";
  $out =~ s/
//g;

  return($cmd, $out);
}

#_______________________________________________________________________________
