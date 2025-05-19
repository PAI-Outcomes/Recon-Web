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
$prevMonth = $dtspl[1];

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
&readOtherSources;

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
             <th>Payer</th>
			 <th>Amount Paid</th>
             <th>DIR Fee</th>
			 <th>Transaction Fee</th>
             <th>Other Adjustments</th>
             <th>Total Received</th>
			 <th>Claim Count</th>\n#;
  print qq#</tr>\n#;
   
  print qq#</thead>\n#;

  print qq#<tbody>\n#;
  
 
#------------------------------------------------------------
  &get_reconciled_data_for_pharmacy;
  
  my $file_yr;
  my $all_total;
  my $tpp_dir;
  my $tpp_tax;
  my $tpp_other;
  my $tpp_total;
  my $tpp_trans;
  my $tpp_pf;
  my $tpp_count;

  #return if (!$counts{$phs_ids});

  my $totals = 0;
  
  my $size = keys %TPP_Total;
 
  foreach (keys %TPP_Total) { 
    $totals = 0;

    if($_ !~ /700137|700217/) {
      $totals = $TPP_Total{$_} - $TPP_DIR{$_} - $OTHER_FEES{$_} - $TPP_TRANSFEE{$_};
    }
    else {
      $totals = $TPP_Total{$_} - $TPP_DIR{$_} - $OTHER_FEES{$_};
    }

    $totals = sprintf("%.2f",$totals); 

    $tpp_total += $TPP_Total{$_};
    $tpp_dir   += $TPP_DIR{$_};
    $tpp_tax   += $TPP_Taxes{$_};
    $tpp_pf    += $TPP_PF{$_};
    $tpp_trans += $TPP_TRANSFEE{$_}; 
    $tpp_other += $OTHER_FEES{$_};
    $all_total += $totals;
	$tpp_count += $TPP_Count{$_};
	
	
	print qq#<tr>#;
    print qq#<td>$TPP_Names{$_}</td>#;
    printf("<td>%0.2f</td>\n",$TPP_Total{$_});
    printf("<td>%0.2f</td>\n",$TPP_DIR{$_});
    printf("<td>%0.2f</td>\n",$TPP_TRANSFEE{$_});
    printf("<td>%0.2f</td>\n",$OTHER_FEES{$_});
    printf("<td>%0.2f</td>\n",$totals);
	print qq#<td>$TPP_Count{$_}</td>#;
	print qq#</tr>\n#;
	
  }  
  
  $tpp_total = "\$" . &commify(sprintf("$FMT", $tpp_total));
  $tpp_dir = "\$" . &commify(sprintf("$FMT", $tpp_dir));
  $tpp_trans = "\$" . &commify(sprintf("$FMT", $tpp_trans));
  $tpp_other = "\$" . &commify(sprintf("$FMT", $tpp_other));
  $all_total = "\$" . &commify(sprintf("$FMT", $all_total)); 
  $tpp_count = &commify($tpp_count);
#--------------------------------------------------------------------
  print qq#</tbody>\n#;
  print qq#<tfoot>\n
    <th style="text-align: right;">TOTAL</th>
    <th >$tpp_total</th>
    <th>$tpp_dir</th>
    <th>$tpp_trans</th>
	<th>$tpp_other</th>
	<th>$all_total</th>
	<th>$tpp_count</th>
  #;
  print qq#</tfoot>\n#;

  $TotalReceived  = $all_total;
 
  print qq#</table>\n#;

  print qq#<div style="clear: both;"></div>#;
  print qq#<br>\n#;

  print qq#<div style="text-align: right; font-weight: bold; padding-right: 15px">\n#;

  print qq#Received Grand Total: $TotalReceived<br>\n#;

  print qq#</div>\n#;

  print qq#</FORM>\n#;
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

#______________________________________________________________________________

sub get_reconciled_data_for_pharmacy { 
  my $count         =  0;
  my $db_office     = 'officedb';
  my $db_recon      = 'reconrxdb';
  my $sql           = "";
  my $tbl_rmt_arc   = '835remitstb_archive';
  my $tbl_rmt       = '835remitstb';
  my $tbl_chk       = 'Checks';
  my $provider_fee  = '';

  if ($PH_ID == "Aggregated") {
      delete $counts{$phs_ids};
     ($phs_ids) = &get_aggr_pharmacies($USER);
	 #print "phs_ids: $phs_ids\n";
	 if ($phs_ids eq "11,23") {
		$db_recon = "webinar";
	 }
  } else {
	delete $counts{$PH_ID};
	$phs_ids = $PH_ID;
	if ($PH_ID == 11 || $PH_ID == 23) {
      $db_recon = "webinar";
    }
  }
  #print "db_recon: $db_recon\n";
  
  ($check_ids, $check_total) = &get_check_ids($phs_ids);
  
  #print "$check_ids\n";

  $sql = " SELECT rmt.835remitstbID, chk.R_ISA_BIN, chk.R_TPP, rmt.R_CLP01_Rx_Number, rmt.R_CLP04_Amount_Payed,
                  rmt.R_TCode, chk.R_TPP_PRI, rmt.Payer_ID, rmt.R_REF02_Value, rmt.R_DTM02_Date, rmt.R_CLP02_Claim_Status_Code,
                  DATE_FORMAT(rmt.R_DTM02_Date, '%m/%d/%Y') AS 'FilledDate',
                  DATE_FORMAT(chk.R_CheckReceived_Date,  '%m/%d/%Y') AS 'RcvdDate', rmt.R_Sales_Tax, rmt.R_AMT02_Tax_Amount, rmt.R_AMT01_Tax_Amount_Qualifier_Code
             FROM $db_recon.$tbl_chk chk
             JOIN $db_recon.$tbl_rmt rmt ON (chk.Check_ID = rmt.Check_ID)
             WHERE chk.Pharmacy_ID in ($phs_ids) 
              AND chk.Check_ID IN ($check_ids)
              AND (R_TCode is null or R_TCode != 'PLB_Only')
            UNION
           SELECT rmt.835remitstbID, chk.R_ISA_BIN, chk.R_TPP, rmt.R_CLP01_Rx_Number, rmt.R_CLP04_Amount_Payed,
                  rmt.R_TCode, chk.R_TPP_PRI, rmt.Payer_ID, rmt.R_REF02_Value, rmt.R_DTM02_Date, rmt.R_CLP02_Claim_Status_Code,
                  DATE_FORMAT(rmt.R_DTM02_Date, '%m/%d/%Y') AS 'FilledDate',
                  DATE_FORMAT(chk.R_CheckReceived_Date,  '%m/%d/%Y') AS 'RcvdDate', rmt.R_Sales_Tax, rmt.R_AMT02_Tax_Amount, rmt.R_AMT01_Tax_Amount_Qualifier_Code
             FROM $db_recon.$tbl_chk chk
             JOIN $db_recon.$tbl_rmt_arc rmt ON (chk.Check_ID = rmt.Check_ID)
            WHERE chk.Pharmacy_ID in ($phs_ids) 
              AND chk.Check_ID IN ($check_ids)
              AND (R_TCode is null or R_TCode != 'PLB_Only')
              ORDER BY R_TCode DESC, R_CLP02_Claim_Status_Code ASC 
         ";

 #print "\n$sql\n";

  my $sth = $dbx->prepare("$sql");
  my $rowsfound = $sth->execute;

  if ($rowsfound ne '0E0') {
    %Arete           = ();
    %BINs            = ();
    %HMA             = ();
    %Payers          = ();
    %NCPDPs          = ();
	%TPPIDs          = ();
    %Rxs             = ();
    %FilledDates     = ();
    %ProcessedDates  = ();
    %ChkRcvdDates    = ();
    %AmountPaid      = ();
    %Code            = ();
    %DirFee          = ();
    %TPP_Total       = ();
    %OTHER_FEES      = ();
    %TPP_DIR         = ();
    %TPP_TRANSFEE    = ();
    %PLB_TPPs        = ();
    %PSAO_FEES       = ();
    %TPP_Taxes       = ();
    %TPP_PF          = ();
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
      $Tax          = '';
      $provider_fee = '';

      if($NCPDP =~ /^19|^14/) { 
        if($Code && $Code =~ /^DENIED|RRM$/) {
        }
        elsif ($other_paid == $AmountPaid && $other_paid > 0) {
        }
        elsif (!$cob_check{$phs_ids}{$Rx}{$DOS}) {
          $cob_check{$phs_ids}{$Rx}{$DOS}++;
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
        } 
      } 

      $count++;

################################################################
      
      if ( $TPP_ID !~ /$Payer_ID/ ) {
        $TPP_ID = $Payer_ID;
        $BIN = $TPP_BINs{$Payer_ID};
        $Payer = $TPP_Names{$Payer_ID};
      }

      $DIR_FEE = 0;

      if ($TPP_DIR_Locs_Display{$TPP_ID}) {
        $loc = $TPP_DIR_Locs_Display{$TPP_ID};
        $DIR_FEE = &get_DIR_Fee ($phs_ids,$ID, $loc);
      }

      my $key = "$phs_ids$count##$ChkRcvdDate##$BIN##$Rx##$FilledDate";

      $BINs{$key}         = $BIN;
      $Payers{$key}       = $Payer;
      $NCPDPs{$key}       = $NCPDP;
	  $TPPIDs{$key}       = $TPP_ID;
      $Rxs{$key}          = $Rx;
      $FilledDates{$key}  = $FilledDate;
      $ChkRcvdDates{$key} = $ChkRcvdDate;
      $AmountPaid{$key}   = $AmountPaid;
      $Code{$key}         = $Code;
      $DirFee{$key}       = $DIR_FEE;

      if($NCPDP =~ /^19|^14/) { 
        $Taxes{$key}        = $Tax if($Code ne 'DENIED');
        $PF{$key}           = $provider_fee if($Code ne 'DENIED');
        $TPP_Taxes{$TPP_ID} += $Tax if($Code ne 'DENIED');
      }

      $TPP_Count{$TPP_ID} += 1;
      $TPP_Total{$TPP_ID} += $AmountPaid;
      $TPP_PF{$TPP_ID}    += $provider_fee if($Code ne 'DENIED');
      $OTHER_FEES{$TPP_ID} = 0 if (!$OTHER_FEES{$TPP_ID});
      $TPP_DIR{$TPP_ID}    = 0 if (!$TPP_DIR{$TPP_ID});
      $TPP_TRANSFEE{$TPP_ID} = 0 if (!$TPP_TRANSFEE{$TPP_ID});
	  $TPPIDs{$TPP_ID} = $TPP_ID;
  
      my ($tf_loc,$tf_rsn_cd, $tf_rsn_dscr) = split (':',$TPP_Trans_Fee_Locs_PSAO{$TPP_ID});
      my ($loc,$rsn_cd, $rsn_dscr)          = split (':',$TPP_DIR_Locs_PSAO{$TPP_ID});

      ### Add Payers That Could Have DIR FEEs
      if ( $loc =~ /PLB/i ) {
        if ( $row->{'R_TPP_PRI'} !~ /$Payer_ID/ ) {
          $PLB_TPPs{"DIR|$TPP_ID##$Ref02|$rsn_cd##$rsn_dscr"}++;
        }
        else {
          $PLB_TPPs{"DIR|$TPP_ID##0|$rsn_cd##$rsn_dscr"}++;
        }
      }

      ### Add Payers That Could Have Trans FEEs
      if ( $tf_loc{$R_TPP_PRI} =~ /PLB/i ) {
        if ( $row->{'R_TPP_ID'} !~ /$Payer_ID/ ) {
          $PLB_TPPs{"TRN|$TPP_ID##$Ref02|$tf_rsn_cd##$tf_rsn_dscr"}++;
        }
        else {
          $PLB_TPPs{"TRN|$TPP_ID##0|$tf_rsn_cd##$tf_rsn_dscr"}++;
        }
      }
    }

    $counts{$phs_ids} = $count if ( $count > 0 );
    $sth->finish();

    $clm_total = 0;

    foreach $payer (keys %TPP_Total) {
      #print "$payer ($ThirdPartyPayer_Names{$payer}) - $TPP_Total{$payer}\n";
      $clm_total += $TPP_Total{$payer};
    }

    &search_plbs($phs_ids);
    &search_cass($phs_ids);
  }
  else {
  }

  $calc_total = $clm_total - $plb_total;
  $diff = $chk_total - ($clm_total - $plb_total);
  
  $cnt = $count;
}

sub search_plbs {

  my $db_recon = "reconrxdb";
  if ($PH_ID == 11 || $PH_ID == 23) {
	$db_recon = "webinar";
  }
  if ($phs_ids eq "11,23") {
	$db_recon = "webinar"
  }

  my $sel_sql = "SELECT a.R_TPP, a.R_TPP_PRI, b.Adjustment_Reason_Code, Adjustment_Reason_Code_Meaning, Adjustment_Description, Adjustment_Amount
                   FROM $db_recon.checks a
                   JOIN $db_recon.check_plbs b ON (a.Check_ID = b.Check_ID)
                  WHERE Pharmacy_ID in ($phs_ids)
                    AND a.Check_ID IN ($check_ids)";

#  print "\n$sel_sql\n";

  my $sth = $dbx->prepare($sel_sql);
  my $rowsfound = $sth->execute;

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
  my $phs_ids = shift @_;
  
   my $db_recon = "reconrxdb";
  my $db_recon = "reconrxdb";
  if ($PH_ID == 11 || $PH_ID == 23) {
	$db_recon = "webinar";
  }
  if ($phs_ids eq "11,23") {
	$db_recon = "webinar"
  }

  my $sel_sql = "SELECT a.R_TPP, a.R_TPP_PRI, a.R_REF02_Value, SUM(b.Transaction_Amt)
                   FROM (SELECT 835remitstbID, R_TPP, R_TPP_PRI, R_REF02_Value
                           FROM $db_recon.835remitstb
                          WHERE Pharmacy_ID in ($phs_ids)
                            AND Check_ID IN ($check_ids)
                            AND (R_TCode is null or R_TCode != 'PLB_Only')
                          UNION
                         SELECT 835remitstbID, R_TPP, R_TPP_PRI, R_REF02_Value
                           FROM $db_recon.835remitstb_archive
                          WHERE Pharmacy_ID in ($phs_ids)
                            AND Check_ID IN ($check_ids)
                            AND (R_TCode is null or R_TCode != 'PLB_Only')
                        ) a
                   JOIN $db_recon.835_cas b ON (a.835remitstbID = b.Claim_id)
                  WHERE b.Group_Code = 'CO'
                    AND b.Reason_Code = '130'
                    AND b.Transaction_Amt > 0
               GROUP BY a.R_TPP, a.R_TPP_PRI, a.R_REF02_Value";

#  print "\n$sel_sql\n";

  my $sth = $dbx->prepare($sel_sql);
  my $rowsfound = $sth->execute;

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

}

#______________________________________________________________________________

sub get_DIR_Fee {
  my $phs_ids = shift;
  my $RID = shift;
  my $loc = shift;
  ($cas,$gc,$rc) = split(':',$loc);
  
  $fee = 0;
  
  my $db_recon = "reconrxdb";
  my $db_recon = "reconrxdb";
  if ($PH_ID == 11 || $PH_ID == 23) {
	$db_recon = "webinar";
  }
  if ($phs_ids eq "11,23") {
	$db_recon = "webinar"
  }

  $sql = "SELECT Transaction_Amt 
            FROM $db_recon.835_cas
           WHERE Claim_ID = $RID
              && Group_Code = '$gc'
              && Reason_Code = '$rc' 
         ";
  #print "DIR Fee sql: $sql\n";
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
  my $phs_ids = shift @_;
  my $checks = '';
  my @chk = ();
  my $chk_total = 0;
  
  my $db_recon = "reconrxdb";
  my $db_recon = "reconrxdb";
  if ($PH_ID == 11 || $PH_ID == 23) {
	$db_recon = "webinar";
  }
  if ($phs_ids eq "11,23") {
	$db_recon = "webinar"
  }

  $sql = "SELECT Check_id, R_BPR02_Check_Amount
            FROM $db_recon.checks
           WHERE Pharmacy_ID in ($phs_ids)
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

sub get_aggr_pharmacies {
  my $USER = shift @_;
  my $phs = '';
  my @ph = ();

  $sql = "select pharmacy_id 
			from officedb.weblogin_dtl wd 
			where login_id  = $USER";
			
  #print "ph sql: $sql\n";
  
  my $sth = $dbx->prepare($sql);
  my $rowsfound = $sth->execute;

  if ($rowsfound ne '0E0') {
    while (my $phs = $sth->fetchrow_array()) {
      push(@ph, $phs);
    }
  }
  else {
    push(@ph, '0');
  }

  $sth->finish();

  $phs = join(',', @ph);

  return($phs);

}
