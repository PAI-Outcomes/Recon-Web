require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Date::Calc qw(Days_in_Month Today);

$| = 1; 
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);

my $cnt = 0;

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;
$inTPP      = $in{'TPP'};
$inTPPID    = $in{'TPP_ID'};
$inMIN      = $in{'min'};
$inMAX      = $in{'max'};

($inMIN) = &StripJunk($inMIN);
($inMAX) = &StripJunk($inMAX);

&readsetCookies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$mdate  = sprintf("%04d%02d%02d", $year, $month, $day);

my $lastDatePrev = last_day_last_month();

$lastDatePrev =~ s/\//-/g;

my @dtspl = split('-', $lastDatePrev);
#my $prevMonth;
if (length($dtspl[1]) < 2) {
   $prevMonth = '0'.$dtspl[1];
}
$lastDatePrev = "$dtspl[0]-$prevMonth-$dtspl[2]"; 
my $yearBegin = "$year-01-01";


if (!$inMIN) {$inMIN = $yearBegin;}
if (!$inMAX) {$inMAX = $lastDatePrev;}

 my $minrange;
 my $maxrange;

  if ($inMIN ne '') {
    $minrange = $inMIN;
    #$minrange =~ s/-//g;
  }
  if ($inMAX ne '') {
    $maxrange = $inMAX;
    #$maxrange =~ s/-//g;
  }
  else {
    $maxrange = "$inMAX";
  }
    $maxrange = "$maxrange";


if ( $USER ) {
  &MyReconRxHeader;
  &ReconRxAggregatedHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

$dbin    = "RIDBNAME";  # Only database needed for this routine
$DBNAME  = $DBNAMES{"$dbin"};

my $FMT = "%0.02f";

#---------------------------------------
# Connect to the database

  $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
         { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
  DBI->trace(1) if ($dbitrace);
#---------------------------------------
&readThirdPartyPayers;

&display_page;

$dbx->disconnect;

&MyReconRxTrailer;

exit(0);

sub display_page {

  $inmin = $inMIN;
  $inmax = $inMAX;

  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inmin"   VALUE="$inMIN">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inmax"   VALUE="$inMAX">\n#;

  #jQuery now loaded on all pages via header include.
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.min.css" /> \n#;
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.dateTime.min.css" /> \n#;
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.buttons.dataTables.min.css" /> \n#;

##  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery-3.5.1.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTablesV2.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/dataTables.dateTime.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/moment.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/dataTables.buttons.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/buttons.html5.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jszip.min.js"></script> \n#;

  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq# var minDate, maxDate; #;

  print qq#\$(document).ready(function() { \n#;
  print qq#  minDate = new DateTime(\$('\#min'), {
    });
    maxDate = new DateTime(\$('\#max'), {
    });
  #;

   print qq#   var table = \$('\#tablef').DataTable( {
                                  "bScrollCollapse": true,
                                  "sScrollY": "350px", 
                                  "bPaginate": false, 
      dom: 'Bfrtip',
        buttons: [
            'copyHtml5',
            'excelHtml5',
            'csvHtml5'
        ],
    	"footerCallback": function ( row, data, start, end, display ) {
            var api = this.api(), data;
 
            // converting to interger to find total
            var intVal = function ( i ) {
                return typeof i === 'string' ?
                    i.replace(/[\$,]/g, '')*1 :
                    typeof i === 'number' ?
                        i : 0;
            };
 
            var pageTotal = api
                .column( 5, { page: 'current'} )
                .data()
                .reduce( function (a, b) {
                    return intVal(a) + intVal(b);
                }, 0 );
	   			
	   
       }
    } ); \n#;

  print qq# 
    \$('\#min, \#max').on('change', function () {
        table.draw();
    });
  #;
  print qq#} ); \n#;
  print qq# var formatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',

  });
  #;
  print qq#</script> \n#;

  print qq#<br>\n#;

  print qq#  <form action="$prog$ext" method="post">#;
    print qq#<table class='noborders'  cellspacing="5" cellpadding="5">
        <tbody><tr>
            <td>Minimum Date:</td>
            <td><input type="text" id="min" name="min" VALUE="$inMIN"></td>
        </tr>
        <tr>
            <td>Maximum Date:</td>
            <td><input type="text" id="max" name="max" VALUE="$inMAX"></td>
        </tr>
        <tr>
          <td><INPUT class="button-form" TYPE="submit" VALUE=">>>"></td>
        </tr>
      </tbody></table>
    </form>
  #;
  print qq#<br>\n#;
  print qq#<br>\n#;
  
  print qq#<table id="tablef">\n#;

  print qq#<thead>\n#;
   print qq#<tr>
             <th>BIN</th>
			 <th>Payer</th>
			 <th>NCPDP</th>
             <th>Rx Number</th>
			 <th>Filled Date</th>
			 <th>Received Date</th>
             <th>Amount Paid</th>
			 <th>Code</th>
             <th>DIR Fee</th>\n#;
  print qq#</tr>\n#;
   
  print qq#</thead>\n#;

  print qq#<tbody>\n#;
  
  my $count         =  0;
  my $db_office     = 'officedb';
  my $db_recon      = 'reconrxdb';
  my $sql           = "";
  my $tbl_rmt_arc   = '835remitstb_archive';
  my $tbl_rmt       = '835remitstb';
  my $tbl_chk       = 'Checks';
  my $tbl_incoming  = 'incomingtb'; 
  my $tbl_incarch   = 'incomingtb_archive'; 
  my $provider_fee  = '';
  my $totamtpaid = 0;
  my $totdirfee = 0;

  delete $counts{$PH_ID};
  ($check_ids, $check_total) = &get_check_ids($PH_ID);

  #print "sub get_reconciled_data_for_pharmacy: $PH_ID Entry \n";
  
  my $binsql = ""; 
  $binsql = "and rmt.Payer_ID = $inTPPID" if ($inTPPID);

  $sql = " SELECT rmt.835remitstbID, chk.R_ISA_BIN, chk.R_TPP, rmt.R_CLP01_Rx_Number, rmt.R_CLP04_Amount_Payed,
                  rmt.R_TCode, chk.R_TPP_PRI, rmt.Payer_ID, rmt.R_REF02_Value,
                  DATE_FORMAT(rmt.R_DTM02_Date, '%m/%d/%Y') AS 'FilledDate',
                  DATE_FORMAT(chk.R_CheckReceived_Date,  '%m/%d/%Y') AS 'RcvdDate',
                  rmt.R_TS3_NCPDP
             FROM $db_recon.$tbl_chk chk
             JOIN $db_recon.$tbl_rmt rmt ON (chk.Check_ID = rmt.Check_ID)
            WHERE chk.Pharmacy_ID IN ($PH_ID)
              AND chk.Check_ID IN ($check_ids)
              AND (R_TCode is null or R_TCode != 'PLB_Only')
			  $binsql 
            UNION
           SELECT rmt.835remitstbID, chk.R_ISA_BIN, chk.R_TPP, rmt.R_CLP01_Rx_Number, rmt.R_CLP04_Amount_Payed,
                  rmt.R_TCode, chk.R_TPP_PRI, rmt.Payer_ID, rmt.R_REF02_Value,
                  DATE_FORMAT(rmt.R_DTM02_Date, '%m/%d/%Y') AS 'FilledDate',
                  DATE_FORMAT(chk.R_CheckReceived_Date,  '%m/%d/%Y') AS 'RcvdDate',
                  rmt.R_TS3_NCPDP
             FROM $db_recon.$tbl_chk chk
             JOIN $db_recon.$tbl_rmt_arc rmt ON (chk.Check_ID = rmt.Check_ID)
            WHERE chk.Pharmacy_ID IN ($PH_ID)
              AND chk.Check_ID IN ($check_ids)
              AND (R_TCode is null or R_TCode != 'PLB_Only')
			  $binsql 
         ";

 #print "\n$sql\n";

  my $sth = $dbx->prepare("$sql");
  my $rowsfound = $sth->execute;
 # print "RowsFound 1:$rowsfound\n";

  if ($rowsfound ne '0E0') {
    %Arete           = ();
    %BINs            = ();
    %HMA             = ();
    %Payers          = ();
    %NCPDPs          = ();
    %Rxs             = ();
    %FilledDates     = ();
    %ProcessedDates  = ();
    %ChkRcvdDates    = ();
    %AmountPaid      = ();
    %Code            = ();
    %DirFee          = ();
    %cob_check       = ();

    while ($row = $sth->fetchrow_hashref()) {
      $ID           = $row->{'835remitstbID'};
      $BIN          = $row->{'R_ISA_BIN'};
      $Payer        = $row->{'R_TPP'};
      $Rx           = $row->{'R_CLP01_Rx_Number'};
      $FilledDate   = $row->{'FilledDate'};
      $ChkRcvdDate  = $row->{'RcvdDate'};
      $AmountPaid   = $row->{'R_CLP04_Amount_Payed'};
      $Code         = $row->{'R_TCode'};
      $TPP_ID       = $row->{'R_TPP_PRI'};
      $Payer_ID     = $row->{'Payer_ID'};
      $prsh_tax     = $row->{'dbParishCountyTax'};
      $inc_provider = $row->{'dbMedicaidProviderFee'};
      $Ref02        = $row->{'R_REF02_Value'};
      ##$Tax01        = $row->{'R_Sales_Tax'};
      $Tax02        = $row->{'R_AMT02_Tax_Amount'};
      $TaxCode      = $row->{'R_AMT01_Tax_Amount_Qualifier_Code'};
      $other_paid   = $row->{'dbOtherPayerAmountRecognized'};
      $DOS          = $row->{'R_DTM02_Date'};
	  $NCPDP		= $row->{'R_TS3_NCPDP'};

	  
	  if($NCPDP =~ /^19|^14/) { 
        if($Code && $Code =~ /^DENIED|RRM$/) {
        }
        elsif ($other_paid == $AmountPaid && $other_paid > 0) {
        }
        elsif (!$cob_check{$PH_ID}{$Rx}{$DOS}) {
          $cob_check{$PH_ID}{$Rx}{$DOS}++;
          if($prsh_tax || $inc_provider) {
            $prsh_tax = 0 if($prsh_tax == '-20000');
            $Tax = $prsh_tax;
            if($inc_provider == '.10') {
              $provider_fee = $inc_provider;
            }
          }
          elsif($TaxCode eq 'T' && $Tax02 && Tax02 ne '' ) {
            $Tax = $Tax02;
          } 
        ##  elsif($TaxCode ne 'T' && $Tax01 && Tax01 ne '' ) {
        ##    $Tax = $Tax01;
        ##  } 
        } 
      } 


      $count++;

################################################################

      $DIR_FEE = 0;

      if ($TPP_DIR_Locs_Display{$TPP_ID}) {
        $loc = $TPP_DIR_Locs_Display{$TPP_ID};
        $DIR_FEE = &get_DIR_Fee ($PH_ID,$ID,$loc);
      }

	print qq#<tr>#;
	print qq#<td>$BIN</td>#;
    print qq#<td>$Payer</td>#;
	print qq#<td>$NCPDP</td>#;
    print qq#<td>$Rx</td>#;
	print qq#<td>$FilledDate</td>#;
	print qq#<td>$ChkRcvdDate</td>#;
	print qq#<td>\$$AmountPaid</td>#;
    print qq#<td>$Code</td>#;
	print qq#<td>\$$DIR_FEE</td>#;
    print qq#</tr>\n#;
	$totamtpaid += $AmountPaid;
	$totdirfee += $DIR_FEE;

} 

$totamtpaid = "\$" . &commify(sprintf("$FMT", $totamtpaid));
$totdirfee = "\$" . &commify(sprintf("$FMT", $totdirfee)); 
#--------------------------------------------------------------------
  print qq#</tbody>\n#;
  print qq#<tfoot>\n
    <th style="text-align: right;">TOTAL</th>
    <th></th>
    <th></th>
    <th></th>
	<th></th>
	<th></th>
	<th>$totamtpaid</th>
	<th></th>
	<th>$totdirfee</th>
  #;
  print qq#</tfoot>\n#;

  $TotalReceived  = $totamtpaid;
 
  print qq#</table>\n#;

  print qq#<div style="clear: both;"></div>#;
  print qq#<br>\n#;

  print qq#<div style="text-align: right; font-weight: bold; padding-right: 15px">\n#;

  print qq#Received Grand Total: $TotalReceived<br>\n#;

  print qq#</div>\n#;

  print qq#</FORM>\n#;
  }
  else {
    print "No Data Found\n";
  }
}

sub last_day_last_month
{
    my ($year, $month, $day) = Today([time]);

    if (--$month == 0)
    {
        $month = 12;
        --$year;
    }

    return sprintf("%02d/%d/%d", $year,
                                 $month,
								 Days_in_Month($year, $month));
}

sub StripIt_local {
  my ($value) = @_;
  $value =~ s/^\s*(.*?)\s*$/$1/;
  $value =~ s/\/\s+\///g;
  return($value);
}

sub search_plbs {
  #my $PH_ID = shift @_;

  my $sel_sql = "SELECT a.R_TPP, a.R_TPP_PRI, b.Adjustment_Reason_Code, Adjustment_Reason_Code_Meaning, Adjustment_Description, Adjustment_Amount
                   FROM reconrxdb.checks a
                   JOIN reconrxdb.check_plbs b ON (a.Check_ID = b.Check_ID)
                  WHERE Pharmacy_ID in ($PH_ID)
                    AND a.Check_ID IN ($check_ids)";

#  print "\n$sel_sql\n";

  my $sth = $dbx->prepare($sel_sql);
  my $rowsfound = $sth->execute;
#  print "PLBs Found: $rowsfound\n";

  if ($rowsfound ne '0E0') {
    while (@row = $sth->fetchrow_array()) {
      my ($R_TPP, $R_TPP_PRI, $Reason_Code, $Reason_Code_Meaning, $Description, $Amount) = @row;
      my $found = 0;

      foreach $payer (keys %PLB_TPPs) {
        my ($plb_type, $tpp_info, $plb_info) = split(/\|/, $payer);
        my ($tpp, $ref) = split('##', $tpp_info);
        my ($code, $dscr) = split('##', $plb_info);

        if ( $ref ) {                ### PSAO CHECK
          if ( $R_TPP_PRI == 700470 ) {
            $psao = 'Arete';
          }
          elsif ( $R_TPP_PRI == 700447 ) {
            $psao = 'HMA';
          }
          else {
            next;
          }

          if ( $Reason_Code =~ /$code/i && $Description =~ /$dscr/ && $Description =~ /$ref/i ) {
            if ( $plb_type =~ /DIR/i ) {
              $TPP_DIR{$tpp} += $Amount;
            }
            else {
              $TPP_TRANSFEE{$tpp} += $Amount;
            }

            $found++;
            last;
          }
          elsif ($R_TPP_PRI == 700447 && $Description =~ /^Total/ && $Description =~ /$ref/i ) {
            $TPP_DIR{'700150'} += $Amount;
            $found++;
            last;
          }
          elsif ( $Description =~ /$psao/i ) {
            $PSAO_FEES{$R_TPP_PRI} += $Amount;
            $found++;
            last;
          }
          elsif ( $R_TPP_PRI == 700470 && $Reason_Code =~ /WO/i ) {
            $PSAO_FEES{$R_TPP_PRI} += $Amount;
            $found++;
            last;
          }

          elsif ( $R_TPP_PRI == 700447 && $Description =~ /ACTVMBR/ ) {
            $PSAO_FEES{$R_TPP_PRI} += $Amount;
            $found++;
            last;
          }
          else {
            next;
          }
        }
        else {                       ### Non-PSAO CHECK
          if ( $R_TPP_PRI == $tpp && $Reason_Code =~ /$code/i && $Description =~ /$dscr/ ) {
            if ( $plb_type =~ /DIR/i ) {
              $TPP_DIR{$tpp} += $Amount;
              $found++;
              last;
            }
            else {
              $TPP_TRANSFEE{$tpp} += $Amount;
              $found++;
              last;
            }
          }
        }
      }

      if (! $found ) {
        if ( $R_TPP_PRI =~ /700470|700447/ ) {
          $Description = substr($Description, index($Description, "["));
          $Description =~ s/^\s+|\s+$//g;
          $Description =~ s/^[^\[]*\[//;
          $Description =~ s/\]//;

          if ($OtherSourceTPP{$R_TPP_PRI}{uc($Description)}) {
            $tpp = $OtherSourceTPP{$R_TPP_PRI}{uc($Description)};
            $OTHER_FEES{$tpp} += $Amount;
          }
          else {
            #print "Unable to locate Ref02 ($Description) for $R_TPP_PRI\n";
          }
        }
        else {
          $OTHER_FEES{$R_TPP_PRI} += $Amount;
        }
      }
    }
  }

  $sth->finish();

#  print "\nDIR FEES\n";
  foreach $payer (keys %TPP_DIR) {
#    print "$payer ($ThirdPartyPayer_Names{$payer}) - $TPP_DIR{$payer}\n";
    $plb_total += $TPP_DIR{$payer};
  }

#  print "\nTRANS FEES\n";
  foreach $payer (keys %TPP_TRANSFEE) {
#    print "$payer ($ThirdPartyPayer_Names{$payer}) - $TPP_TRANSFEE{$payer}\n";
    $plb_total += $TPP_TRANSFEE{$payer};
  }

#  print "\nOTHER FEES\n";
  foreach $payer (keys %OTHER_FEES) {
#    print "$payer ($ThirdPartyPayer_Names{$payer}) - $OTHER_FEES{$payer}\n";
    $plb_total += $OTHER_FEES{$payer};
  }

#  print "\nPSAO FEES\n";
  foreach $payer (keys %PSAO_FEES) {
#    print "$payer ($ThirdPartyPayer_Names{$payer}) - $PSAO_FEES{$payer}\n";
    $plb_total += $PSAO_FEES{$payer};
  }
}

sub search_cass {
  my $PH_ID = shift @_;

  my $sel_sql = "SELECT a.R_TPP, a.R_TPP_PRI, a.R_REF02_Value, SUM(b.Transaction_Amt)
                   FROM (SELECT 835remitstbID, R_TPP, R_TPP_PRI, R_REF02_Value
                           FROM reconrxdb.835remitstb
                          WHERE Pharmacy_ID in ($PH_ID)
                            AND Check_ID IN ($check_ids)
                            AND (R_TCode is null or R_TCode != 'PLB_Only')
                          UNION
                         SELECT 835remitstbID, R_TPP, R_TPP_PRI, R_REF02_Value
                           FROM reconrxdb.835remitstb_archive
                          WHERE Pharmacy_ID in ($PH_ID)
                            AND Check_ID IN ($check_ids)
                            AND (R_TCode is null or R_TCode != 'PLB_Only')
                        ) a
                   JOIN reconrxdb.835_cas b ON (a.835remitstbID = b.Claim_id)
                  WHERE b.Group_Code = 'CO'
                    AND b.Reason_Code = '130'
                    AND b.Transaction_Amt > 0
               GROUP BY a.R_TPP, a.R_TPP_PRI, a.R_REF02_Value";

#  print "\n$sel_sql\n";

  my $sth = $dbx->prepare($sel_sql);
  my $rowsfound = $sth->execute;
#  print "PLBs Found: $rowsfound\n";

  if ($rowsfound ne '0E0') {
    while (@row = $sth->fetchrow_array()) {
      my ($R_TPP, $R_TPP_PRI, $R_REF02, $Amount) = @row;
      my $found = 0;

      if ( $R_TPP_PRI =~ /700470|700447/ ) {
        if ($OtherSourceTPP{$R_TPP_PRI}{uc($R_REF02)}) {
          $tpp = $OtherSourceTPP{$R_TPP_PRI}{uc($R_REF02)};

          ### Check for PLBs
          if ( $TPP_TRANSFEE{$tpp} ) {
#            print "Skip adding: $Amount\n";
          }
          else {
          $TPP_TRANSFEE{$tpp} += $Amount;
          }
        }
        else {
#          print "Unable to locate Ref02 ($R_REF02) for $R_TPP_PRI\n";
        }
      }
      else {
          if ( $TPP_TRANSFEE{$R_TPP_PRI} ) {
#            print "Skip adding: $Amount\n";
          }
          else {
            $TPP_TRANSFEE{$R_TPP_PRI} += $Amount;
#            print "Direct TRANS Fee Found\n";
          }
      }
    }
  }

  $sth->finish();

#  print "\nTRANS FEES\n";
#  foreach $payer (keys %TPP_TRANSFEE) {
#    print "$payer ($ThirdPartyPayer_Names{$payer}) - $TPP_TRANSFEE{$payer}\n";
#  }
}

#______________________________________________________________________________

sub get_DIR_Fee {
  my $PH_ID = shift;
  my $RID = shift;
  my $loc = shift;
  ($cas,$gc,$rc) = split(':',$loc);
  
  $fee = 0;

  $sql = "SELECT Transaction_Amt 
            FROM reconrxdb.835_cas
           WHERE Claim_ID = $RID
              && Group_Code = '$gc'
              && Reason_Code = '$rc' 
         ";

  my $sth = $dbx->prepare($sql);
  my $rowsfound = $sth->execute;
  #print "RowsFound:$rowsfound\n";

  if ($rowsfound ne '0E0') {
    ($fee) = $sth->fetchrow_array();
  }

  return $fee;
  $sth->finish();
}

sub get_check_ids {
  my $PH_ID = shift @_;
  my $checks = '';
  my @chk = ();
  my $chk_total = 0;
#  $mdate = '2021-10-01';
#  $rdate = '2021-10-31';

  $sql = "SELECT Check_id, R_BPR02_Check_Amount
            FROM reconrxdb.checks
           WHERE Pharmacy_ID in ($PH_ID)
             AND R_CheckReceived_Date  >= '$minrange'
             AND R_CheckReceived_Date  <= '$maxrange'";
  #print "check ID sql: $sql\n";
  my $sth = $dbx->prepare($sql);
  my $rowsfound = $sth->execute;
  #print "RowsFound:$rowsfound\n";

  if ($rowsfound ne '0E0') {
    while (my ($check_id, $check_amt) = $sth->fetchrow_array()) {
      push(@chk, $check_id);
      $chk_total += $check_amt;
    }
  }
  else {
    push(@chk, '0');
  }

  $sth->finish();

  $checks = join(',', @chk);

  return($checks, $chk_total);
}



