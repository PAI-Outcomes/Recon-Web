use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

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

if ( $USER ) {
  if ( $in{'no_menu'} == 1 ) {
    print "Content-type: text/html\n\n";

    print qq#<!doctype html> 
                   <html lang="en">
                     <head>
                       <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
 
                       <TITLE>Archive</TITLE>

                       <link rel="stylesheet" href="/css/reconrx_style.css?ver=20160731" />

                       <script src="https://code.jquery.com/jquery-1.11.1.min.js"></script>

                     </head>
  
                     <body><div style='margin-left: 100px; margin-top: 50px'>#;
  }
  else {
    &MyReconRxHeader;
    &ReconRxHeaderBlock;
  }
} else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  exit(0);
}

&hasAccess($USER);

if ( $ReconRx_Admin_Archive !~ /^Yes/i ) {
  print qq#<p class="yellow"><font size=+1><strong>\n#;
  print qq#$prog<br><br>\n#;
  print qq#<i>You do not have access to this page.</i>\n#;
  print qq#</strong></font>\n#;
  print qq#</p><br>\n#;
  # print qq#<a href="Login.cgi">Log In</a><P>\n#;
  print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

  &trailer;

  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$adate  = sprintf("%04d-%02d-%02d", $year, $month, $day);

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

# Start page operations
&displayOptions;
  
if ( $in{submit} =~ /^Search/i ) {
  &displayResults();
}
elsif ( $in{submit} =~ /Save/i ) {
  &updateRecords();
  if ( $in{'no_menu'} == 1 ) {
    print "<script>window.opener.location.reload(true); window.close();</script></html>\n";
    exit;
  }
}

if ( $in{'no_menu'} == 1 ) {
  print "</div>\n";
}

# Close the Database
$dbx->disconnect;

&MyReconRxTrailer;

exit(0);
 
sub displayOptions {
  print "<hr>\n";

  print qq#<style> \n#;
  print qq#td { border-top: none; }\n#;
  print qq#</style> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq# function clearSearch(frm) { \n#;
  print qq#     tags = frm.getElementsByTagName('input'); \n#;
  print qq#     for(i = 0; i < tags.length; i++) { \n#;
  print qq#         if ( tags[i].type == 'text' ) { \n#;
  print qq#             tags[i].value = ''; \n#;
  print qq#         } \n#;
  print qq#     } \n#;
  print qq#     tags = frm.getElementsByTagName('select'); \n#;
  print qq#     for(i = 0; i < tags.length; i++) { \n#;
  print qq#         tags[i].selectedIndex = 0; \n#;
  print qq#     } \n#;
  print qq# } \n#;
  print qq#</script> \n#;

  print qq#<form id="selectForm" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<INPUT TYPE="hidden" NAME="no_menu" VALUE="$in{'no_menu'}">\n#;
  print "<table>\n";
  # print qq#<tr><th colspan=2 align="center">Search</th></tr>#;

  print qq#<tr><td><label for="NCPDPNumber">Pharmacy:</label></td>#;
  print qq#<td><input type="text" name="NCPDPNumber" list="plist" id="NCPDP" value="$in{NCPDPNumber}" style="width:300px;">\n#;
  print qq#<datalist id="plist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
               FROM officedb.pharmacy 
              WHERE Status_ReconRx = 'Active'
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM officedb.pharmacy_coo
              WHERE Status_ReconRx = 'Active'
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($PH_ID, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    print qq#<option value="$NCPDP - $Pharmacy_Name"> </option>\n#;
  }

  $sthx->finish;
  print qq# </datalist></td></tr>#;


  print qq#<tr><td>Date Of Service:</td><td><INPUT TYPE="text" NAME="DateOfService" PLACEHOLDER="YYYYMMDD" SIZE=10 VALUE="$in{DateOfService}"></td></tr>\n#;
  
  print qq#<tr><td>Rx Number:</td><td><INPUT TYPE="text" NAME="RxNumber" SIZE=25 VALUE="$in{RxNumber}"></td></tr>\n#;

  print qq#<tr><td>Amount Paid:</td><td><INPUT TYPE="text" NAME="TotalAmountPaid" SIZE="10" VALUE="$in{TotalAmountPaid}"></td></tr>\n#;

  print qq#<td><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Search"><INPUT style="padding:5px; margin:5px" TYPE="button" NAME="Clear" VALUE="Clear" onclick="clearSearch(this.form);"></td><td>$nbsp</td></tr>\n#;

  print qq#</table>\n#;

  print qq#</form>\n#;

  print qq#<br /><hr />\n#;
}

sub displayResults {
  my $incwhere, $remitwhere;

  foreach $key (sort keys %in) {
    next if ($key =~ /submit/);

    $field = 'db' . $key;

    if ( $key =~ /NCPDPNumber/i ) {
      $incwhere   .= "&& $field = '" . substr($in{$key},0,7) . "' ";
      $remitwhere .= "&& clm.R_TS3_NCPDP = '" . substr($in{$key},0,7) . "' ";
    }
    elsif ( $key =~ /DateOfService/i && $in{$key} ne '' ) {
      $incwhere .= "&& $field = '$in{$key}' ";
    }
    elsif ( $key =~ /RxNumber/i && $in{$key} ne '') {
      $in{$key} =~ s/\s+//g;
      @rxnums = split(/\,/, $in{$key});

      foreach $rx (@rxnums) {
        $rxnums .= "'$rx',"
      }
      chop($rxnums);

      $incwhere   .= "&& $field IN ($rxnums) ";
      $remitwhere .= "&& clm.R_CLP01_Rx_Number IN ($rxnums) ";
    }
    elsif ( $key =~ /TotalAmountPaid/i && $in{$key} ne '') {
      $incwhere   .= "&& $field = '$in{$key}' ";
      $remitwhere .= "clm.&& R_CLP04_Amount_Payed = '$in{$key}' ";
    }
  }
  $remitwhere .= "&& chk.R_PENDRECV = 'R'";

  # print "$incwhere<br>";

  print qq#<form name="frm2" id="frm2" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<INPUT TYPE="hidden" NAME="incoming_id" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="remit_id" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="NCPDPNumber" VALUE="$in{'NCPDPNumber'}">\n#;
  print qq#<INPUT TYPE="hidden" NAME="incoming_comment" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="remit_comment" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="no_menu" VALUE="$in{'no_menu'}">\n#;

  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq# \$(document).ready(function() { \n#;
  print qq#     \$('\#tablef, \#tableg').DataTable({ \n#;
  print qq#         "sDom": 'T<"clear">lrtip',\n#;
  print qq#         "sScrollX": "100%", \n#;
  print qq#         "bScrollCollapse": true,  \n#;
  print qq#         "sScrollY": "350px", \n#;
  print qq#         "bPaginate": false, \n#;
  print qq#         "searching": false, \n#;
  print qq#         "aaSorting": [[ 1, 'asc' ]], \n#;
  print qq#         "aoColumnDefs": [ \n#;
  print qq#             { "bSortable": false, "aTargets": [ 0 ] } \n#;
  print qq#         ] \n#;   
  print qq#     }); \n#;
  print qq# }); \n#;
  print qq# function checkAll(ele) { \n#;
  print qq#     var remit_checkboxes = document.getElementsByName('remit_ids'); \n#;
  print qq#     var incoming_checkboxes = document.getElementsByName('incoming_ids'); \n#;
  print qq#     if (ele.checked) { \n#;
  print qq#         if (ele.name == 'remit_selectall') { \n#;
  print qq#             for (var i = 0; i < remit_checkboxes.length; i++) { \n#;
  print qq#                 if (remit_checkboxes[i].type == 'checkbox') { \n#;
  print qq#                     remit_checkboxes[i].checked = true; \n#;
  print qq#                 } \n#;
  print qq#             } \n#;
  print qq#         } else { \n#;
  print qq#             for (var i = 0; i < incoming_checkboxes.length; i++) { \n#;
  print qq#                 if (incoming_checkboxes[i].type == 'checkbox') { \n#;
  print qq#                     incoming_checkboxes[i].checked = true; \n#;
  print qq#                 } \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#     } else { \n#;
  print qq#         if (ele.name == 'remit_selectall') { \n#;
  print qq#             for (var  i = 0; i < remit_checkboxes.length; i++) { \n#;
  print qq#                 if (remit_checkboxes[i].type == 'checkbox') { \n#;
  print qq#                     remit_checkboxes[i].checked = false; \n#;
  print qq#                 } \n#;
  print qq#             } \n#;
  print qq#         } else { \n#;
  print qq#             for (var  i = 0; i < incoming_checkboxes.length; i++) { \n#;
  print qq#                 if (incoming_checkboxes[i].type == 'checkbox') { \n#;
  print qq#                     incoming_checkboxes[i].checked = false; \n#;
  print qq#                 } \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#     } \n#;
  print qq# } \n#;
  print qq# function setSelected(form) { \n#;
  print qq#     var incoming_ids = ''; \n#;
  print qq#     var remit_ids = ''; \n#;
  print qq#     var inc_comment = ''; \n#;
  print qq#     var remit_comment = ''; \n#;
  print qq#     for (var i = 0; i < form.elements.length; i++ ) { \n#;
  print qq#         if (form.elements[i].type == 'checkbox' && form.elements[i].name == 'incoming_ids') { \n#;
  print qq#             if (form.elements[i].checked == true) { \n#;
  print qq#                 incoming_ids += form.elements[i].value + ','; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#         if (form.elements[i].type == 'checkbox' && form.elements[i].name == 'remit_ids') { \n#;
  print qq#             if (form.elements[i].checked == true) { \n#;
  print qq#                 remit_ids += form.elements[i].value + ','; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#         if (form.elements[i].name == 'inc_cmt') { \n#;
  print qq#             inc_comment = form.elements[i].value; \n#;
  print qq#         } \n#;
  print qq#         if (form.elements[i].name == 'remit_cmt') { \n#;
  print qq#             remit_comment = form.elements[i].value; \n#;
  print qq#         } \n#;
  print qq#     } \n#;
  print qq#     incoming_ids = incoming_ids.substring(0, incoming_ids.length - 1); \n#;
  print qq#     remit_ids = remit_ids.substring(0, remit_ids.length - 1); \n#;
  print qq#     if ( \$("\#archive_type").val() != '' && remit_ids == '') {  \n#;
  print qq#         if (incoming_ids == '') { \n#;
  print qq#             alert('No Incoming Records Selected'); \n#;
  print qq#             return false; \n#;
  print qq#         } \n#;
  print qq#     } else { \n#;
  print qq#         if (incoming_ids == '' || remit_ids == '') { \n#;
  print qq#             alert('Please Select a Remit AND Claim to Continue'); \n#;
  print qq#             return false; \n#;
  print qq#         } \n#;
  print qq#     } \n#;
  print qq#     form.incoming_id.value = incoming_ids;\n#;
  print qq#     form.remit_id.value = remit_ids;\n#;
  print qq#     form.incoming_comment.value = inc_comment;\n#;
  print qq#     form.remit_comment.value = remit_comment;\n#;
  print qq# } \n#;
  print qq#</script> \n#;

  # tableg
  print qq#<h3>835 Remits</h3>\n#;
  print qq#<table id="tableg">\n#;
  print qq#<thead>\n#;
  print qq#<tr><th><!--<INPUT name=\"remit_selectall\" type=\"checkbox\" onchange=\"checkAll(this)\" name=\"remit_ids[]\" />--></th><th>Rx \#</th><th>NCPDP</th><th>CS</th><th>DOS</th><th>TPP</th><th>P/R</th><th>P/R Date</th><th>Paid</th><th>Chk \#</th><th>Chk Date</th><th>Chk Amt</th><th>Rec. Date</th></tr>\n#;
  print qq#</thead>\n#;
  
  my $sql = "SELECT clm.835remitstbID, 
                    clm.R_CLP01_Rx_Number, 
                    clm.R_TS3_NCPDP, 
                    clm.R_CLP02_Claim_Status_Code, 
                    clm.R_DTM02_Date, 
                    chk.R_TPP, 
                    chk.R_PENDRECV, 
                    chk.R_CheckReceived_Date, 
                    clm.R_CLP04_Amount_Payed, 
                    chk.R_TRN02_Check_Number, 
                    chk.R_BPR16_Date, 
                    chk.R_BPR02_Check_Amount, 
                    clm.R_Reconciled_Date,
                    clm.R_Comments
               FROM $DBNAME.Checks chk
               JOIN $DBNAME.835remitstb clm ON (chk.Check_ID = clm.Check_ID)
              WHERE 1=1 
             $remitwhere";
 
  # print "sql: $sql\n";
  my $sthr  = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($id, $rxnum, $ncpdp, $cs, $dos, $tpp, $pendrec, $prdate, $tap, $checknum, $checkdate, $checkamt, $recdate, $comments) = $sthr->fetchrow_array() ) {
    print "<tr><td><input type='checkbox' name='remit_ids' value=$id><input type='hidden' name='remit_cmt' value='$comments'></td><td>$rxnum</td><td>$ncpdp</td><td>$cs</td><td>$dos</td><td>$tpp</td><td>$pendrec</td><td>$prdate</td><td>$tap</td><td>$checknum</td><td>$checkdate</td><td>$checkamt</td><td>$recdate</td></tr>\n";
  }

  $sthr->finish;  

  print "</tbody>";
  print "</table><br><br><br>\n";

  print qq#<strong>Archive Type:</strong> #;
  print qq#<select id="archive_type" name="archive_type">\n#;
  print qq#<option value="">Select Type of Archive</option>\n#;
  
  my $DBNAME = "reconrxdb";
  my $TABLE  = "tcodedefs";

  my $sql = "SELECT TCode, Meaning
               FROM $DBNAME.$TABLE
              WHERE Association NOT IN ('Remit Data','Cleanup - Automated')
           ORDER BY Meaning";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  my $selected;

  while ( my ($code, $meaning) = $sthx->fetchrow_array() ) {
    print qq#<option value="$code">$code - $meaning</option>\n#;
  }

  $sthx->finish;
  print qq#</select><br><br>#;

  # tablef
  print qq#<h3>Incoming Aging</h3>\n#;
  print qq#<table id="tablef">\n#;
  print "<thead>\n";
  print "<tr><th><!--<INPUT name=\"incoming_selectall\" type=\"checkbox\" onchange=\"checkAll(this)\" name=\"incoming_ids[]\" />--></th><th>Rx #</th><th>NCPDP</th><th>RC</th><th>DB Code</th><th>DB TCode</th><th>Paid</th><th>BIN</th><th>DOS</th><th>Date Trans</th><th>Rec. Date</th></tr>\n";
  print "</thead>\n";
  print "<tbody>\n";

  my $DBNAME = "reconrxdb";

  my $sql = "SELECT incomingtbID, 
                    dbNCPDPNumber, 
                    dbBinNumber, 
                    dbDateOfService, 
                    dbRxNumber, 
                    dbTotalAmountPaid, 
                    dbResponseCode, 
                    dbCode, 
                    dbTCode, 
                    dbDateTransmitted, 
                    dbReconciledDate,
                    dbComments
               FROM $DBNAME.Incomingtb
              WHERE 1=1 
             $incwhere";
 
  # print "sql: $sql\n";
  my $sthr  = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($id, $ncpdp, $bin, $dos, $rxnum, $tap, $rc, $dbc, $dbtc, $dtrans, $recdate, $comments) = $sthr->fetchrow_array() ) {
    print "<tr><td><input type='checkbox' name='incoming_ids' value=$id><input type='hidden' name='inc_cmt' value='$comments'></td><td>$rxnum</td><td>$ncpdp</td><td>$rc</td><td>$dbc</td><td>$dbtc</td><td>$tap</td><td>$bin</td><td>$dos</td><td>$dtrans</td><td>$recdate</td></tr>\n";
  }

  $sthr->finish;  

  print "</tbody>";
  print "</table><br><br>\n";

  # save button
  print qq#<INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Save" onclick="return setSelected(document.frm2)">\n#;
  print "</form>\n";
}  

sub updateRecords {
  ### Archive Incoming Aging Data ###

  my $inc_sel_ids  = $in{'incoming_id'};
  my $inc_comment  = $in{'incoming_comment'};
  my $archive_type = $in{'archive_type'};
  my $base_comment = "Archived By IT on $adate by $USER";
  $comment         = ($inc_comment && $inc_comment !~ /$base_comment/) 
                        ? "$inc_comment || $base_comment" 
                        : ($inc_comment) ? $inc_comment : $base_comment;

  $archive_type = 'PD' if ( !$archive_type );

  $sql = "START TRANSACTION";
  $sth = $dbx->prepare("$sql");
  $sth->execute;
  ($rowsfound) = $sth->rows;

  $DBNAME     = "reconrxdb";
  $FROM_TABLE = "incomingtb";
  $TO_TABLE   = "incomingtb_archive";

  $sql = "UPDATE $DBNAME.$FROM_TABLE
             SET dbReconciledDate = '$adate',
                 dbCode = '$archive_type',
                 dbTCode = '$archive_type',
                 dbComments = '$comment'
           WHERE incomingtbID IN ($inc_sel_ids)";
  #print "Incoming Update SQL: $sql<br>";

  $sth = $dbx->prepare("$sql");
  $sth->execute;
  $inc_updated = $sth->rows;

  $sql = "INSERT INTO $DBNAME.$TO_TABLE
            (SELECT *
               FROM $DBNAME.$FROM_TABLE
              WHERE incomingtbID IN ($inc_sel_ids))";
  #print "Incoming Insert SQL: $sql<br>";

  $sth = $dbx->prepare("$sql");
  $sth->execute;
  $inc_inserted = $sth->rows;

  $sql = "DELETE
            FROM $DBNAME.$FROM_TABLE
           WHERE incomingtbID IN ($inc_sel_ids)";
  #print "Incoming Delete SQL: $sql<br>";

  $sth = $dbx->prepare("$sql");
  $sth->execute;
  $inc_deleted = $sth->rows;

  if ( $inc_updated != $inc_inserted || $inc_inserted != $inc_deleted) {
    $sql  = 'ROLLBACK;';
    $sth = $dbx->prepare("$sql");
    $sth->execute;
    ($rowsfoundROLLBACK) = $sth->rows;
    print "<span style='color: red;'>Incoming Aging Archive Failed!</span><br>";
    return;
  } else {
    $sql = 'COMMIT;';
    $sth = $dbx->prepare("$sql");
    $sth->execute;
    ($rowsfound) = $sth->rows;
    print "<span style='color: green;'>Succesfully Archived ($inc_inserted) Incoming Aging Records!</span><br>";
  }

  ### Archive/Reconcile 835 Data ###
  
  if ( $in{'remit_id'} ) {
    my $remit_sel_ids = $in{'remit_id'};
    my $remit_comment = $in{'remit_comment'};
    $comment          = ($remit_comment && $remit_comment !~ /$base_comment/) 
                          ? "$remit_comment || $base_comment" 
                          : ($remit_comment) ? $remit_comment : $base_comment;

    $DBNAME     = "reconrxdb";
    $FROM_TABLE = "835remitstb";
    $TO_TABLE   = "835remitstb_archive";

    $sql = "UPDATE $DBNAME.$FROM_TABLE
               SET R_Reconciled_Date = '$adate',
                   R_TCode = 'PD',
                   R_Comments = '$comment'
             WHERE 835remitstbID IN ($remit_sel_ids)";
    # print "835 Remits Update SQL: $sql<br>";

    $sth = $dbx->prepare("$sql");
    $sth->execute;
    $remit_updated = $sth->rows;

    $sql = "INSERT INTO $DBNAME.$TO_TABLE
              (SELECT *
                 FROM $DBNAME.$FROM_TABLE
                WHERE 835remitstbID IN ($remit_sel_ids))";
    # print "835 Remits Insert SQL: $sql<br>";

    $sth = $dbx->prepare("$sql");
    $sth->execute;
    $remit_inserted = $sth->rows;

    $sql = "DELETE
              FROM $DBNAME.$FROM_TABLE
             WHERE 835remitstbID IN ($remit_sel_ids)";
    # print "835 Remits Delete SQL: $sql<br>";

    $sth = $dbx->prepare("$sql");
    $sth->execute;
    $remit_deleted = $sth->rows;

    if ( $remit_updated != $remit_inserted || $remit_inserted != $remit_deleted) {
      $sql = 'ROLLBACK;';
      $sth = $dbx->prepare("$sql");
      $sth->execute;
      ($rowsfoundROLLBACK) = $sth->rows;
      print "<span style='color: red;'>835 Remits Archive Failed!</span><br>";
    } else {
      $sql = 'COMMIT;';
      $sth = $dbx->prepare("$sql");
      $sth->execute;
      ($rowsfound) = $sth->rows;
      print "<span style='color: green;'>Succesfully Reconciled and Archived ($remit_inserted) 835 Remit Records!</span><br>";
    }
  }
}
