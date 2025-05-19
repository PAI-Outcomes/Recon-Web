
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
my $table = 'reconrxdb';

$| = 1; # don't buffer output
#______________________________________________________________________________
#
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$tdate  = sprintf("%04d%02d%02d", $year, $month, $day);
$DATEEX = sprintf("%02d/%02d/%04d", $month, $day, $year);
#______________________________________________________________________________

&readPharmacies(0, $PROGRAM, $inNCPDP);
&readCSRs();

if ( $USER ) {
  $table = 'webinar' if ($PH_ID == 11 && $USER != 66);
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} 
else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

print << "EOL";
<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
<script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
<script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>
<!-- <script src="/includes/validate_req.js" type="text/javascript"></script> -->

<script>
\$(function() {
  \$('.phone').mask('(999) 999-9999');
  \$(".datepicker").mask("99/99/9999");
});

function checkDecision() {
if (confirm("This will Archive ALL claims on this page. Are you sure?")) {
  return true;
}
else {
  return false;
}

}
function checkRequiredFields(form) {
	var elements = form.elements;
	var errors = '';

  	for (var i = 0, element; element = elements[i++];) {
		if (element.type != "submit" && element.type != "hidden") {
			var patt = /required/;
			if ( element.value === "" && patt.test(element.className)) {
				element.style.borderColor = "red";
				errors = 'Please Fill in the Highlighted Areas';
			}
			else {
				element.style.borderColor = "black";
			}
		}
	}

	if ( errors ) {
		document.getElementById("errors").innerHTML = errors;
		return false;
	}
        else {
	        return true;
	}
}

</script>
EOL

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);


  if ( $in{'Submit'} =~ /Save Changes|Archive ALL/i) {
    &process_input();
    &close_interventions();
    &remove_action();
    print qq#<h2 style="color: green">Thank you for updating your information!</h2>\n#;
    exit;
  }

$ntitle = "Verify Claims";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

print qq#<h2>Please update your claim information.</h2>\n#;

&displayWebPage;


$dbx->disconnect;

#______________________________________________________________________________

print '<div style="display: block; padding-top: 600px;color:red;  width: 80%;">';
print qq#<p><b>Disclaimer: Claims that have not received a response code from the pharmacy within 90 days from the date the claims were added to the Action Required tab will be marked as paid.</p></b>\n#;
print qq#</div>\n#;

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return checkRequiredFields(this)\;">\n#;

  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq#\$(document).ready(function() { \n#;
  print qq#                \$('\#tablef').dataTable( { \n#;
  print qq#                                "sScrollX": "100%", \n#;
  print qq#                                "bScrollCollapse": true,  \n#;
  print qq#                                "sScrollY": "335px", \n#;
  print qq#                                "aaSorting": [ [7,'desc'] ], \n#;
  print qq#                                "sDom": "lrtip",\n#;
  print qq#                                "bInfo": false,\n#;
  print qq#                                "bLengthChange": false,\n#;
  print qq#                                "bPaginate": false \n#;
  print qq#                } ); \n#;
  print qq#} ); \n#;
  print qq#</script> \n#;

  print '<div style="position: relative; display: block; float: left; width: 80%;">';

  print "<table id='tablef'><thead><tr><th>NCPDP</th><th>BIN</th><th>PCN</th><th>RX</th><th>DOS</th><th>AMT DUE</th><th>Response Code</th></tr></thead><tbody>";

  $sql = "SELECT a.id, a.incomingtbID, b.dbNCPDPNumber, b.dbBinNumber, b.dbProcessorControlNumber, b.dbRxNumber, b.dbDateOfService, b.dbTotalAmountPaid_Remaining, a.status, a.intervention_id
               FROM $table.incomingtb_review a
               JOIN $table.incomingtb b ON (a.Pharmacy_ID = b.Pharmacy_ID AND a.incomingtbID = b.incomingtbID)
               JOIN $table.cscodes c ON (a.cscode = c.code AND c.display = 'P')
              WHERE a.Pharmacy_ID = $PH_ID
                AND a.status IS NULL
                #AND a.date_sent IS NOT NULL
           ORDER BY b.dbDateOfService";

   ($sqlout = $sql) =~ s/\n/<br>\n/g;
   $sth = $dbx->prepare($sql);
   $sth->execute();

   while ( my ( $id, $incoming_id, $ncpdp, $bin, $pcn, $rxnum, $dos, $amt_paid, $status, $int_id ) = $sth->fetchrow_array()) {
     $dos = substr($dos,4,2) . '/' . substr($dos,6,2) . '/' . substr($dos,0,4);

     print "<tr>
              <td>$ncpdp</td>
              <td>$bin</td>
              <td>$pcn</td>
              <td>$rxnum</td>
              <td>$dos</td>
              <td>$amt_paid</td>
              <td><select name='Status_${id}_${incoming_id}_${int_id}'>
                       <option value=''>-Select-</option>
                       <option value='CUP'>Coupon</option>
                       <option value='DN'>Denied</option>
                       <option value='PDEV'>E-voucher</option>
                       <option value='BR'>Other - Remove from Aging</option>
                       <option value='FRR'>Other - DO NOT Remove from Aging</option>
                       <option value='RVL'>Reversal</option>
                  </select></td>
            </tr>";
   }

   $sth->finish;

   print "</tbody>";

   print "</table></div>";

   print '<div style="position: relative; display: block; float: left; width: 75%;">';
   print qq#<INPUT id="submit" style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Save Changes">\n#;
   if ($USER == 66) {
     print '<div style="position: relative; display: block; float: right; width: 75%;">';
       print qq#<INPUT id="submit" style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Archive ALL" onClick="return checkDecision()" >\n#;
     print "</div>";
   }
   print "</table></div>";
   print "</FORM>";
}

#______________________________________________________________________________

sub process_input {
  $comment = "Verify Claims Archived:$in{'Submit'}:$tdate:$USER";
  foreach $key (sort keys %in) {
    next if ( $key !~ /_/i || ($in{$key} eq '' && $in{'Submit'} =~ /Save Changes/i));

    ($field, $id, $incoming_id, $intervention_id)  = split('_', $key);
    my $tmp01 = "$in{$key}";
    my $tmp02 = "'$in{$key}'";

    if ($in{'Submit'} =~ /Archive ALL/i) {
      $tmp01 = 'BR';
      $tmp02 = dbCode;
    }

    ## Update Queue Table
    $sql = "UPDATE $table.incomingtb_review
               SET status = '$tmp01'
             WHERE id = $id";

#    print "$sql<br><br>";

    $rows = $dbx->do("$sql") or warn $DBI::errstr;

    if ( $in{$key} =~ /FRR/i && $in{'Submit'} =~ /Save Changes/i) {
      $dbField = 'dbCode';
    }
    else {
      $dbField = 'dbTCode';
    }

    ## Update Aging
    $sql = "UPDATE $table.incomingtb
               SET $dbField = $tmp02,
               dbComments = '$comment'
             WHERE IncomingtbID = $incoming_id";

#    print "$sql<br><br>";

    $rows = $dbx->do("$sql") or warn $DBI::errstr;
  }
}

#______________________________________________________________________________

sub remove_action {
  my $sel_sql = "SELECT sum(for_review), sum(reviewed)
                   FROM (SELECT '1' AS 'for_review', IF (a.status IS NOT NULL, 1, 0) AS 'reviewed'
                           FROM $table.incomingtb_review a
                          WHERE a.Pharmacy_ID = $PH_ID
                        ) x";

#  print "SELECT SQL: $sel_sql<br>";

  $sth = $dbx->prepare($sel_sql);
  $sth->execute();

  while ( my ( $for_review, $reviewed ) = $sth->fetchrow_array()) {
    if ( $for_review == $reviewed ) {
      $sql = "DELETE FROM officedb.pharmacy_action_req
               WHERE Pharmacy_ID = $PH_ID
                 AND action = 'Claim Verification'";

#      print "$sql<br><br>";

      $rows = $dbx->do("$sql") or warn $DBI::errstr;
    }
  }

  $sth->finish;
}

#______________________________________________________________________________

sub close_interventions {
  my $acct_mgr = $Pharmacy_ReconRx_Account_Managers{$PH_ID};
  my $sql;

  my $close_date = &build_date();
  my $close_date_TS = &build_date_TS($close_date);

  my $sel_sql = "SELECT intervention_id, sum(for_review), sum(reviewed)
                   FROM (SELECT a.intervention_id, '1' AS 'for_review', IF (a.status IS NOT NULL, 1, 0) AS 'reviewed'
                           FROM $table.incomingtb_review a
                           JOIN officedb.interventions b ON ( a.intervention_id = b.Intervention_ID AND b.Status = 'Active')
                          WHERE a.Pharmacy_ID = $PH_ID
                        ) x
               GROUP BY intervention_id";

  $sth = $dbx->prepare($sel_sql);
  $sth->execute();

  while ( my ( $int_id, $for_review, $reviewed ) = $sth->fetchrow_array()) {
    next if ( $for_review != $reviewed );

    $sql = "INSERT INTO officedb.int_rows (Row_Intervention_ID, Row_CSR_ID, Row_CSR_Name, Row_Date_TS, Row_Date, Row_Comments)
            VALUES ($int_id, '$CSR_IDs{$acct_mgr}', '$acct_mgr', '$close_date_TS', '$close_date', 'Claim Research has been completed.')";

#    print "INT DTL SQL: $sql\n";

    $rows = $dbx->do($sql) or warn $DBI::errstr;

    $sql = "UPDATE officedb.interventions 
               SET Status = 'Closed',
                   Closed_Date_TS = '$close_date_TS',
                   Closed_Date = '$close_date'
             WHERE Intervention_ID = $int_id";

#    print "INT SQL: $sql\n";

    $rows = $dbx->do($sql) or warn $DBI::errstr;
  }

  $sth->finish;
}

#______________________________________________________________________________
