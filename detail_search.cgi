use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Data::Dumper qw(Dumper);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

&readsetCookies;

$PH_ID = $in{'PH_ID'};
$rxnumber = $in{'rxnumber'};

$dbin     = "RIDBNAME";
$database = $DBNAMES{"$dbin"};
$database = 'webinar' if ($PH_ID == 23);

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

%cscodes = ();

#______________________________________________________________________________

if ( $USER ) {
  if ( $in{'btn_save'} =~ /Save/i ) {
    &update_data();
  }
  else {
    &build_codes_hash();
    &displayDetails();
  }
} else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  exit(0);
}

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

exit(0);

#______________________________________________________________________________
#______________________________________________________________________________

sub displayDetails {
  my $sel_ids = $in{'pcwnr_id'};
  print "Content-type: text/html\n\n";

  print qq#<!doctype html> 
                 <html lang="en">
                   <head>
                     <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

                     <TITLE>Detail Search</TITLE>
   
                     <link href='https://fonts.googleapis.com/css?family=Roboto:400,300,700,400italic' rel='stylesheet' type='text/css'>
                     <link type="text/css" rel="stylesheet" media="screen" href="../css/new_style.css" />
                     <link type="text/css" rel="stylesheet" media="screen" href="../css/reconrx_style.css" />
                     <link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />

                   </head>

                   <body style="background-color: \#133562;">#;

#  print "<h3><span class=\"searchtext\">Searching NCPDP: </span>$ncpdp_disp <span class=\"searchtext\">for Rx Number: </span>$searchnumber_disp</h3>\n";

  print "<div id=\"detail_wrapper\">";
  print "<h2><u>ReconRx Detailed Search</u></h2>";
  print qq#<form name="frm" id="frm" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<INPUT TYPE="hidden" NAME="PH_ID" VALUE="$PH_ID">\n#;
  &remits();
  print "<hr />\n";
#  print "<div class=\"archive\">";
  &remitsarchive();
#  print "</div>";
  print "<hr />\n";
  &incoming();
  print "<hr />\n";
#  print "<div class=\"archive\">";
  &incomingarchive();
  print "<hr />\n";
#  print "<button name='btn_save' type='button' form='frm' value='Save' onclick='form.submit()'>Save</button><button type='button' onclick='window.close()'>Close</button>";
  print "<input name='btn_save' type='submit' value='Save'><button type='button' onclick='window.close()'>Close</button>";
  print "</form>";
  print "</div></html>";
}

#-----------------------------------------------------------------------------
#
sub remits {
  print "<h2>835remits Results (Remits)</h2>\n";

  $sql = "SELECT R_CLP01_Rx_Number, a.R_TS3_NCPDP, a.R_TPP, R_CLP02_Claim_Status_Code, R_DTM02_Date, R_PENDRECV, R_CheckReceived_Date, R_CLP04_Amount_Payed, R_TRN02_Check_Number, R_BPR16_Date, R_BPR02_Check_Amount, R_Reconciled_Date 
            FROM $database.835remitstb a
            JOIN $database.checks b ON a.check_id = b.check_id
           WHERE a.Pharmacy_ID = $PH_ID
              && R_CLP01_Rx_Number = '$rxnumber'";

#  print "$sql<br>";
 
  my $sth = $dbx->prepare("$sql");
  $rowsfound = $sth->execute;

  if ( $rowsfound > 0 ) {
    print "<table border=0 class=\"responsive fixed\">\n";
    print "<tr><th>Rx#</th><th>NCPDP</th><th class=\"small\">CS</th><th>DOS</th><th>TPP</th><th>P/R</th><th>P/R Date</th><th>Paid</th><th>Check #</th><th>ChkDate</th><th>ChkAmt</th><th>Rec. Date</th></tr>";

    while ( my ($rrx, $dbncpdp, $rtpp, $rclaimstatus, $rdos, $rpr, $rprdate, $rpaid, $rchecknum, $rcheckdate, $rcheckamt, $rrecdate) = $sth->fetchrow_array() ) {
      print "<tr><td>$rrx</td><td>$dbncpdp</td><td>$rclaimstatus</td><td>$rdos</td><td>$rtpp</td><td>$rpr</td><td>$rprdate</td><td>\$$rpaid</td><td>$rchecknum</td><td>$rcheckdate</td><td>\$$rcheckamt</td><td>$rrecdate</td></tr>\n";
    }

    print "</table>";
  }
  else {
    print "<p class=\"indent\">No records found in 835remits</p>";
  }

  $sth->finish();
}

#-----------------------------------------------------------------------------

sub remitsarchive {
  print "<h2>835remits Archive Results (Remits Archive)</h2>\n";

  $sql = "SELECT R_CLP01_Rx_Number, a.R_TS3_NCPDP, a.R_TPP, R_CLP02_Claim_Status_Code, R_DTM02_Date, R_TCode, R_PENDRECV, R_CheckReceived_Date, R_CLP04_Amount_Payed, R_TRN02_Check_Number, R_BPR16_Date, R_BPR02_Check_Amount, R_Reconciled_Date            FROM $database.835remitstb_archive a
            JOIN $database.checks b ON a.check_id = b.check_id
           WHERE a.Pharmacy_ID = $PH_ID
              && R_CLP01_Rx_Number = '$rxnumber'";

#  print "$sql<br>";
 
  my $sth = $dbx->prepare("$sql");
  $rowsfound = $sth->execute;

  if ( $rowsfound > 0 ) {
    print "<table border=0 class=\"responsive fixed\">\n";
    print "<tr><th>Rx#</th><th>NCPDP</th><th class=\"smallcol\">TC</th><th>DOS</th><th>TPP</th><th>P/R</th><th>P/R Date</th><th>Paid</th><th>Check #</th><th>ChkDate</th><th>ChkAmt</th><th>Rec. Date</th></tr>";

    while ( my ($rrx, $dbncpdp, $rtpp, $rclaimstatus, $rdos, $rtcode, $rpr, $rprdate, $rpaid, $rchecknum, $rcheckdate, $rcheckamt, $rrecdate) = $sth->fetchrow_array() ) {
      print "<tr><td>$rrx</td><td>$dbncpdp</td><td>$rclaimstatus</td><td>$rdos</td><td>$rtpp</td><td>$rpr</td><td>$rprdate</td><td>\$$rpaid</td><td>$rchecknum</td><td>$rcheckdate</td><td>\$$rcheckamt</td><td>$rrecdate</td></tr>\n";
    }

    print "</table>";
  }
  else {
    print "<p class=\"indent\">No records found in 835remits Archive</p>";
  }

  $sth->finish();
}

#-----------------------------------------------------------------------------

sub incoming {
  print "<h2>Incoming Results (Aging)</h2>\n";

  $sql = "SELECT incomingtbID, dbRxNumber, dbNCPDPNumber, dbResponseCode, dbCode, dbTCode, dbTotalAmountPaid, dbBinNumber, dbBinParentdbkey, dbDateOfService, dbDateTransmitted, dbReconciledDate, 835remitstbID
            FROM $database.incomingtb clm
       LEFT JOIN $database.835remitstb rmt ON (clm.pharmacy_id = rmt.pharmacy_id
                                        AND clm.dbRxNumber = rmt.R_CLP01_Rx_Number
                                        AND clm.dbDateOfService = rmt.R_DTM02_Date
                                        AND clm.dbTotalAmountPaid_Remaining = rmt.R_CLP04_Amount_Payed
                                        AND clm.pharmacy_id = $PH_ID
                                        AND clm.dbRxNumber = '$rxnumber'
                                        AND clm.dbCode <> 'PD')
            LEFT JOIN $database.checks b ON (rmt.check_id = b.check_id AND b.R_PENDRECV='P')
           WHERE clm.Pharmacy_ID = $PH_ID
              && clm.dbRxNumber = '$rxnumber'";

#  print "$sql<br>";
 
  my $sth = $dbx->prepare("$sql");
  $rowsfound = $sth->execute;

  if ( $rowsfound > 0 ) {
    print "<table border=0 class=\"responsive fixed\">\n";
    print "<tr><th>RxNumber</th><th>NCPDP</th><th>RC</th><th>Code</th><th>TCode</th><th>Paid</th><th>Bin#</th><th>DOS</th><th>DateTrans</th><th>Rec. Date</th><th>Flag</th></tr>\n";

    while ( my ($id, $irx, $dbncpdp, $dbresponsecode, $dbcode, $dbtcode, $dbpaid, $dbbin, $dbpkey, $dbdos, $dbdatetrans, $dbrecdate, $rmt_id) = $sth->fetchrow_array() ) {
      print "<tr><td>$irx</td><td>$dbncpdp</td>
                 <td>$dbresponsecode</td>
                 <td>$dbcode</td>
                 <td>$dbtcode</td>
                 <td>\$$dbpaid</td>
                 <td>$dbbin</td>
                 <td>$dbdos</td>
                 <td>$dbdatetrans</td>
                 <td>$dbrecdate</td>";

      if ( $rmt_id ) {
        print "<td style='color: green'>Matches Pending Remit</td>";
      }
      else {
        print "  <td><select name='UPD_${id}_${dbpkey}'>
                       <option value=''>-Select-</option>";

        foreach my $key (sort { $a cmp $b } keys %cscodes) {
          print "<option value='$cscodes{$key}'>$key</option>";
        }

        print "      </select></td>\n";
      }

      print "</tr>\n";
    }

    print "</table>";
  }
  else {
    print "<p class=\"indent\">No records found in Incoming</p>";
  }

  $sth->finish();
}

#-----------------------------------------------------------------------------

sub incomingarchive {
  print "<h2>Incoming Archive Results (Aging Archive)</h2>\n";

  $sql = "SELECT dbRxNumber, dbNCPDPNumber, dbResponseCode, dbCode, dbTCode, dbTotalAmountPaid, dbBinNumber, dbDateOfService, dbDateTransmitted, dbReconciledDate   
            FROM $database.incomingtb_archive 
           WHERE Pharmacy_ID = $PH_ID
              && dbRxNumber = '$rxnumber'";

#  print "$sql<br>";
 
  my $sth = $dbx->prepare("$sql");
  $rowsfound = $sth->execute;

  if ( $rowsfound > 0 ) {
    print "<table border=0 class=\"responsive fixed\">\n";
    print "<tr><th>RxNumber</th><th>NCPDP</th><th>RC</th><th>Code</th><th>TCode</th><th>Paid</th><th>Bin#</th><th>DOS</th><th>DateTrans</th><th>Rec. Date</th><th>&nbsp;</th></tr>\n";

    while ( my ($irx, $dbncpdp, $dbresponsecode, $dbcode, $dbtcode, $dbpaid, $dbbin, $dbdos, $dbdatetrans, $dbrecdate) = $sth->fetchrow_array() ) {
      print "<tr><td>$irx</td><td>$dbncpdp</td><td>$dbresponsecode</td><td>$dbcode</td><td>$dbtcode</td><td>\$$dbpaid</td><td>$dbbin</td><td>$dbdos</td><td>$dbdatetrans</td><td>$dbrecdate</td></tr>\n";
    }

    print "</table>";
  }
  else {
    print "<p class=\"indent\">No records found in Incoming Archive</p>";
  }

  $sth->finish();
}

#______________________________________________________________________________

sub update_data {
  my ($key, $code, $sql);

  print "Content-type: text/html\n\n";

  print qq#<!doctype html> 
                 <html lang="en">
                   <head>
                     <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

                     <TITLE>Detail Search</TITLE>

                   </head>

                   <body>#;
  
  foreach $key (sort keys %in) {
#     print "$key => $in{$key}<br>";
     next if ( $key !~ /^UPD/i || $in{$key} eq '');
     $code = $in{$key};

     my ($junk, $incoming_id, $tpp_id) = split("_", $key);

     $sql  = "UPDATE $database.incomingtb
                 SET dbCode = '$code'
               WHERE incomingtbID = $incoming_id";

#     print "$sql<br>";
     $dbx->do($sql) or die $DBI::errstr;

     if ( $code =~ /FRR/i ) {
       $sql  = "REPLACE INTO $database.incomingtb_review (Pharmacy_ID, tpp_id, incomingtbID, cscode, status)
                VALUES ( $PH_ID, $tpp_id, $incoming_id, '$code', '$code')";
     }
     elsif ( $code =~ /NP/i ) {
       $sql  = "DELETE FROM $database.incomingtb_review WHERE incomingtbID = $incoming_id";
     }
     else {
       $sql  = "REPLACE INTO $database.incomingtb_review (Pharmacy_ID, tpp_id, incomingtbID, cscode, status)
                VALUES ( $PH_ID, $tpp_id, $incoming_id, '$code', NULL)";
     }


#     print "$sql<br>";
     $dbx->do($sql) or die $DBI::errstr;
  }

#  print "<script>window.opener.location.reload(true); window.close();</script></html>\n";
  print "<script>window.close();</script></html>\n";
#  print "<button name='close' onClick='window.opener.location.reload(true); window.close();'>Close</button></html>\n";
}

#______________________________________________________________________________

sub build_codes_hash {
  $sql = "SELECT code, dscr
            FROM $database.cscodes";

#  print "$sql<br>";

  my $sth    = $dbx->prepare("$sql");
  my $numrows = $sth->execute();
  $cscodes{'Original State'} = 'NP';
	
  while( my ($code, $dscr) = $sth->fetchrow_array() ) {
    $cscodes{$dscr} = $code;
  }

  $sth->finish();
}

#______________________________________________________________________________

