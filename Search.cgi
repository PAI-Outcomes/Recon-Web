
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;
my $ag=0;

$searchnumber = $in{'searchnumber'};
$searchtype   = $in{'searchtype'};

&readsetCookies;
&readPharmacies;

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    &ReconRxAggregatedHeaderBlock_New;
    $PH_ID = $Agg_String;
    $ag = 1;
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

my $FMT = "%0.02f";

my $dbin    = "RIDBNAME";
my $DBNAME  = $DBNAMES{"$dbin"};
my $TABLE   = $DBTABN{"$dbin"};
my $HASH    = $HASHNAMES{$dbin};

if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
}

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST", $dbuser,$dbpwd, \%attr) || &handle_error;

#&readThirdPartyPayers;
#&read_Other_Sources_835s;
#&read_Other_Sources_835s_Lookup;

$ntitle = "Detailed Search";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

&displayWebPage;
$dbx->disconnect;

&MyReconRxTrailer;

exit(0);

sub displayWebPage {

  $searchnumber_orig = $searchnumber;
  $searchtype      = "claim" if ($searchtype =~ /^\s*$/ );
  $checkedclaim    = "";
  $checkedcheck    = "";
  $checkedcheckamt = "";

  if ( $searchtype =~ /claim/i ) {
    $checkedclaim = "checked";
  } elsif ( $searchtype =~ /checkamt/i ) {
    $checkedcheckamt = "checked";	# listed before check for "check" as "check" is embedded in "checkamt"
  } elsif ( $searchtype =~ /check/i ) {
    $checkedcheck = "checked";
  }

  if ( $searchnumber =~ /[A-Za-z]|_|-|\s+/ ) {
    $searchnumber = "'$searchnumber'";
  }

  print qq#
  <form action="$prog$ext" method="post">
  <p>Enter search criteria here:
  <input type="text" name="searchnumber" placeholder="search number" value="$searchnumber_orig" class="input-text-form">
  <input type="radio" name="searchtype" value="claim"    $checkedclaim>Rx</input> $nbsp
  <input type="radio" name="searchtype" value="check"    $checkedcheck>Check\#</input> $nbsp
  <input type="radio" name="searchtype" value="checkamt" $checkedcheckamt>Check Amount</input>
  <INPUT class="button-form" TYPE="submit" VALUE=">>>">
  </form>

  <hr />
  #;

  $searchnumber_SAVE = $searchnumber;

  if ( $searchtype =~ /checkamt/i ) {
    $searchnumber =~ s/\t|\s+|\$|,//g;
  }

  if ($searchtype eq "claim") {
    if ( $searchnumber !~ /^\s*$/ ) {
      print "<h3>Searching <span class=\"searchtext\">for Rx Number: </span>$searchnumber</h3>\n";
    }
  } elsif ($searchtype eq "check") {
    print "<h3>Searching <span class=\"searchtext\">for Check Number: </span>$searchnumber</h3>\n";
  } elsif ($searchtype eq "checkamt") {
    print "<h3>Searching <span class=\"searchtext\">for Check Amount: </span>$searchnumber_SAVE</h3>\n";
 }

  if ( $searchnumber =~ /^\s*$/ ) {
    # do nothing
  } elsif ($searchtype eq "claim") {
    print "<div>";
    &claim_search($searchnumber);
    print "</div>";
  } elsif ($searchtype eq "check") {
    &remits_check($searchnumber);
    print "<div class=\"archive\">";
    &remitsarchive_check($searchnumber);
    print "</div>";
  } elsif ($searchtype eq "checkamt") {
    &remits_checkamt($searchnumber);
    print "<div class=\"archive\">";
    &remitsarchive_checkamt($searchnumber);
    print "</div>";
 }
}

sub claim_search {
  my ($searchnumber) = @_;

  my $tbl_incoming  = 'incomingtb';
  my $tbl_i_archive = 'incomingtb_archive';
  my $tbl_check     = 'checks';
  my $tbl_remit     = '835remitstb';
  my $tbl_r_archive = '835remitstb_archive';
  my $sth;
  my @row;
  my $cnt     = 0;
  
  if ( $ENV =~ /dev/i ) {
    $FRONT = "HTTP://dev.Recon-Rx.com";
    $SECTYP = "http://";
  } else {
    $FRONT = "HTTPS://WWW.Recon-Rx.com";
    $SECTYP = "https://";
  }

  print qq#<link type="text/css" media="screen" rel="stylesheet" href="$FRONT/includes/datatables/css/jquery.dataTables.css" /> \n#;
  #Load DataTables externally
  print qq#<script type="text/javascript" charset="utf-8" src="${SECTYP}cdn.datatables.net/1.10.2/js/jquery.dataTables.js"></script> \n#;
  
  $URLH = "${prog}.cgi";

  print qq#
  <script> 
    \$(document).ready(function() {
       oTable = \$('\#tablef').dataTable( { 
         autoWidth: false, 
         "sScrollX": "100%", 
         "bScrollCollapse": true, 
         "bPaginate": false, 
         "aaSorting": [],
         "bLengthChange": false,
         "pageLength": 100,
         "aoColumnDefs": [
            { 'bSortable': false, 'aTargets': [ 0 ] }

      }); 
  
      \$("\#submit_form").click(function(e) {
        fnResetAllFilters(oTable);
        \$('\#prform').submit();
      });
      }
      oSettings.oPreviousSearch.sSearch = '';
      oTable.fnDraw();
      oTable.fadeTo("fast", 0.33);
    }
  </script> 
  \n#;

  $sql = "SELECT dbNCPDPNumber, dbRxNumber as RX_Number, dbDateOfService, dbTotalAmountPaid as AMT_DUE,'' as AMT_PAID, 
                 '' as CHECK_NO, '' as CHECK_AMT, '' as CHECK_DATE, '' as CHECK_RECEIVED_DATE, '' as ISA06_ID, '' AS R_TPP_PRI, '' AS R_REF02_Value,
                 '' AS Check_ID, '' AS PostedBy
            FROM $DBNAME.$tbl_incoming	
           WHERE Pharmacy_ID IN ($PH_ID)
             AND dbRxNumber = $searchnumber 
             AND dbTotalAmountPaid > 0
             AND dbTCode = ''
           UNION
          SELECT a.dbNCPDPNumber, a.dbRxNumber, a.dbDateOfService, a.dbTotalAmountPaid, c.R_CLP04_Amount_Payed, b.R_TRN02_Check_Number,
                 b.R_BPR02_Check_Amount, b.R_BPR16_Date, b.R_CheckReceived_Date, b.R_ISA06_Interchange_Sender_ID, c.R_TPP_PRI, c.R_REF02_Value,
                 b.Check_ID, b.R_PostedBy
            FROM $DBNAME.$tbl_incoming a
            JOIN $DBNAME.$tbl_r_archive c
              ON (R_TS3_NCPDP         = a.dbNCPDPNumber
               AND c.R_CLP01_Rx_Number = a.dbRxNumber
               AND R_DTM02_Date        = a.dbDateOfService
               AND c.R_CLP04_Amount_Payed = (a.dbTotalAmountPaid - a.dbTotalAmountPaid_Remaining)
               AND c.Payer_ID = a.dbBinParentdbkey
               AND a.dbReconciledDate = c.R_Reconciled_Date
               AND c.R_TCode = 'PP')
            JOIN $DBNAME.$tbl_check b ON (b.Check_ID = c.Check_ID)
           WHERE b.Pharmacy_ID IN ($PH_ID)
             AND a.dbRxNumber = $searchnumber 
             AND a.dbTotalAmountPaid > 0
             AND a.dbTCode = 'PP'
           UNION
          SELECT a.dbNCPDPNumber, a.dbRxNumber, dbDateOfService, dbTotalAmountPaid, c.R_CLP04_Amount_Payed, d.R_TRN02_Check_Number, 
                 d.R_BPR02_Check_Amount, d.R_BPR16_Date, d.R_CheckReceived_Date, d.R_ISA06_Interchange_Sender_ID, c.R_TPP_PRI, c.R_REF02_Value,
                 d.Check_ID, d.R_PostedBy
            FROM $DBNAME.$tbl_i_archive  a
            JOIN officedb.tpp_fee_overpayment b
              ON a.dbBinParentdbkey = b.TPP_ID
            JOIN $DBNAME.$tbl_r_archive c
              ON (R_TS3_NCPDP = a.dbNCPDPNumber
               AND c.R_CLP01_Rx_Number = a.dbRxNumber
               AND R_DTM02_Date = a.dbDateOfService
               AND (c.R_CLP04_Amount_Payed <= ROUND((a.dbTotalAmountPaid  + IFNULL(b.max, 1)),2)  && c.R_CLP04_Amount_Payed >= ROUND((a.dbTotalAmountPaid + IFNULL(b.min, -1)),2)) 
               AND CASE WHEN dbTCode = 'PP' 
                     THEN c.Payer_ID = a.dbBinParentdbkey
                     ELSE 1=1
                     END
               AND a.dbReconciledDate = c.R_Reconciled_Date
               AND c.R_TCode in ('PP','PD','GR'))
            JOIN $DBNAME.$tbl_check d ON (c.Check_ID = d.Check_ID)
           WHERE d.Pharmacy_ID IN ($PH_ID)
             AND a.dbRxNumber = $searchnumber 
             AND a.dbTotalAmountPaid > 0
          UNION
          SELECT a.dbNCPDPNumber, a.dbRxNumber, dbDateOfService, dbTotalAmountPaid, c.R_CLP04_Amount_Payed, b.R_TRN02_Check_Number, 
                 b.R_BPR02_Check_Amount, b.R_BPR16_Date, b.R_CheckReceived_Date, b.R_ISA06_Interchange_Sender_ID, c.R_TPP_PRI, c.R_REF02_Value,
                 b.Check_ID, b.R_PostedBy
            FROM $DBNAME.$tbl_i_archive  a
            LEFT JOIN $DBNAME.$tbl_r_archive c
              ON (R_TS3_NCPDP = a.dbNCPDPNumber
               AND c.R_CLP01_Rx_Number = a.dbRxNumber
               AND R_DTM02_Date = a.dbDateOfService
               AND R_TCode IN ('PP','PD'))
            LEFT JOIN $DBNAME.$tbl_check b ON (b.Check_ID = c.Check_ID)
           WHERE a.Pharmacy_ID IN ($PH_ID)
             AND a.dbRxNumber = $searchnumber 
             AND a.dbTotalAmountPaid > 0
             AND dbTCode IN ('PP','PD','PDEV')
           UNION
          SELECT a.R_TS3_NCPDP, a.R_CLP01_Rx_Number, a.R_DTM02_Date, a.R_CLP04_Amount_Payed, a.R_CLP04_Amount_Payed, b.R_TRN02_Check_Number, 
                 b.R_BPR02_Check_Amount, b.R_BPR16_Date, b.R_CheckReceived_Date, b.R_ISA06_Interchange_Sender_ID, a.R_TPP_PRI, a.R_REF02_Value,
                 b.Check_ID, b.R_PostedBy
            FROM $DBNAME.$tbl_remit a
            JOIN $DBNAME.$tbl_check b ON (a.Check_ID = b.Check_ID)
           WHERE b.Pharmacy_ID IN ($PH_ID)
             AND a.R_CLP01_Rx_Number = $searchnumber
             AND a.R_CLP04_Amount_Payed > 0
        ";

##  print "$sql<br>" if ($USER == 66);
  $sth = $dbx->prepare($sql);
  $sth->execute();

#  print qq#<FORM name="prform" id="prform" ACTION="$URLH" METHOD="POST">\n#;

  print qq#<tbody>\n#;
  
  print qq#<table id="tablef" class="main">\n#;

  print qq#<thead>\n#;
#  print qq#<tr> <th>Rx\#</th> <th>DOS</th> <th>Amt Due</th> <th>Amt Paid</th> <th>Check \#</th> <th>Check Amt</th><th>Check Date</th><th>Check Rcvd Date</th> </tr>\n#;
  if ($ag) {
    print qq#<tr><th>NCPDP\#</th> <th>Rx\#</th> <th>DOS</th> <th>Amt Due</th> <th>Amt Paid</th> <th>Check \#</th> <th>Check Amt</th><th>Check Date</th><th>Check Rcvd Date</th> <th>Print Remit</th> </tr>\n#;
  }
  else {
    print qq#<tr> <th>Rx\#</th> <th>DOS</th> <th>Amt Due</th> <th>Amt Paid</th> <th>Check \#</th> <th>Check Amt</th><th>Check Date</th><th>Check Rcvd Date</th> <th>Print Remit</th> </tr>\n#;
  }
  print qq#</thead>\n#;
  while ( my @row = $sth->fetchrow() ) {
    $cnt++;
    $ncpdp        = $row[0];
    $rrx          = $row[1];
    $rdos         = $row[2];
    $amtdue       = $row[3];
    $amtpaid      = $row[4];
    $rchecknum    = $row[5];
    $rcheckamt    = $row[6];
    $rcheckdate   = $row[7];
    $rrecdate     = $row[8];
    $risa06       = $row[9];
    $rtpp_pri     = $row[10];
    $rref02       = $row[11];
    $check_id     = $row[12];
    $postedby     = $row[13];
    $rrecdate =~ s/\-//g;

    ###This section will take out duplicates when getting COB***DO NOT ORDER BY*****
    next if(${$rrx}{$rdos}{$amtpaid});
    ${$rrx}{$rdos}{$amtpaid}++;
    #######

    $amtdue    = "\$" . &commify(sprintf("$FMT", $amtdue))    if($amtdue);
    $amtpaid   = "\$" . &commify(sprintf("$FMT", $amtpaid))   if($amtpaid);
    $disp_rcheckamt = "\$" . &commify(sprintf("$FMT", $rcheckamt)) if($rcheckamt);

    $rdos       = substr($rdos, 4, 2)."/".substr($rdos, 6, 2)."/".substr($rdos, 0, 4) if ($rdos);
    $disp_rcheckdate = substr($rcheckdate, 4, 2)."/".substr($rcheckdate, 6, 2)."/".substr($rcheckdate, 0, 4) if ($rcheckdate);
    $rrecdate   = substr($rrecdate, 4, 2)."/".substr($rrecdate, 6, 2)."/".substr($rrecdate, 0, 4) if ($rrecdate);

    if ( $rchecknum ) {
      my $year = substr($rcheckdate, 0, 4);
      my $mon  = substr($rcheckdate, 4, 2);
      my $day  = substr($rcheckdate, 6, 2);

      $sec = 0; $min = 0; $hour = 0;
      $mon = $mon - 1;	# For indexing into abbr array
      $TS = timelocal($sec,$min,$hour,$day,$mon,$year);
    }

    print "<tr>";
    if ($ag) {
      print "<td>$ncpdp</td><td>$rrx</td> <td>$rdos</td> <td>$amtdue</td> <td>$amtpaid</td> <td>$rchecknum</td> <td>$rcheckamt</td> <td>$rcheckdate</td> <td>$rrecdate</td>";
    }
    else {
      print "<td>$rrx</td> <td>$rdos</td> <td>$amtdue</td> <td>$amtpaid</td> <td>$rchecknum</td> <td>$rcheckamt</td> <td>$rcheckdate</td> <td>$rrecdate</td>";
    }

#        <INPUT TYPE="hidden" NAME="REF02"       VALUE="$rref02">
    if ( $rchecknum ) {
    print <<BM;
    <td>
      <FORM ACTION="Retrieve_Remit.cgi" METHOD="POST">
        <INPUT TYPE="hidden" NAME="SRC"         VALUE="search">
        <INPUT TYPE="hidden" NAME="Check_ID"    VALUE="$check_id">
        <INPUT TYPE="hidden" NAME="Payer_ID"    VALUE="$rtpp_pri">
        <INPUT TYPE="hidden" NAME="TPPPRI"      VALUE="$rtpp_pri">
        <INPUT TYPE="hidden" NAME="REF02_STR"   VALUE="$str_ref02">
        <INPUT TYPE="hidden" NAME="PostedBy"   VALUE="$postedby">
        <INPUT TYPE="hidden" NAME="CHKNUM"      VALUE="$rchecknum">
        <INPUT TYPE="hidden" NAME="CHKDATE"     VALUE="$disp_rcheckdate">
        <INPUT TYPE="hidden" NAME="DISPCHKAMT"  VALUE="$disp_rcheckamt">
        <INPUT style="float: lefth; position: relative; top: 0px; padding:2px; margin:0px" TYPE="Submit" NAME="Submit" VALUE="Retrieve Remit">
      </FORM>
    </td>
BM
    }
    else {
      print "<td>No Remit Found</td>";
    }

    print "</tr>\n";

  }
  print "</table>\n";

  if ($cnt == 0){
      print "<p class=\"indent\">No records found for this claim.</p>";
  }
  
  print qq#</tbody>\n#;
#  print qq#</FORM>\n#;
}

sub remits {
  my ($searchnumber) = @_;

  print "<strong><u>PENDING PAYMENTS</u></strong>\n";
  print "<h4>The following REMIT results are for PAYMENTS PENDING (Not yet received)</h4>\n";

  my $dbin    = "R8DBNAME";  # Only database needed for this routine
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
     $dbin    = "P8DBNAME";  # Only database needed for this routine
  my $DBNAMEA = $DBNAMES{"$dbin"};
  my $TABLEA  = $DBTABN{"$dbin"};
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
	$DBNAMEA = "webinar";
  }

  $query = "SELECT R_CLP01_Rx_Number, R_TS3_NCPDP, R_TPP, R_CLP02_Claim_Status_Code, R_DTM02_Date, R_PENDRECV, R_CheckReceived_Date,
                   R_CLP04_Amount_Payed, R_TRN02_Check_Number, R_BPR16_Date, R_BPR02_Check_Amount, R_Reconciled_Date 
              FROM $DBNAME.$TABLE
             WHERE Pharmacy_ID IN ($PH_ID)
                && R_CLP01_Rx_Number = $searchnumber";

  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;

  if ($row_cnt >= 0) {
    print qq#<table border=0 class="responsive fixed">\n#;
    print qq#<tr> <th>Rx\#</th> <th>NCPDP</th> <th>Filled Date</th> <th>Third Party</th> <th>Amt Paid</th> <th>Check \#</th> <th>Check Date</th> <th>Check Amt</th> </tr>\n#;

    foreach $line (@result) {
       @row = split("##", $line);
       $rrx          = $row[0];
       $dbncpdp      = $row[1];
       $rtpp         = $row[2];
       $rclaimstatus = $row[3];
       $rdos         = $row[4];
       $rpr          = $row[5];
       $rprdate      = $row[6];
       $rpaid        = $row[7];
       $rchecknum    = $row[8];
       $rcheckdate   = $row[9];
       $rcheckamt    = $row[10];
       $rrecdate     = $row[11];

       $rpaid     = "\$" . &commify(sprintf("$FMT", $rpaid));
       $rcheckamt = "\$" . &commify(sprintf("$FMT", $rcheckamt));

       my $year = substr($rdos, 0, 4);
       my $mon  = substr($rdos, 4, 2);
       my $day  = substr($rdos, 6, 2);
       $rdos = "$mon/$day/$year";

       my $year2 = substr($rcheckdate, 0, 4);
       my $mon2  = substr($rcheckdate, 4, 2);
       my $day2  = substr($rcheckdate, 6, 2);
       $rcheckdate = "$mon2/$day2/$year2";
      
       print "<tr> <td>$rrx</td> <td>$dbncpdp</td> <td>$rdos</td> <td>$rtpp</td> <td>$rpaid</td> <td>$rchecknum</td> <td>$rcheckdate</td> <td>$rcheckamt</td> </tr>\n";
    }
    print "</table>\n";
  } else {
    print "<p class=\"indent\">No records found for this section.</p>";
  }
}

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

sub remitsarchive {
  my ($searchnumber) = @_;

  print "<strong><u>RECEIVED PAYMENTS</u></strong>\n";
  print "<h4>The following REMIT results are for PAYMENTS RECEIVED and Reconciled</h4>\n";

  my $dbin    = "R8DBNAME";  # Only database needed for this routine
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
     $dbin    = "P8DBNAME";  # Only database needed for this routine
  my $DBNAMEA = $DBNAMES{"$dbin"};
  my $TABLEA  = $DBTABN{"$dbin"};
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
	$DBNAMEA = "webinar";
  }

  $query = "SELECT R_CLP01_Rx_Number, R_TS3_NCPDP, R_TPP, R_DTM02_Date, R_TCode, R_PENDRECV, R_CheckReceived_Date, R_CLP04_Amount_Payed,
                   R_TRN02_Check_Number, R_BPR16_Date, R_BPR02_Check_Amount, R_Reconciled_Date 
              FROM $DBNAMEA.$TABLEA
             WHERE Pharmacy_ID IN ($PH_ID)
                && R_CLP01_Rx_Number = $searchnumber";

  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;

  if ($row_cnt >= 0) {
    print "<table border=0 class=\"responsive fixed\">\n";
    print qq#<tr> <th>Rx\#</th> <th>NCPDP</th> <th>Filled Date</th> <th>Third Party</th> <th>Amt Paid</th> <th>Check \#</th> <th>Check Date</th> <th>Check Amt</th> </tr>\n#;

    foreach $line (@result) {
       @row = split("##", $line);
       $rrx        = $row[0];
       $dbncpdp    = $row[1];
       $rtpp       = $row[2];
       $rdos       = $row[3];
       $rtcode     = $row[4];
       $rpr        = $row[5];
       $rprdate    = $row[6];
       $rpaid      = $row[7];
       $rchecknum  = $row[8];
       $rcheckdate = $row[9];
       $rcheckamt  = $row[10];
       $rrecdate   = $row[11];

       $rpaid     = "\$" . &commify(sprintf("$FMT", $rpaid));
       $rcheckamt = "\$" . &commify(sprintf("$FMT", $rcheckamt));

       my $year = substr($rdos, 0, 4);
       my $mon  = substr($rdos, 4, 2);
       my $day  = substr($rdos, 6, 2);
       $rdos = "$mon/$day/$year";

       my $year2 = substr($rcheckdate, 0, 4);
       my $mon2  = substr($rcheckdate, 4, 2);
       my $day2  = substr($rcheckdate, 6, 2);
       $rcheckdate = "$mon2/$day2/$year2";
      
       print "<tr> <td>$rrx</td> <td>$dbncpdp</td> <td>$rdos</td> <td>$rtpp</td> <td>$rpaid</td> <td>$rchecknum</td> <td>$rcheckdate</td> <td>$rcheckamt</td> </tr>\n";
    }
    print "</table>";
  } else {
    print "<p class=\"indent\">No records found for this section.</p>";
  }
}

sub incoming {
  my ($searchnumber) = @_;

  print "<strong><u>AGED UNPAID CLAIMS</u></strong>\n";
  print "<h4>The following results are for UNPAID or PAID SHORT claims on your AGING report</h4>\n";

  my $dbin    = "RIDBNAME";
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
     $dbin    = "RADBNAME";
  my $DBNAMEA = $DBNAMES{"$dbin"};
  my $TABLEA  = $DBTABN{"$dbin"};
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
	$DBNAMEA = "webinar";
  }

  $query = "SELECT dbRxNumber, dbNCPDPNumber, dbResponseCode, dbCode, dbTCode, dbTotalAmountPaid, dbBinNumber, dbDateOfService, dbDateTransmitted, dbReconciledDate   
              FROM $DBNAME.$TABLE
             WHERE Pharmacy_ID IN ($PH_ID)
                && dbRxNumber = $searchnumber";

  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;

  if ($row_cnt >= 0) {
    print "<table border=0 class=\"responsive fixed\">\n";
    print "<tr> <th>Rx #</th> <th>NCPDP</th> <th>Filled Date</th> <th>BIN</th> <th>Amt Paid</th> <th>Date/Time Processed</th> </tr>\n";

    foreach $line (@result) {
       @row = split("##", $line);
       $irx            = $row[0];
       $dbncpdp        = $row[1];
       $dbresponsecode = $row[2];
       $dbcode         = $row[3];
       $dbtcode        = $row[4];
       $dbpaid         = $row[5];
       $dbbin          = $row[6];
       $dbdos          = $row[7];
       $dbdatetrans    = $row[8];
       $dbrecdate      = $row[9];
 
       $dbpaid     = "\$" . &commify(sprintf("$FMT", $dbpaid));

       my $year = substr($dbdos, 0, 4);
       my $mon  = substr($dbdos, 4, 2);
       my $day  = substr($dbdos, 6, 2);
       $dbdos = "$mon/$day/$year";

       my $year2 = substr($dbdatetrans,  0, 4);
       my $mon2  = substr($dbdatetrans,  4, 2);
       my $day2  = substr($dbdatetrans,  6, 2);
       my $hour2 = substr($dbdatetrans,  8, 2);
       my $min2  = substr($dbdatetrans, 10, 2);
       my $sec2  = substr($dbdatetrans, 12, 2);
       $dbdatetrans = "$mon2/$day2/$year2 $hour2:$min2:$sec2";
      
       print "<tr> <td align=right>$irx</td> <td>$dbncpdp</td> <td>$dbdos</td> <td align=right>$dbbin</td> <td align=right>$dbpaid</td> <td>$dbdatetrans</td> </tr>\n";
    }
    print "</table>";
  } else {
    print "<p class=\"indent\">No records found for this section.</p>";
  }
}

sub incomingarchive {
  my ($searchnumber) = @_;

  print "<strong><u>PAID SWITCH CLAIMS</u></strong>\n";
  print "<h4>The following results are for ARCHIVED PAID claims from AGING</h4>\n";

  my $dbin    = "RIDBNAME";
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
     $dbin    = "RADBNAME";
  my $DBNAMEA = $DBNAMES{"$dbin"};
  my $TABLEA  = $DBTABN{"$dbin"};
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
	$DBNAMEA = "webinar";
  }

  $query = "SELECT dbRxNumber, dbNCPDPNumber, dbResponseCode, dbCode, dbTCode, dbTotalAmountPaid, dbBinNumber, dbDateOfService, dbDateTransmitted, dbReconciledDate   
              FROM $DBNAMEA.$TABLEA
             WHERE Pharmacy_ID IN ($PH_ID)
                && dbRxNumber = $searchnumber";

  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;

  if ($row_cnt >= 0) {
    print "<table border=0 class=\"responsive fixed\">\n";
    print "<tr> <th>Rx #</th> <th>NCPDP</th> <th>Filled Date</th> <th>BIN</th> <th>Amt Paid</th> <th>Date/Time Processed</th> </tr>\n";

    foreach $line (@result) {
      @row = split("##", $line);
      $irx            = $row[0];
      $dbncpdp        = $row[1];
      $dbresponsecode = $row[2];
      $dbcode         = $row[3];
      $dbtcode        = $row[4];
      $dbpaid         = $row[5];
      $dbbin          = $row[6];
      $dbdos          = $row[7];
      $dbdatetrans    = $row[8];
      $dbrecdate      = $row[9];

      $dbpaid     = "\$" . &commify(sprintf("$FMT", $dbpaid));
      my $year = substr($dbdos, 0, 4);
      my $mon  = substr($dbdos, 4, 2);
      my $day  = substr($dbdos, 6, 2);
      $dbdos = "$mon/$day/$year";

      my $year2 = substr($dbdatetrans,  0, 4);
      my $mon2  = substr($dbdatetrans,  4, 2);
      my $day2  = substr($dbdatetrans,  6, 2);
      my $hour2 = substr($dbdatetrans,  8, 2);
      my $min2  = substr($dbdatetrans, 10, 2);
      my $sec2  = substr($dbdatetrans, 12, 2);
      $dbdatetrans = "$mon2/$day2/$year2 $hour2:$min2:$sec2";
      
      print "<tr> <td align=right>$irx</td> <td>$dbncpdp</td> <td>$dbdos</td> <td align=right>$dbbin</td> <td align=right>$dbpaid</td> <td>$dbdatetrans</td> </tr>\n";
    }
    print "</table>";
  } else {
    print "<p class=\"indent\">No records found for this section.</p>";
  }
}

sub remits_check {
  my ($searchnumber) = @_;

  print "<strong><u>PENDING PAYMENT</u></strong>\n";
  print "<h4>The following Check results are for PAYMENTS PENDING (Not yet received)</h4>\n";

  my $dbin    = "R8DBNAME";
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
  my $TABLEC  = 'Checks';
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
  }

  $queryADD  = " Pharmacy_ID IN($PH_ID) AND R_PENDRECV<>'R' AND R_TRN02_Check_Number = $searchnumber";
  
  $query = "  SELECT R_TPP, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_BPR16_Date, R_CheckReceived_Date, R_TS3_NCPDP 
                FROM $DBNAME.$TABLEC
               WHERE $queryADD
            GROUP BY R_TRN02_Check_Number";
  
  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;
  
  if ($row_cnt >= 0) {
     print "<table border=0 class=\"responsive fixed\">\n";
     print "<tr><th>NCPDP</th> <th>Third Party</th> <th>Check #</th> <th>Check Amt</th> <th>Check Date</th> <th>Received Date</th> </tr>"; 
  
     foreach $line (@result) {
        @row = split("##", $line);
        $rtpp         = $row[0];
        $rchecknum    = $row[1];
        $rcheckamt    = $row[2];
        $rcheckdate   = $row[3];
        $rprdate      = $row[4];
        $rncpdp       = $row[5];


        my $year = substr($rcheckdate, 0, 4);
        my $mon  = substr($rcheckdate, 4, 2);
        my $day  = substr($rcheckdate, 6, 2);
        $rcheckdate = "$mon/$day/$year";

        if ( $rprdate =~ /-/ ) {
           my $year = substr($rprdate, 0, 4);
           my $mon  = substr($rprdate, 5, 2);
           my $day  = substr($rprdate, 8, 2);
           $rprdate = sprintf("%02d/%02d/%04d", $mon, $day, $year) ;# . " ($rprdate)";
        } 

        $rcheckamt = "\$" . &commify(sprintf("$FMT", $rcheckamt));
  
        print "<tr>";
        print "<td>$rncpdp</td>";
        print "<td>$rtpp</td>";
        print "<td>$rchecknum</td>";
        print "<td align=right>$rcheckamt</td>";
        print "<td>$rcheckdate</td>";
        print "<td>$rprdate</td>";
        print "</tr>\n"; 
     }
     print "</table>";
  } else {
     print "<p class=\"indent\">No records found for this section.</p>";
  }
}

sub remitsarchive_check {
  my ($searchnumber) = @_;

  print "<strong><u>RECEIVED PAYMENT</u></strong>\n";
  print "<h4>The following Check results are for PAYMENTS RECEIVED and Reconciled</h4>\n";

  my $dbin    = "R8DBNAME";  # Only database needed for this routine
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
     $dbin    = "P8DBNAME";  # Only database needed for this routine
  my $DBNAMEA = $DBNAMES{"$dbin"};
  my $TABLEA  = $DBTABN{"$dbin"};
  my $TABLEC  = 'Checks';
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
	$DBNAMEA = "webinar";
  }

  $searchnumber =~ s/\'//gi;

  if ( $searchnumber !~ /EFT/ ) {
    $searchnumber = "'$searchnumber','EFT-$searchnumber'";
  }
  else {
    $searchnumber = "'$searchnumber'";
  }

  $queryADD  = " Pharmacy_ID IN ($PH_ID) && R_PENDRECV='R' && R_TRN02_Check_Number IN ($searchnumber)";
  
  $query = "SELECT Check_ID, R_TPP, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_BPR16_Date, R_CheckReceived_Date,
                   R_TPP_PRI, R_ISA06_Interchange_Sender_ID, R_TS3_NCPDP, R_PostedBy
              FROM $DBNAME.$TABLEC
             WHERE $queryADD
          GROUP BY R_TRN02_Check_Number";

#  print "$query<br>";
  
  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;
  
  if ($row_cnt >= 0) {
     print "<table border=0 class=\"responsive fixed\">\n";
     print "<tr><th>NCPCP</th> <th>Third Party</th> <th>Check #</th> <th>Check Amt</th> <th>Check Date</th> <th>Received Date</th> <th>Print Remit</th> </tr>"; 
  
     foreach $line (@result) {
        @row = split("##", $line);
        $check_id     = $row[0];
        $rtpp         = $row[1];
        $rchecknum    = $row[2];
        $rcheckamt    = $row[3];
        $rcheckdate   = $row[4];
        $rprdate      = $row[5];
        $rtpp_pri     = $row[6];
        $risa06       = $row[7];
        $rncpdp       = $row[8];
        $postedby     = $row[9];

        my $year = substr($rcheckdate, 0, 4);
        my $mon  = substr($rcheckdate, 4, 2);
        my $day  = substr($rcheckdate, 6, 2);
        $disp_rcheckdate = "$mon/$day/$year";

        if ( $rprdate =~ /-/ ) {
           my $year2 = substr($rprdate, 0, 4);
           my $mon2  = substr($rprdate, 5, 2);
           my $day2  = substr($rprdate, 8, 2);
           $rprdate = "$mon2/$day2/$year2";
        } 

#        ($rtpp, $OtherSource, $Display_TPPID, $Display_on_Remits) = &check_Other_Source($rtpp_pri, $rtpp,
#        $rref01, $rref02, $racttpp);

#        if ( $OtherSource ) {
#           ($NEW_Check_Amount, $COUNT) = &calc_OtherSource_Check_Amount($rncpdp, $rcheckdate, $rref02, $rchecknum);
#        } else {
#           $NEW_Check_Amount = $rcheckamt;
#        }

#        $disp_rcheckamt = "\$" . &commify(sprintf("$FMT", $NEW_Check_Amount));
        $disp_rcheckamt = "\$" . &commify(sprintf("$FMT", $rcheckamt));

        $sec = 0; $min = 0; $hour = 0;
        $mon = $mon - 1;	# For indexing into abbr array
        $TS = timelocal($sec,$min,$hour,$day,$mon,$year);

        print "<tr>";
        print "<td>$rncpdp</td><td>$rtpp</td> <td>$rchecknum</td> <td align=right>$disp_rcheckamt</td> <td>$disp_rcheckdate</td> <td>$rprdate</td>";

        print <<BM;
        <td>
        <FORM ACTION="Retrieve_Remit.cgi" METHOD="POST">
          <INPUT TYPE="hidden" NAME="SRC"         VALUE="search">
          <INPUT TYPE="hidden" NAME="Check_ID"    VALUE="$check_id">
          <INPUT TYPE="hidden" NAME="Payer_ID"    VALUE="$rtpp_pri">
          <INPUT TYPE="hidden" NAME="TPPPRI"      VALUE="$rtpp_pri">
          <INPUT TYPE="hidden" NAME="REF02_STR"   VALUE="$str_ref02">
          <INPUT TYPE="hidden" NAME="PostedBy"   VALUE="$postedby">
          <INPUT TYPE="hidden" NAME="CHKNUM"      VALUE="$rchecknum">
          <INPUT TYPE="hidden" NAME="CHKDATE"     VALUE="$disp_rcheckdate">
          <INPUT TYPE="hidden" NAME="DISPCHKAMT"  VALUE="$disp_rcheckamt">
          <INPUT style="float: right; position: relative; top: 0px; padding:0px; margin:0px" TYPE="Submit" NAME="Submit" VALUE="Retrieve Remit">
        </FORM>
        </td>
BM
  
        print "</tr>\n"; 
     }
     print "</table>";
  } else {
    print "<p class=\"indent\">No records found for this section.</p>";
  }
}

sub remits_checkamt {
  my ($searchnumber) = @_;

  print "<strong><u>PENDING PAYMENT</u></strong>\n";
  print "<h4>The following Check results are for PAYMENTS PENDING (Not yet received)</h4>\n";

  my $dbin    = "R8DBNAME";  # Only database needed for this routine
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
  my $DBNAMEA = $DBNAMES{"$dbin"};
  my $TABLEA  = $DBTABN{"$dbin"};
  my $TABLEC  = 'Checks';
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
	$DBNAMEA = "webinar";
  }

  $queryADD = "a.Pharmacy_ID IN ($PH_ID) AND a.R_BPR02_Check_Amount = $searchnumber AND a.R_PENDRECV<>'R'";
  
  $query = "SELECT R_CLP01_Rx_Number, R_TS3_NCPDP, R_TPP, R_CLP02_Claim_Status_Code, R_DTM02_Date, R_TCode, R_PENDRECV, R_CheckReceived_Date,
                   R_CLP04_Amount_Payed, R_TRN02_Check_Number, R_BPR16_Date, R_BPR02_Check_Amount, R_Reconciled_Date 
              FROM ( SELECT b.R_CLP01_Rx_Number, a.R_TS3_NCPDP, b.R_TPP, b.R_CLP02_Claim_Status_Code, b.R_DTM02_Date, b.R_TCode, a.R_PENDRECV, a.R_CheckReceived_Date,
                            b.R_CLP04_Amount_Payed, a.R_TRN02_Check_Number, a.R_BPR16_Date, a.R_BPR02_Check_Amount, b.R_Reconciled_Date 
                       FROM $DBNAME.$TABLEC a
                       JOIN $DBNAME.$TABLE b ON (a.Check_ID = b.Check_ID)
                      WHERE $queryADD
                  UNION ALL
                     SELECT b.R_CLP01_Rx_Number, a.R_TS3_NCPDP, b.R_TPP, b.R_CLP02_Claim_Status_Code, b.R_DTM02_Date, b.R_TCode, a.R_PENDRECV, a.R_CheckReceived_Date,
                            b.R_CLP04_Amount_Payed, a.R_TRN02_Check_Number, a.R_BPR16_Date, a.R_BPR02_Check_Amount, b.R_Reconciled_Date 
                       FROM $DBNAME.$TABLEC a
                       JOIN $DBNAMEA.$TABLEA b ON (a.Check_ID = b.Check_ID)
                      WHERE $queryADD
                   ) TABA
          GROUP BY R_TRN02_Check_Number, R_BPR02_Check_Amount";

  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;

  if ($row_cnt >= 0) {
     print "<table border=0 class=\"responsive fixed\">\n";
     print "<tr><th>NCPCP</th> <th>Third Party</th> <th>Check #</th> <th>Check Amt</th> <th>Check Date</th> <th>Received Date</th> </tr>"; 
  
     foreach $line (@result) {
        @row = split("##", $line);
        $rrx          = $row[0];
        $dbncpdp      = $row[1];
        $rtpp         = $row[2];
        $rclaimstatus = $row[3];
        $rdos         = $row[4];
        $rtcode       = $row[5];
        $rpr          = $row[6];
        $rprdate      = $row[7];
        $rpaid        = $row[8];
        $rchecknum    = $row[9];
        $rcheckdate   = $row[10];
        $rcheckamt    = $row[11];
        $rrecdate     = $row[12];

        if ( $rprdate =~ /0000-00-00/ ) {
           $rprdate = "";
        } elsif ( $rprdate =~ /-/ ) {
          my $year = substr($rprdate, 0, 4);
          my $mon  = substr($rprdate, 5, 2);
          my $day  = substr($rprdate, 8, 2);
          $rprdate = "$mon/$day/$year";
        }
        my $year = substr($rcheckdate, 0, 4);
        my $mon  = substr($rcheckdate, 4, 2);
        my $day  = substr($rcheckdate, 6, 2);
        $rcheckdate = "$mon/$day/$year";

        $rcheckamt = "\$" . &commify(sprintf("$FMT", $rcheckamt));
        
        print "<tr>\n";
        print "<td>$dbncpdp</td>\n";
        print "<td>$rtpp</td>\n";
        print "<td>$rchecknum</td>\n";
        print "<td align=right>$rcheckamt</td>\n";
        print "<td>$rcheckdate</td>\n";
        print "<td>$rprdate</td>\n";
        print "</tr>\n";
     }
     print "</table>";
  } else {
     print "<p class=\"indent\">No records found for this section.</p>";
  }
}

sub remitsarchive_checkamt {
  my ($searchnumber) = @_;

  print "<strong><u>RECEIVED PAYMENTS</u></strong>\n";
  print "<h4>The following Check results are for PAYMENTS RECEIVED and Reconciled</h4>\n";

  my $dbin    = "R8DBNAME";  # Only database needed for this routine
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = $DBTABN{"$dbin"};
     $dbin    = "P8DBNAME";  # Only database needed for this routine
  my $DBNAMEA = $DBNAMES{"$dbin"};
  my $TABLEA  = $DBTABN{"$dbin"};
  my $TABLEC  = 'Checks';
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$DBNAME  = "webinar";
	$DBNAMEA = "webinar";
  }

  $queryADD = "Pharmacy_ID IN ($PH_ID) && R_BPR02_Check_Amount = $searchnumber && R_PENDRECV='R'";

  $query = "SELECT Check_ID, R_TPP, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_BPR16_Date, R_CheckReceived_Date,
                   R_TPP_PRI, R_ISA06_Interchange_Sender_ID, R_TS3_NCPDP, R_PostedBy
              FROM $DBNAME.$TABLEC
             WHERE $queryADD
         GROUP BY R_TRN02_Check_Number, R_BPR02_Check_Amount";

  (@result) = &mysqli_query("$query");
  $row_cnt = $#result;

  if ($row_cnt >= 0) {
     print "<table border=0 class=\"responsive fixed\">\n";
  
     print "<tr><th>NCPCP</th> <th>Third Party</th> <th>Check #</th> <th>Check Amt</th> <th>Check Date</th> <th>Received Date</th> <th>Print Remit</th> </tr>"; 
  
     foreach $line (@result) {
       @row = split("##", $line);
       $check_id     = $row[0];
       $rtpp         = $row[1];
       $rchecknum    = $row[2];
       $rcheckamt    = $row[3];
       $rcheckdate   = $row[4];
       $rprdate      = $row[5];
       $rtpp_pri     = $row[6];
       $risa06       = $row[7];
       $rncpdp       = $row[8];
       $postedby     = $row[9];

       my $year = substr($rcheckdate, 0, 4);
       my $mon  = substr($rcheckdate, 4, 2);
       my $day  = substr($rcheckdate, 6, 2);
       $disp_rcheckdate = "$mon/$day/$year";

       if ( $rprdate =~ /0000-00-00/ ) {
          $rprdate = "";
       } elsif ( $rprdate =~ /-/ ) {
         my $year = substr($rprdate, 0, 4);
         my $mon  = substr($rprdate, 5, 2);
         my $day  = substr($rprdate, 8, 2);
         $rprdate = "$mon/$day/$year";
       }

       $disp_rcheckamt = "\$" . &commify(sprintf("$FMT", $rcheckamt));

       $sec = 0; $min = 0; $hour = 0;
       $mon = $mon - 1;	# For indexing into abbr array
       $TS = timelocal($sec,$min,$hour,$day,$mon,$year);

       print "<tr>";
       print "<td>$rncpdp</td><td>$rtpp</td> <td>$rchecknum</td> <td align=right>$disp_rcheckamt</td> <td>$disp_rcheckdate</td> <td>$rprdate</td>";

       print <<BM;
       <td>
       <FORM ACTION="Retrieve_Remit.cgi" METHOD="POST">
         <INPUT TYPE="hidden" NAME="SRC"         VALUE="search">
         <INPUT TYPE="hidden" NAME="Check_ID"    VALUE="$check_id">
         <INPUT TYPE="hidden" NAME="Payer_ID"    VALUE="$rtpp_pri">
         <INPUT TYPE="hidden" NAME="TPPPRI"      VALUE="$rtpp_pri">
         <INPUT TYPE="hidden" NAME="REF02_STR"   VALUE="$str_ref02">
         <INPUT TYPE="hidden" NAME="PostedBy"   VALUE="$postedby">
         <INPUT TYPE="hidden" NAME="CHKNUM"      VALUE="$rchecknum">
         <INPUT TYPE="hidden" NAME="CHKDATE"     VALUE="$disp_rcheckdate">
         <INPUT TYPE="hidden" NAME="DISPCHKAMT"  VALUE="$disp_rcheckamt">
         <INPUT style="float: right; position: relative; top: 0px; padding:0px; margin:0px" TYPE="Submit" NAME="Submit" VALUE="Retrieve Remit">
       </FORM>
       </td>
BM
  
       print "</tr>\n"; 
     }
     print "</table>";
  } else {
     print "<p class=\"indent\">No records found for this section.</p>";
  }
}

sub mysqli_query {
  my ($sql) = @_;

  $sthLM = $dbx->prepare($sql);
  $sthLM->execute();
    
  my $NumOfRows = $sthLM->rows;

  @result = ();
  if ( $NumOfRows > -1 ) {
     while ( my @row = $sthLM->fetchrow_array() ) {
        $line = join("##", @row);
#       print "line: $line<br>\n";
        push(@result, $line);
     }
  }
  $sthLM->finish;

  return(@result);
}

#______________________________________________________________________________

sub calc_OtherSource_Check_Amount {
  my ($inNCPDP, $SFDATE2, $REF02_Value, $CheckNumber) = @_;
  my $PLB_REF02 = $REF02_Value;
  my $Q = 'CD';
  $PLB_REF02 =~ s/'//g;
  $PLB_REF02 =~ s/,/\|/g;
  $PLB_REF02 =~ s/\|\|/\|/g;
  $PLB_REF02 =~ s/^\|//g;
  $PLB_REF02 =~ s/\|$//g;

  my $NEW_Check_Amount = 0;
  my $Amount_Payed = 0;
  my $Amount_PLBs  = 0;
  my $COUNT        = 0;

  my $R8dbin     = "R8DBNAME";
  my $R8DBNAME = $DBNAMES{"$R8dbin"};
  my $R8TABLE  = $DBTABN{"$R8dbin"};

  my $P8dbin     = "P8DBNAME";
  my $P8DBNAME = $DBNAMES{"$P8dbin"};
  my $P8TABLE  = $DBTABN{"$P8dbin"};
  
  if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23" ) {
	$R8DBNAME  = "webinar";
	$P8DBNAME = "webinar";
  }

  my $sql = "";

#  # selected a Date from previous page
  $sql  = "SELECT round(sum(sum),2), sum(cnt)
             FROM (  SELECT sum(R_CLP04_Amount_Payed) as sum, count(*) as cnt 
                      FROM $P8DBNAME.$P8TABLE
                      WHERE Pharmacy_ID IN ($PH_ID)
                         && R_PENDRECV = 'R'
                         && R_REF02_Value IN ('$REF02_Value')
                         && R_TRN02_Check_Number = '$CheckNumber' 
                         && ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2' \n";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2' \n";
  }

  $sql .= "      UNION ALL
                     SELECT sum(R_CLP04_Amount_Payed) as sum, count(*) as cnt
                      FROM $R8DBNAME.$R8TABLE
                      WHERE Pharmacy_ID IN ($PH_ID)
                         && R_PENDRECV = 'R'
                         && R_REF02_Value IN ('$REF02_Value')
                         && R_TRN02_Check_Number = '$CheckNumber' 
                         && ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2' \n";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2' \n";
  }

  $sql .= " ) a \n";

  (my $sqlout = $sql) =~ s/\n/<br>\n/g;

  $stAmounts = $dbx->prepare($sql);
  $numofrows = $stAmounts->execute;
  print "numofrows: $numofrows<br>\n" if ($debug);

  if ( $numofrows > 0 ) {
    while (my @row = $stAmounts->fetchrow_array()) {
      ($Amount_Payed, $COUNT) = @row;
    }
  } else {
    $Amount_Payed = 0;
    $Amount_PLBs  = 0;
    $COUNT        = 0;
  }
  $stAmounts->finish;

  $sql  = "SELECT round(max(Total_PLBs),2)
             FROM ( SELECT  
                           (IF ( R_PLB03_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB04_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB05_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB06_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB07_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB08_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB09_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB10_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB11_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB12_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB13_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB14_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB15_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB16_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB17_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB18_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB19_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB20_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB21_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB22_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB23_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB24_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB25_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB26_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB27_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB28_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB29_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB30_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB31_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB32_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB33_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB34_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB35_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB36_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB37_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB38_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB39_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB40_Adjustment_Amount, 0), 0) 
                           ) as 'Total_PLBs'
                      FROM $P8DBNAME.$P8TABLE
                      WHERE Pharmacy_ID IN ($PH_ID)
                         && R_PENDRECV = 'R'
                         && R_TRN02_Check_Number = '$CheckNumber' 
                         && ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2' \n";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2' \n";
  }

  $sql .= "      UNION ALL
                    SELECT 
                           (IF ( R_PLB03_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB04_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB05_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB06_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB07_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB08_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB09_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB10_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB11_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB12_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB13_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB14_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB15_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB16_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB17_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB18_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB19_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB20_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB21_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB22_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB23_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB24_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB25_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB26_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB27_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB28_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB29_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB30_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB31_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB32_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB33_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB34_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB35_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB36_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB37_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB38_Adjustment_Amount, 0), 0) +
                            IF ( R_PLB39_02_Adjustment_Description REGEXP '($PLB_REF02)', IFNULL(R_PLB40_Adjustment_Amount, 0), 0) 
                           ) as 'Total_PLBs'
                      FROM $R8DBNAME.$R8TABLE
                      WHERE Pharmacy_ID IN ($PH_ID)
                         && R_PENDRECV = 'R'
                         && R_TRN02_Check_Number = '$CheckNumber' 
                         && ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2' \n";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2' \n";
  }

  $sql .= " ) a \n";

  (my $sqlout = $sql) =~ s/\n/<br>\n/g;
 
  $stAmounts = $dbx->prepare($sql);
  $numofrows = $stAmounts->execute;
  print "numofrows: $numofrows<br>\n" if ($debug);

  if ( $numofrows > 0 ) {
    while (my @row = $stAmounts->fetchrow_array()) {
      ($Amount_PLBs) = @row;
    }
  } else {
    $Amount_PLBs  = 0;
  }
  $stAmounts->finish;

  $NEW_Check_Amount = $Amount_Payed - $Amount_PLBs;

  return($NEW_Check_Amount, $COUNT);
}

#______________________________________________________________________________
#______________________________________________________________________________
