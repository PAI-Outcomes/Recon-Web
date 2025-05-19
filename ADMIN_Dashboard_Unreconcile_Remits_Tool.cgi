## Unreconcile and Remove
# Purpose: To automatically unreconcile and/or remove remits/checks
# Date last updated: 17 January 2023
# Version: 2.1.0
# Maintainer: Katherine Hays
##


# Might use later, idk 
# if ($OWNER !~ /^\s*$/) { $POSTER = $OWNER; } else { $POSTER = $Pharmacy_Name; }
    # &logActivity($POSTER, $sql, $USER);

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Excel::Writer::XLSX;

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";
my $testing = 0;
$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;
  
my $remits_archive   = '835remitstb_archive';
my $remits_prod      = '835remitstb';
my $incoming = $testing ? 'incomingtb_new' : 'incomingtb';
my $incoming_archive = $testing ? 'incomingtb_new_archive' : 'incomingtb_archive';
my $exc_ids; 

foreach $key (sort keys %in) {
  $$key = $in{$key};
}

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;
   exit(0);
}

#______________________________________________________________________________

&hasAccess($USER);

if ( $ReconRx_UnReconcile_Tool !~ /^Yes/i ) {
   print qq#<p class="yellow"><font size=+1><strong>\n#;
   print qq#$prog<br><br>\n#;
   print qq#<i>You do not have access to this page.</i>\n#;
   print qq#</strong></font>\n#;
   print qq#</p><br>\n#;
   print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

   &trailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

print qq#
<style>
label{
    display: inline-block;
    float: left;
    clear: left;
    width: 120px;
    text-align: left;
}
.input-text {
  display: inline-block;
  float: left;
}
</style>#;

#______________________________________________________________________________

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong><br>\n#;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;    # reported as "years since 1900".
$month += 1;    # reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

$long_time  = sprintf("%04d%02d%02d%02d%02d", $year, $month, $day, $hour, $min);

($in_TPP_ID, $in_TPP_BIN, $in_TPP_NAME) = split("##", $filter_in, 3);
 
#______________________________________________________________________________
#______________________________________________________________________________

my $USEDBNAME;
if ( $testing ) {
 
  
   $WHICHDB = "Testing";        # Valid Values: "Testing" or "Webinar"
   &set_Webinar_or_Testing_DBNames;
  
   $HHH = $DBNAMES{"R8DBNAME"}; print "HHH: $HHH<br>\n";
   print "R8DBNAME: $R8DBNAME, R8TABLE : $R8TABLE<br>\n";
   print "P8DBNAME: $P8DBNAME, P8TABLE : $P8TABLE<br>\n";
   print "<hr>\n";
   $USEDBNAME = "testing";
} else {
   $USEDBNAME = "reconrxdb";
}
#______________________________________________________________________________
#______________________________________________________________________________

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};
# $testing = 1;
my $dbi_connection = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&getCIDs;

&displayPage;

#______________________________________________________________________________
# Close the Database

$dbi_connection->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
sub displayPage {
  print "<hr>\n";
  
  print qq#
  <link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
  <script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
  <script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>
  <script>
  
  
  function checkData1() {
    if (
      (
        document.querySelector('input[name="unreconciled_selected"]:checked') == null
        && document.querySelector('input[name="remove_selected"]:checked') == null
      )
      || document.querySelector('input[name="check_number"]') == null
      || document.querySelector('input[name="ncpdp"]') == null
    ) {
      window.alert("You need to choose a check to unreconcile");
      return false;
    } else {
      let chx = document.getElementsByName("unreconciled_selected");
      const unrecon_array = [];
      const remove_array = [];
      
      for (var i=0; i<chx.length; i++) {
        if (chx[i].type == 'radio' && chx[i].checked) {
         unrecon_array.push(chx[i].value);
        } 
      }
      
      document.getElementById('check_unreconcile').value = unrecon_array.join(",");
      
      chx = document.getElementsByName("remove_selected");
      
      for (var i=0; i<chx.length; i++) {
        if (chx[i].type == 'checkbox' && chx[i].checked) {
         remove_array.push(chx[i].value);
        }
      }
      document.getElementById('check_zremove').value = remove_array.join(",");
    }
  }

  
  </script>
  #;
  
  
  
  # -------------------------------------------------------------------------------- #
  
  print "in_TPP_ID: $in_TPP_ID<br>\n" if ($debug);

  my ($TPP_ID, $TPP_BIN, $TPP_NAME);
  
  # -------------------------------------------------------------------------------- #
 
  print qq~
  <style>
  \@import url('//maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css');

  .info-msg,
  .success-msg,
  .warning-msg,
  .error-msg {
    margin: 10px 0;
    padding: 10px;
    border-radius: 3px 3px 3px 3px;
  }
  .success-msg {
    color: #270;
    background-color: #DFF2BF;
  }
  .error-msg {
    color: #D8000C;
    background-color: #FFBABA;
  }
  .warning-msg {
   color: #9F6000;
   background-color: #FEEFB3;
  }
  </style>
  ~;

  print qq#<form action="$PROG" method="POST" onsubmit="return checkData1()">#;
  print qq#
	<INPUT TYPE="hidden" ID="check_unreconcile" NAME="check_unreconcile">
	<INPUT TYPE="hidden" ID="check_zremove" NAME="check_zremove">
  #;
  print qq#<label for="ncpdp">Pharmacy:*</label>#;
  print qq#<input class="input-text" id="ncpdp" type="text" name="ncpdp" list="plist"
    value="$ncpdp" class="recon-dropdown-form" 
    style="width:300px;" onchange="this.form.submit();">\n#;
  print qq#<datalist id="plist" >#;

  $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
    FROM officedb.pharmacy 
    WHERE (Status_ReconRx IN ('Active','Transition') OR Status_ReconRx_Clinic IN ('Active','Transition'))
      && NCPDP NOT IN (2222222,3333333,5555555)
    UNION ALL
    SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
      FROM officedb.pharmacy_coo
    WHERE (Status_ReconRx IN ('Active','Transition') OR Status_ReconRx_Clinic IN ('Active','Transition'))
      && NCPDP NOT IN (2222222,3333333,5555555)
    ORDER BY Pharmacy_Name";

  my $sthx  = $dbi_connection->prepare("$sql");
  $sthx->execute;

  while ( my ($ph_id, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    print qq#<option value="$NCPDP - $Pharmacy_Name"> </option>\n#;
  }

  $sthx->finish;
  print "</datalist><br>";
  my $NCPDP_sub = substr($ncpdp, 0,7);
  print qq~
  <label for="check_number">Check Number:*</label>
    <input class="input-text" id="check_number" type="text" name="check_number" value="$check_number"
      onchange="this.form.submit()";></input>
  
  <br>
  <label for="check_amount">Check Amount:</label>
    <input class="input-text" id="check_amount" type="text" name="check_amount" value="$check_amount"
      onchange="this.form.submit()";></input>
  
  <br>
  ~;
  
  print qq#<p><INPUT class="button-form" TYPE="submit" VALUE="Unreconcile/Remove"></p>#;
  print qq#</form>#;
  
  print "<hr />\n";
  
  if (($NCPDP_sub !~ /^\s*$/ && $NCPDP_sub > 0)
  && $check_number ne undef) {
    &displayDataWeb($NCPDP_sub);
  } else {
    print "<p>Please fill out all required information to continue</p>";
  }
}

#______________________________________________________________________________

sub displayDataWeb {

  #%filter_PayerIDs   = ();
  my $NCPDP_sub = shift;
  my $dbin    = "R8DBNAME";
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = 'Checks';

  my $sql = "SELECT Check_ID, R_TS3_NCPDP, R_TPP, R_TRN02_Check_Number, R_BPR02_Check_Amount,
    R_BPR16_Date, R_BPR04_Payment_Method_Code, R_PENDRECV
    FROM $DBNAME.$TABLE 
    LEFT JOIN officedb.third_party_payers tpp
    ON R_TPP_PRI = Third_Party_Payer_ID
    WHERE 1=1 
    AND (
      R_PENDRECV IN ('P', 'M')
      OR (
        R_PENDRECV = 'R'
        AND R_CheckReceived_Date >= (NOW() - INTERVAL 30 DAY )
      )
    )";

  if ($NCPDP_sub != undef) {
    $sql .= " AND $TABLE.R_TS3_NCPDP = '$NCPDP_sub' ";
  }
  if ($check_number) {
    $sql .= " AND $TABLE.R_TRN02_Check_Number = '$check_number' ";
  }
  if ($check_amount) {
    $sql .= " AND $TABLE.R_BPR02_Check_Amount = $check_amount ";
  }
  
  $sql .= " ORDER BY R_TS3_NCPDP, R_BPR16_Date";
           
  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  
  # print "$sql" if $testing;
  
  my $sthx  = $dbi_connection->prepare("$sql");
  my $numrows = $sthx->execute;
  
  if ($numrows > 0) {
    print qq#<table class="main">\n#;
    print qq#
    <tr>
    <th>NCPDP</th>
    <th>TPP</th>
    <th>Check\#</th>
    <th style="padding-right: 20px">Check Amount</th>
    <th>Check Date</th>
    <th>Pmt Type</th>
    <th style="text-align:center">Pmt Status</th>
    <th style="text-align:center">Unreconcile</th>
    <th style="text-align:center">Remove</th>
    </tr>\n#;
    
    my $row = 1;
    
    while ( my (@row) = $sthx->fetchrow_array() ) {
      my ($CID, $R_TS3_NCPDP, $R_TPP, $R_TRN02_Check_Number, $R_BPR02_Check_Amount,
      $R_BPR16_Date, $R_BPR04_Payment_Method_Code, $R_PENDRECV) = @row;
      
      $R_TS3_NCPDP = sprintf("%07d", $R_TS3_NCPDP);
      
      my $R_BPR16_DateDisplay = substr($R_BPR16_Date, 4, 2) . "/" . substr($R_BPR16_Date, 6, 2) . "/" . substr($R_BPR16_Date, 0, 4);
      
      if ($row % 2 == 0) {
        $row_color = "lj_blue_table";
      } else {
        $row_color = "";
      }

      my $disabled = $R_PENDRECV eq 'R' ? '' : 'disabled';
      print qq#
      <tr>
      <td class="$row_color">$R_TS3_NCPDP</td>
      <td class="$row_color">$R_TPP</td>
      <td class="$row_color">$R_TRN02_Check_Number</td>
      <td class="$row_color" style="padding-right: 20px" align=right>$R_BPR02_Check_Amount</td>
      <td class="$row_color">$R_BPR16_DateDisplay</td>
      <td class="$row_color">$R_BPR04_Payment_Method_Code $CID</td>
      <td class="$row_color" align=center>$R_PENDRECV</td>
      <td class="$row_color"align=center>
        <input type="radio" name="unreconciled_selected"  value="$CID" $disabled>
      </td>
      <td class="$row_color"align=center>
        <input type="checkbox" name="remove_selected"  value="$CID">
      </td>
      </tr>\n#;
      
      $row++;
    }
    print "</table>\n";
    
    
    print qq#<hr />#;
    
    
    print qq#</form>#;
  } else {
    print "<p>No rows found.</p>\n";
  }
  
  $sthx->finish;
}

#______________________________________________________________________________

sub getCIDs {
  foreach $key (sort keys %in) {
    my $unreconcile_check;
    if ($key =~ /check_unreconcile/) {
        $cid = $in{$key};
       $unreconcile_check = unreconcile($cid) if $cid; 
    }
    if ($key =~ /check_zremove/ && ($unreconcile_check == undef
      || $unreconcile_check == 1)) {
        $cid = $in{$key};
       remove($cid) if $cid; 
    } elsif ($key =~ /check_zremove/) {
      print qq~
      <div class="warning-msg">
        <i class="fa fa-warning"></i>
        Check could not be removed because reconciliation failed.
      </div>
      ~;
    }
  } 
}


sub unreconcile {
  my $cid = shift;

  my $sqlST = qq~START TRANSACTION;~;
  my $sthSTART  = $dbi_connection->prepare($sqlST) or die "Can't prepare\n";
  my $rowsfound = $sthSTART->execute or die "Can't execute\n";
  my $sthCOMMIT;

  print "Inserting/deleting remits_archive -> remits table <br>" if $testing;
  
  my $insert = "INSERT into $USEDBNAME.$remits_prod
    SELECT * from $USEDBNAME.$remits_archive
    WHERE $remits_archive.check_id = $cid
    AND rec_claim_id IS NOT NULL
 ##   AND R_CLP04_Amount_Payed > 0; ";
  
  my $insert_prep = $dbi_connection->prepare($insert) or die "Error!";
  my $insert_with_rec = $insert_prep->execute();

  my $delete = "DELETE FROM $USEDBNAME.$remits_archive
    WHERE $remits_archive.check_id = $cid
    AND rec_claim_id IS NOT NULL
##    AND R_CLP04_Amount_Payed > 0;";
  
  my $delete_prep = $dbi_connection->prepare($delete) or die "Error!";
  my $delete_with_rec = $delete_prep->execute();
  
  $insert = "INSERT into $USEDBNAME.$remits_prod
    SELECT * from $USEDBNAME.$remits_archive
    WHERE $remits_archive.check_id = $cid
    AND (rec_claim_id IS NULL || R_CLP04_Amount_Payed = 0);";
  $insert_prep = $dbi_connection->prepare($insert) or die "Error!";
  my $insert_wo_rec = $insert_prep->execute();

  $delete = "DELETE FROM $USEDBNAME.$remits_archive
    WHERE $remits_archive.check_id = $cid
    AND (rec_claim_id IS NULL || R_CLP04_Amount_Payed = 0);";
  
  $delete_prep = $dbi_connection->prepare($delete) or die "Error!";
  my $delete_wo_rec = $delete_prep->execute();
  
  my $rcid = "SELECT rec_claim_ID FROM $USEDBNAME.$remits_prod
    WHERE Check_ID = $cid";
  
  print "Inserting/deleting incoming_archive -> incoming table <br>" if $testing;
  $insert = "INSERT INTO $USEDBNAME.$incoming
    SELECT I.* from $USEDBNAME.$incoming_archive I
    WHERE I.incomingtbid IN ($rcid);";
  $insert_prep = $dbi_connection->prepare($insert) or die "Error!";
  my $insert_found_inc = $insert_prep->execute();
  
  $delete = "DELETE I.*
    FROM $USEDBNAME.$incoming_archive I
      WHERE I.incomingtbid IN ($rcid);";
  $delete_prep = $dbi_connection->prepare($delete) or die "Error!";
  my $delete_found_inc = $delete_prep->execute();

  print "Updating incoming table<br>" if $testing;
  
  my $update = "UPDATE $USEDBNAME.$incoming I
    JOIN $USEDBNAME.$remits_prod R ON R.rec_claim_id = I.incomingtbid
      AND R.check_id = $cid
    SET I.dbTotalAmountPaid_Remaining =
    CASE
      WHEN ((R.R_CLP04_Amount_Payed != I.dbTotalAmountPaid) && I.dbTotalAmountPaid_Remaining = 0)
      THEN (I.dbTotalAmountPaid)
    END,
    I.dbTCode =
    CASE
      WHEN ((R.R_CLP04_Amount_Payed != I.dbTotalAmountPaid) && I.dbTotalAmountPaid_Remaining != 0)
      THEN 'PP' 
      ELSE NULL 
    END,
    dbReconciledDate = NULL,
    dbCode = 'NP',
    dbComments = CONCAT(IFNULL(dbComments,''), ' Unreconciliation for $cid processed automatically at ', NOW())
    WHERE R.check_id = $cid;";
 
  my $update_prep = $dbi_connection->prepare($update) or die "failed to prepare";
  my $incoming_update = $update_prep->execute() or die "failed to execute";
  
  $update = "UPDATE $USEDBNAME.checks
    SET R_PENDRECV = 'P',
      R_PostedBy = null,
      R_PostedByUser = null,
      R_PostedByDate = null,
	  R_CheckReceived_Date = null,
      R_Comments = CONCAT(IFNULL(R_Comments,''), ' Unreconciliation for $cid processed automatically at ', NOW())
      WHERE check_id = $cid;";
  
  $update_prep = $dbi_connection->prepare($update);
  my $check_update = $update_prep->execute();
  
  $update = "UPDATE $USEDBNAME.$remits_prod
    SET r_tcode = NULL,
    r_reconciled_date = '0000-00-00',
    R_Comments = CONCAT(IFNULL(R_Comments,''), ' Unreconciliation for $cid processed automatically at ', NOW())
    WHERE check_id = $cid
    AND rec_claim_id IS NULL;";
  my $update_prep = $dbi_connection->prepare("$update");
  my $update_found2 = $update_prep->execute();
  
  $update = "UPDATE $USEDBNAME.$remits_prod
    SET r_tcode = NULL,
    r_reconciled_date ='0000-00-00',
    rec_claim_id = null,
    R_Comments = CONCAT(IFNULL(R_Comments,''), ' Unreconciliation for $cid processed automatically at ', NOW())
    WHERE check_id = $cid
    AND rec_claim_id IS NOT NULL;";
  
  $update_prep = $dbi_connection->prepare("$update");
  my $update_found1 = $update_prep->execute();

  print "Remit Found (rec): $insert_with_rec<br>
  Delete Found (rec): $delete_with_rec<br>
  Remit Found (no rec): $insert_wo_rec<br>
  Delete Found (no rec): $delete_wo_rec<br>
  Incoming Found:$insert_found_inc<br>
  Delete Found: $delete_found_inc<br>
  Incoming Update: $incoming_update<br>
  Check Update: $check_update<br>
  Updates Found (rec): $update_found1<br>
  Updates Found (no rec): $update_found2<br>" if $testing;

  my @errors;
  
  if ($insert_with_rec != $delete_with_rec) {
    push(@errors, 'Remits number of inserts doesn\'t match deletes.');
  }
  if ($insert_found_inc != $delete_found_inc) {
    push(@errors, 'Incoming number of inserts doesn\'t match deletes.');
  }
  if ($insert_found_inc != $insert_with_rec) {
    push (@errors, "Remit count doesn\'t match incoming count. RMTCNT:$insert_with_rec-INCCNT:$insert_found_inc");
  }
  if ($check_update > 1) {
    push (@errors, 'Duplicate check IDs found.');
  }
  if (@errors) {
    my $error_msg = join(' ', @errors);
    print "ROLLBACK";
    my $rollback = qq~ROLLBACK;~;
    $sthCOMMIT  = $dbi_connection->prepare("$rollback");
    $sthCOMMIT->execute() or die "Can not rollback";
    print qq~
    <div class="error-msg">
      <i class="fa fa-times-circle"></i>
      $cid could not be unreconciled! $error_msg Please contact PAI IT for further assistance.
    </div>~;
    return 0;
  } else {
    print "COMMITTING" if $testing;
    my $commit = "COMMIT;";
    $sthCOMMIT  = $dbi_connection->prepare("$commit");
    $sthCOMMIT->execute() or die "Can not commit";
    print qq~<div class="success-msg">
      <i class="fa fa-check"></i>
      $cid successfully reconciled.
    </div>~;
    return 1;
  }
}

# Removes check
sub remove {
  my $cid = shift;

  my $insert = qq ~
    INSERT INTO $USEDBNAME.checks_archive
    SELECT *
    FROM $USEDBNAME.checks
    WHERE check_id IN ($cid)
    AND R_PENDRECV IN ('P', 'M');
  ~;
  my $delete = qq ~
    DELETE FROM $USEDBNAME.checks
    WHERE check_id IN ($cid)
    AND R_PENDRECV IN ('P', 'M');
  ~;

  print "TESTING QUERY: $insert\n$delete\n" if $testing;

  compare_rows($insert, $delete);
}

sub compare_rows {
  # return 1 if $testing;
  print "Comparing rows\n" if $testing;
  my ($insert, $delete) = @_;
  
  my $sqlST = qq#START TRANSACTION#;
  my $sthSTART  = $dbi_connection->prepare($sqlST) or die "Can't prepare\n";
  $rowsfound = $sthSTART->execute or die "Can't execute\n";
  $sthINSERT  = $dbi_connection->prepare("$insert") or die $dbi_connection->errstr;
  $rowsfoundInsert = $sthINSERT->execute or die "Can't execute";
  print "Rows Inserted: $rowsfoundInsert\n" if $testing;

  if ( $rowsfoundInsert > 0 ) {

     $sthDELETE  = $dbi_connection->prepare("$delete");
     $rowsfoundDelete = $sthDELETE->execute;
     print "Rows Deleted: $rowsfoundDelete\n" if $testing;
  

    if ($rowsfoundInsert == $rowsfoundDelete) {
      $commit  = qq#COMMIT; #;
      $sthCOMMIT  = $dbi_connection->prepare("$commit");
      $rowsfound = $sthCOMMIT->execute || die "Can not execute";
      print "COMMIT!!!!!!!!!!!\n" if $testing;
      print qq~<div class="success-msg">
        <i class="fa fa-check"></i>
        $cid successfully removed.
      </div>~;
    } else {
      $sql  = qq~ROLLBACK;~;
      $sthCOMMIT  = $dbi_connection->prepare("$sql");
      $rowsfound = $sthCOMMIT->execute || die "Can not rollback";
      print "\nROLLBACK!!!!!!!!!!!\n\n" if $testing;
      print qq~<div class="error-msg">
        <i class="fa fa-times-circle"></i>
        $cid could not be removed!
      </div>~;
    }
    $sthSTART->finish;
    $sthINSERT->finish;
    $sthDELETE->finish;
    $sthCOMMIT->finish;
  }
}

#______________________________________________________________________________
#______________________________________________________________________________
