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

if ( $ReconRx_Admin_Archive !~ /^Yes/i ) {
   print qq#<p class="yellow"><font size=+1><strong>\n#;
   print qq#$prog<br><br>\n#;
   print qq#<i>You do not have access to this page.</i>\n#;
   print qq#</strong></font>\n#;
   print qq#</p><br>\n#;
#  print qq#<a href="Login.cgi">Log In</a><P>\n#;
   print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

   &trailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

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

#Start page operations

&displayOptions;
  
if ( $in{submit} =~ /^Search/i ) {
  &displayResults();
}
elsif ( $in{submit} =~ /Save/i ) {
  &updateRecords();
}

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
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
  print "<table>\n";
#  print qq#<tr><th colspan=2 align="center">Search</th></tr>#;

  print qq#<tr><td><label for="NCPDPNumber">Pharmacy:</label></td>#;
  print qq#<td><input type="text" name="NCPDPNumber" list="plist" id="NCPDP" value="$in{NCPDPNumber}" style="width:300px;">\n#;
  print qq#<datalist id="plist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
               FROM officedb.pharmacy 
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active' OR Status_ReconRx = 'Transition' OR Status_ReconRx_Clinic = 'Transition')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM officedb.pharmacy_coo
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active' OR Status_ReconRx = 'Transition' OR Status_ReconRx_Clinic = 'Transition')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($PH_ID, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    print qq#<option value="$NCPDP - $Pharmacy_Name"> </option>\n#;
  }

  $sthx->finish;
  print qq# </datalist></td></tr>#;


  print qq#<tr><td><label for="BinNumber">Third Party Payer:</label></td>#;
  print qq#<td><input type="text" name="BINParent" list="blist" id="bin" value="$in{BINParent}" style="width:300px;">\n#;
  print qq#<datalist id="blist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "third_party_payers";

  my $sql = "SELECT Third_Party_Payer_ID, BIN, Third_Party_Payer_Name  
               FROM $DBNAME.$TABLE 
              WHERE Status = 'Active'
                 && Primary_Secondary = 'Pri'
                 && BIN NOT LIKE '99999%' 
                 && BIN != '000000' 
           ORDER BY Third_Party_Payer_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($TPP_ID, $TPP_BIN, $TPP_NAME) = $sthx->fetchrow_array() ) {
    print qq#<option value="$TPP_BIN - $TPP_NAME"> </option>\n#;
  }

  $sthx->finish;
  print qq# </datalist></td></tr>#;

  print qq#<tr><td>Date Of Service:</td><td><INPUT TYPE="text" NAME="begDateOfService" PLACEHOLDER="YYYYMMDD" SIZE=10 VALUE="$in{begDateOfService}"> &nbsp-&nbsp <INPUT TYPE="text" NAME="endDateOfService" PLACEHOLDER="YYYYMMDD" SIZE=10 VALUE="$in{endDateOfService}"></td></tr>\n#;
  
  print qq#<tr><td>Rx Numbers:</td><td><INPUT TYPE="text" NAME="RxNumber" SIZE=75 VALUE="$in{RxNumber}"></td></tr>\n#;

  print qq#<tr><td>PCN:</td><td><INPUT TYPE="text" NAME="ProcessorControlNumber" SIZE=20 VALUE="$in{ProcessorControlNumber}"></td></tr>\n#;

  print qq#<td><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Search"><INPUT style="padding:5px; margin:5px" TYPE="button" NAME="Clear" VALUE="Clear" onclick="clearSearch(this.form);"></td><td>$nbsp</td></tr>\n#;

  print qq#</table>\n#;

  print qq#</form>\n#;

  print qq#<br /><hr />\n#;
}

#______________________________________________________________________________

sub updateRecords {
  my $sel_ids = $in{'incoming_id'};
  my $archive_type = $in{'archive_type'};
  my $comment = "Archived By IT on $adate by $USER";

  $sql = "START TRANSACTION";
  ($rowsfound) = &jdo_sql($sql);

  my $DBNAME     = "reconrxdb";
  my $FROM_TABLE = "incomingtb";
  my $TO_TABLE   = "incomingtb_archive";

  $sql = "UPDATE $DBNAME.$FROM_TABLE
             SET dbTCode = '$archive_type',
                 dbComments = '$comment'
           WHERE incomingtbID IN ($sel_ids)";
#  print "SQL: $sql<br>";

  $sth = $dbx->prepare("$sql");
  $sth->execute;
  $updated = $sth->rows;

  $sql = "INSERT INTO $DBNAME.$TO_TABLE
            (SELECT *
               FROM $DBNAME.$FROM_TABLE
              WHERE incomingtbID IN ($sel_ids))";
#  print "SQL: $sql<br>";

  $sth = $dbx->prepare("$sql");
  $sth->execute;
  $inserted = $sth->rows;

  $sql = "DELETE
            FROM $DBNAME.$FROM_TABLE
           WHERE incomingtbID IN ($sel_ids)";
#  print "SQL: $sql<br>";

  $sth = $dbx->prepare("$sql");
  $sth->execute;
  $deleted = $sth->rows;

  if ( $updated != $inserted || $inserted != $deleted ) {
    $sql  = 'ROLLBACK ';
    ($rowsfoundROLLBACK) = &jdo_sql($sql);
    print "<span style='color: red;'>Archive Failed!</span><br>";
  } else {
    $sql  = 'COMMIT; ';
    ($rowsfound) = &ReconRx_jdo_sql($sql);
    print "<span style='color: green;'>Succesfully Archived ($inserted) Records!</span><br>";
  }
}

#______________________________________________________________________________

sub displayResults {
  my $where;

  foreach $key (sort keys %in) {
    next if ($key =~ /submit/);

    if ( $key =~ /DateOfService/ ) {
      $field = 'db' . substr($key,3);
    } else {
      $field = 'db' . $key;
    }

    if ( $key =~ /NCPDPNumber/i ) {
      $where .= "&& $field = '" . substr($in{$key},0,7) . "' ";
    }
    elsif ( $key =~ /BINParent/i && $in{$key} ne '') {
      $where .= "&& $field = '" . substr($in{$key},0,6) . "' ";
    }
    elsif ( $key =~ /DateOfService/i && $in{$key} ne '' ) {
      if ( $key =~ /beg/i ) {
        $where .= "&& $field >= '$in{$key}' ";
      } else {
        $where .= "&& $field <= '$in{$key}' ";
      }
    }
    elsif ( $key =~ /RxNumber/i && $in{$key} ne '') {
     if ($in{$key} !~ /\,/) {
      @rxnums = split(' ', $in{$key});
     }
     else {
      $in{$key} =~ s/\s+//g;
      @rxnums = split(/\,/, $in{$key});
     }

      foreach $rx (@rxnums) {
        $rxnums .= "'$rx',"
      }
      chop($rxnums);

      $where .= "&& $field IN ($rxnums) ";
    }
    elsif ( $in{$key} ne '') {
      $where .= "&& $field = '$in{$key}' ";
    }
  }

#  print "$where<br>";

  print qq#<form name="frm2" id="frm2" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<INPUT TYPE="hidden" NAME="incoming_id" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="NCPDPNumber" VALUE="$in{'NCPDPNumber'}">\n#;
  print qq#<strong>Archive Type:</strong> #;
  print qq#<select id="archive_type" name="archive_type">\n#;
  print qq#<option value="">Select Type of Archive</option>\n#;
  
  my $DBNAME = "reconrxdb";
  my $TABLE  = "tcodedefs";

  my $sql = "SELECT *
               FROM $DBNAME.$TABLE
              WHERE Association NOT IN ('Remit Data','Cleanup - Automated')
           ORDER BY Meaning";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  my $selected;

  while ( my ($code, $meaning, $ass) = $sthx->fetchrow_array() ) {
    print qq#<option value="$code">$code - $meaning</option>\n#;
  }

  $sthx->finish;
  print qq#</select><br><br>#;
 
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq#\$(document).ready(function() { \n#;
  print qq#                \$('\#tablef').dataTable( { \n#;
  print qq#                                "sScrollX": "100%", \n#;
  print qq#                                "bScrollCollapse": true,  \n#;
  print qq#                                "sScrollY": "350px", \n#;
  print qq#                                "bPaginate": false, \n#;
  print qq#                                "searching": false \n#;
#  print qq#                                "columnDefs": [ { \n#;
#  print qq#                                   orderable: false, \n#;
#  print qq#                                   targets:   0 \n#;
#  print qq#                                 } ], \n#;
  print qq#                } ); \n#;
#  print qq#                \$(".dataTables_filter").hide(); \n#;
  print qq#} ); \n#;
  print qq# function checkAll(ele) { \n#;
  print qq#     var checkboxes = document.getElementsByTagName('input'); \n#;
  print qq#     if (ele.checked) { \n#;
  print qq#         for (var i = 0; i < checkboxes.length; i++) { \n#;
  print qq#             if (checkboxes[i].type == 'checkbox') { \n#;
  print qq#                 checkboxes[i].checked = true; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#     } else { \n#;
  print qq#         for (var  i = 0; i < checkboxes.length; i++) { \n#;
  print qq#             if (checkboxes[i].type == 'checkbox') { \n#;
  print qq#                 checkboxes[i].checked = false; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#     } \n#;
  print qq# } \n#;
  print qq# function setSelected(form) { \n#;
  print qq#     var ids = ''; \n#;
  print qq#     if ( \$("\#archive_type").val() != '' ) {  \n#;
  print qq#       for (var i = 0; i < form.elements.length; i++ ) { \n#;
  print qq#         if (form.elements[i].type == 'checkbox' && form.elements[i].name == 'ids') { \n#;
  print qq#             if (form.elements[i].checked == true) { \n#;
  print qq#                 ids += form.elements[i].value + ','; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#       } \n#;
  print qq#     } else { \n#;
  print qq#       alert('Archive Type Not Selected'); \n#;
  print qq#       return false; \n#;
  print qq#     } \n#;
  print qq#     ids = ids.substring(0, ids.length - 1); \n#;
  print qq#     if (ids == '') { \n#;
  print qq#       alert('No Records Selected'); \n#;
  print qq#       return false; \n#;
  print qq#     } \n#;
  print qq#     form.incoming_id.value = ids\n#;
  print qq# } \n#;
  print qq#</script> \n#;

  print qq#<table id="tablef">\n#;
  print "<thead>\n";
  print "<tr><th><INPUT name=\"selectall\" type=\"checkbox\" onchange=\"checkAll(this)\" name=\"ids[]\" /></th><th>Rx Number</th><th>Date of Service</th><th>BIN</th><th>PCN</th><th>NDC</th><th>Amt Paid</th><th>Amt Paid Rem</th><th>NCPDP</th></tr>\n";
  print "</thead>\n";
  print "<tbody>\n";


  my $DBNAME = "reconrxdb";

  my $sql = "SELECT incomingtbID, dbNCPDPNumber, dbBinNumber, dbProcessorControlNumber, dbDateOfService, dbRxNumber, dbNDC, dbTotalAmountPaid, dbTotalAmountPaid_Remaining
               FROM $DBNAME.Incomingtb
              WHERE 1=1 
             $where
              LIMIT 5000";
 
  my $sthr  = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($id, $ncpdp, $bin, $pcn, $dos, $rxnum, $ndc, $tap, $tapr) = $sthr->fetchrow_array() ) {
    print "<tr><td><input type='checkbox' name='ids' value=$id></td><td>$rxnum</td><td>$dos</td><td>$bin</td><td>$pcn</td><td>$ndc</td><td>$tap</td><td>$tapr</td><td>$ncpdp</td></tr>\n";
  }

  $sthr->finish;

  print "</tbody>";
  print "</table><br>\n";
  print qq#<INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Save" onclick="return setSelected(document.frm2)">\n#;
  print "</form>\n";
}  

#______________________________________________________________________________
