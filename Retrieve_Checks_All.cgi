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
  print qq#<tr><th class="align_left" colspan=3><h1 class="page_title">Retrieve Check</h1></th></tr>#;

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
  $TITLE = qq#$Pharmacy_Name ($USER)\nReconRx: Retrieve All Checks - $HEADDATE#;

  $worksheet->set_header("&C\&11\&\"Calibri,Regular\"$TITLE", 0.20);
  $worksheet->print_area('A:H' );

  $worksheet->set_footer("\&L&D\&RPage &P of &N");
  $worksheet->repeat_rows(0);
  $worksheet->set_margin_left(0.20);
  $worksheet->set_margin_right(0.20);
 
  $workbook->set_properties(
      title    => "$report",
      author   => "ReconRx - Jay Herder",
      comments => "Created with Perl and Excel::Writer::XLSX\n$tdate $ttime",
      subject  => "$report"
  );

# binmode(STDOUT);

# $worksheet->add_write_handler(qr[\w], \&store_string_widths);

  $headformat = $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformat->set_align('top');
  $headformat->set_text_wrap();

  $headformatR= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'right');
  $headformatR->set_text_wrap();

  $headformatC= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'center');
  $headformatC->set_text_wrap();

  $format     = $workbook->add_format();
  $format->set_align('left');
  $format->set_font('Arial');
  $format->set_text_wrap();

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
  }

  $FILENAME = "$outdir\\$fname";
  $report = "RetrieveCheck";
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
  $URL = qq#/reports/$fname?TS=$now#;
  $URL = qq#https://members.Recon-Rx.com/WebShare/reports/$fname?TS=$now#;

  $URL =~ s/ /\%20/g;
  print "URL: $URL<br><br>\n" if ($debug);

  print qq#$nbsp <a href="$URL" target=new>$fname</a>#;
  print qq#</td></tr>\n#;
}

#______________________________________________________________________________

sub genFile {

   my $check_tbl = 'checks';
   my $sql  = "SELECT Check_ID, R_TPP, R_TS3_NCPDP, R_BPR04_Payment_Method_Code, R_BPR02_Check_Amount, 
                   R_BPR16_Date, R_TRN02_Check_Number, R_PENDRECV, R_PostedBy,
                   R_TPP_PRI, Payer_ID, Third_Party_Payer_Name, 
                   CASE WHEN R_TPP_PRI != Payer_ID THEN R_REF02_Value ELSE '' END AS ref02,
                   ROUND(SUM(R_CLP04_Amount_Payed),2) as sum, count(*) as cnt
              FROM ( SELECT a.Check_ID, a.R_TPP, a.R_TS3_NCPDP, a.R_BPR04_Payment_Method_Code, a.R_BPR02_Check_Amount, 
                            a.R_BPR16_Date, a.R_TRN02_Check_Number, a.R_PENDRECV, a.R_ISA06_Interchange_Sender_ID, a.R_PostedBy, 
                            a.R_TPP_PRI, b.R_REF02_Value, b.Payer_ID, b.R_CLP04_Amount_Payed
                       FROM $P8DBNAME.$check_tbl a
                       JOIN $P8DBNAME.$P8TABLE b ON ( a.Check_ID = b.Check_ID )
                      WHERE a.Pharmacy_ID IN ($PH_ID)
                        AND a.R_PENDRECV = 'R'
                        AND ";

   if ( $Q =~ /CRD/i ) {
      $sql .= " a.R_CheckReceived_Date='$SFDATE2' ";
   } else {
      $sql .= " a.R_BPR16_Date='$SFDATE2' ";
   }
   $sql .= "      UNION ALL
                     SELECT a.Check_ID, a.R_TPP, a.R_TS3_NCPDP, a.R_BPR04_Payment_Method_Code, a.R_BPR02_Check_Amount, 
                            a.R_BPR16_Date, a.R_TRN02_Check_Number, a.R_PENDRECV, a.R_ISA06_Interchange_Sender_ID, a.R_PostedBy, 
                            a.R_TPP_PRI, b.R_REF02_Value, b.Payer_ID, b.R_CLP04_Amount_Payed
                       FROM $R8DBNAME.$check_tbl a
                       JOIN $R8DBNAME.$R8TABLE b ON ( a.Check_ID = b.Check_ID )
                      WHERE a.Pharmacy_ID IN ($PH_ID)
                        AND a.R_PENDRECV='R'
                        AND ";

   if ( $Q =~ /CRD/i ) {
      $sql .= " a.R_CheckReceived_Date='$SFDATE2' ";
   } else {
      $sql .= " a.R_BPR16_Date='$SFDATE2' ";
   }

   $sql .= " ) a 
             JOIN officedb.third_party_payers b ON ( a.Payer_ID = b.Third_Party_Payer_ID )
         GROUP BY a.Check_ID, a.Payer_ID
         ORDER BY b.Third_Party_Payer_Name, a.R_BPR04_Payment_Method_Code, a.R_TRN02_Check_Number, a.R_BPR02_Check_Amount, a.R_BPR16_Date";

   

   (my $sqlout = $sql) =~ s/\n/<br>\n/g;

 
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

     while (my @row = $stb->fetchrow_array()) {
       ($Check_ID, $R_TPP, $R_TS3_NCPDP, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount,
        $R_BPR16_Date, $R_TRN02_Check_Number, $R_PENDRECV, $R_PostedBy,
        $R_TPP_PRI, $Payer_ID, $payer_name, $R_REF02_Value, $claim_total, $claim_count) = @row;

       $checks{$Check_ID}++;


       if ( $REPORT =~ /Excel/i ) {
          my $checkdate = substr($R_BPR16_Date, 4, 2) . "/" . substr($R_BPR16_Date, 6, 2) . "/" . substr($R_BPR16_Date, 0, 4);
          $row++;
          $col = 0;
          $jout = $payer_name; &outExcel($format, $jout); $col++;

          if ($agg_check) {
            $jout = $R_TS3_NCPDP;       &outExcel($formatC, $jout  ); $col++;
          }
          $jout = $R_BPR04_Payment_Method_Code; &outExcel($format, $jout); $col++;

          $jout = $R_TRN02_Check_Number;
          $worksheet->write_string($row, $col, "$jout", $formatN); $col++;

          $jout = sprintf("%0.2f", $R_BPR02_Check_Amount); &outExcel($formatD, $jout  ); $col++;
          $jout = $checkdate;      &outExcel($formatR, $jout  ); $col++;
          $jout = $claim_count;       &outExcel($formatC, $jout  ); $col++;
       }
      }
     }

   if ( $REPORT =~ /Excel/i ) {
      $worksheet->set_column("A:A", 28 );	# Payer
      $worksheet->set_column("B:B", 8 );	# NCPDP
      $worksheet->set_column("C:C", 15 );	# Payment Type
      $worksheet->set_column("D:D", 22 );	# Check #
      $worksheet->set_column("E:E", 15 );	# Check Amt
      $worksheet->set_column("F:F", 12 );	# Check Date
      $worksheet->set_column("G:G", 11 );	# Count
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
     $jout = "Payer"; &outExcel($headformat , $jout); $col++;
     if ($agg_check) {
       $jout = "NCPDP"; &outExcel($headformatC, $jout); $col++;
     }
     $jout = "Pmt Type"; &outExcel($headformat, $jout); $col++;
     $jout = "Check #";       &outExcel($headformat , $jout); $col++;
     $jout = "Check Amount";  &outExcel($headformatR, $jout); $col++;
     $jout = "Check Date";    &outExcel($headformatR, $jout); $col++;
     $jout = "Count";    &outExcel($headformat, $jout); $col++;

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
  $out =~ s///g;

  return($cmd, $out);
}

#_______________________________________________________________________________
