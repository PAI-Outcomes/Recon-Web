
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

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

if ( $USER ) {
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
<script>

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

  if ( $in{'Submit'} =~ /Save/i ) {
    if ( $in{'a_incoming_id'} ) {
      &process_input('A', $in{'a_incoming_id'});
    }

    if ( $in{'na_incoming_id'} ) {
      &process_input('NA', $in{'na_incoming_id'});
    }

    print qq#<h2 style="color: green">Saved!</h2>\n#;
    exit;
  }

$ntitle = "Claim Archive Authorization";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

print qq#<h2>Please Authorize the following claims for Archive:</h2>\n#;

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
#  if ( $USER == 69 || $USER == 66 ) {
  if ( $USER =~ /69/ ) {
    $type  = "'A','I'";
    $where = "a.status IS NULL || a.status = 'DIT'";
  }
  else {
    $type  = "'I'";
    $where = "a.status IS NOT NULL AND a.status NOT IN ('FRR','DIT')";
#    $where = "a.status IS NOT NULL AND a.status != 'FRR'";
#    $where = "a.status IS NOT NULL AND a.status != 'FRR' AND b.dbTCode != 'PP'";
#    $where = "(a.status IS NOT NULL AND a.status != 'FRR') OR (a.cscode = 'COB' AND b.dbTCode != 'PP')";
#    $where = "a.status IS NOT NULL AND a.status != 'FRR'";
  }

  print qq#<!-- displayWebPage -->\n#;

  print qq#<form name="frm2" id="frm2" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<INPUT TYPE="hidden" NAME="a_incoming_id" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="na_incoming_id" VALUE="">\n#;

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
  print qq# function setSelected(form) { \n#;
  print qq#     var a_ids = ''; \n#;
  print qq#     var na_ids = ''; \n#;
  print qq#       for (var i = 0; i < form.elements.length; i++ ) { \n#;
  print qq#         if (form.elements[i].type == 'checkbox' && form.elements[i].name == 'ids') { \n#;
  print qq#             if (form.elements[i].checked == true) { \n#;
  print qq#                 a_ids += form.elements[i].value + ','; \n#;
  print qq#             } else { \n#;
  print qq#                 na_ids += form.elements[i].value + ','; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#       } \n#;
  print qq#     a_ids = a_ids.substring(0, a_ids.length - 1); \n#;
  print qq#     na_ids = na_ids.substring(0, na_ids.length - 1); \n#;
  print qq#     if (a_ids == '') { \n#;
  print qq#       alert('No Records Selected'); \n#;
  print qq#       return false; \n#;
  print qq#     } \n#;
  print qq#     form.a_incoming_id.value = a_ids\n#;
  print qq#     form.na_incoming_id.value = na_ids\n#;
  print qq# } \n#;
  print qq#</script> \n#;

  print qq#
    <script>
    function denyArchive(claim_id) {
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange=function() {
        if (this.readyState == 4 && this.status == 200) {
          var r = this.response;
          if(r.match(/9/g)) {
            alert("Failed: Please Contact IT\\n");
          }
          else { 
            alert("Complete");
            document.getElementById("deny_btn_" + claim_id).style.backgroundColor = '\#404040';
          }
        }
      };

      var url = '../includes/DenyArchiveRequest.pl?user=$USER&id=' + claim_id;
      xhttp.open("POST", url, false);
      xhttp.send();
    }
    </script>
  #;

  print '<div style="position: relative; display: block; float: left;">';

  print "<table><tr><th style='background-color: #ffff4d; width: 20px;'></th><th style='font-weight: normal; font-size: 100%;'>Denied by IT</th></table>";

  print "<table id='tablef'><thead><tr><th>NCPDP</th><th>BIN</th><th>PCN</th><th>RX</th><th>DOS</th><th>AMT DUE</th><th>Reason Code</th><th>Approved</th></tr></thead><tbody>";

  $sql = "SELECT a.id, a.incomingtbID, b.dbNCPDPNumber, b.dbBinNumber, b.dbProcessorControlNumber, b.dbRxNumber, b.dbDateOfService, b.dbTotalAmountPaid_Remaining, a.cscode,
                 a.intervention_id, a.Pharmacy_ID, a.status
               FROM reconrxdb.incomingtb_review a
               JOIN reconrxdb.incomingtb b ON (a.Pharmacy_ID = b.Pharmacy_ID AND a.incomingtbID = b.incomingtbID)
               JOIN reconrxdb.cscodes c ON (a.cscode = c.code AND c.display IN ($type))
              WHERE $where
              LIMIT 10000";

#   print "$sql<br>";

   $sth = $dbx->prepare($sql);
   $sth->execute();

   %sum = ();

   while ( my ( $id, $incoming_id, $ncpdp, $bin, $pcn, $rxnum, $dos, $amt_paid, $code, $int_id, $PH_ID, $status ) = $sth->fetchrow_array()) {
     $dos = substr($dos,4,2) . '/' . substr($dos,6,2) . '/' . substr($dos,0,4);
     ++$sum{$code};
     if ( $status =~ /DIT/i ) {
       $bgcolor = '#ffff4d';
     }
     else {
       $bgcolor = '#FFFFFF';
     }

     print "<tr style='background-color: $bgcolor'>
              <td>$ncpdp</td>
              <td>$bin</td>
              <td>$pcn</td>
              <td><a href='detail_search.cgi?PH_ID=$PH_ID&rxnumber=$rxnum' target='_blank'>$rxnum</a></td>
              <td>$dos</td>
              <td>$amt_paid</td>
              <td>$code</td>";

     if ( $USER =~ /69/ ) {
       if ( $status =~ /DIT/i ) {
         print "<td><input type='checkbox' name='ids' value=$id></td>";
       }
       else {
         print "<td><input type='checkbox' name='ids' value=$id checked></td>";
       }
     }
     else {
       if ( $code !~ /COB/ ) {
         print "<td>
                  <a href='ADMIN_Date_Reconciliation_Archiving.cgi?no_menu=1&submit=Search&NCPDPNumber=$ncpdp&RxNumber=$rxnum' style='background: \#335CAD; padding: 3px; text-align: center; border-radius: 5px; color: white;' target='_blank'>Archive</a>&nbsp<a href='#' id='deny_btn_$incoming_id' style='background: \#335CAD; padding: 3px; text-align: center; border-radius: 5px; color: white;' onClick='denyArchive($incoming_id);'>Deny</a>
                </td>";
       }
       else {
         print "<td>
                  <a href='#' id='deny_btn_$incoming_id' style='background: \#335CAD; padding: 3px; text-align: center; border-radius: 5px; color: white;' onClick='denyArchive($incoming_id);'>Deny</a>
                </td>";
       }
     }

     print "</tr>";
   }

   $sth->finish;

   print "</tbody>";

   print "</table></div>";

   if ( $USER =~ /69|66/ ) {
     print '<div style="position: relative; display: block; float: left; width: 75%;">';
     print qq#<INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="Submit" VALUE="Save" onclick="return setSelected(document.frm2)">\n#;
   }
   print "</table>";
   print "</FORM>";

#  print '<br><div style="position: relative; display: block; float: left;">';
#  print '<br><div style="position: relative; display: block; float: left;">';
  print "<br><table><thead><tr><th>Code</th><th>Count</th></tr></thead><tbody>";

  $total = 0;

  foreach my $key (sort keys %sum) {
    print "<tr><td>$key</td><td>$sum{$key}</td></tr>";
    $total += $sum{$key};
  }

  print "<tr><td><strong>Total</strong></td><td><strong>$total</strong></td></tr>";

#  print "</table>";
  print "</table></div>";

}

#______________________________________________________________________________

sub process_input {
  my $type    = shift @_;
  my $sel_ids = shift @_;

  if ( $type eq 'A' ) {
    $sql = "UPDATE reconrxdb.incomingtb_review a
              JOIN reconrxdb.cscodes b ON (a.cscode = b.code)
                 SET a.status = b.to_tcode,
                     a.ts_admin_status = CURRENT_TIMESTAMP
               WHERE a.id IN ($sel_ids)";

#    print "$sql<br><br>";
    $rows = $dbx->do("$sql") or warn $DBI::errstr;

    ## Update Aging
    $sql = "UPDATE reconrxdb.incomingtb a
              JOIN reconrxdb.incomingtb_review b ON (a.IncomingtbID = b.IncomingtbID)
              JOIN reconrxdb.cscodes c ON (b.cscode = c.code AND c.display = 'A')
               SET a.dbTCode = c.to_tcode,
                   a.dbComments = concat(IFNULL(a.dbComments,''),'RAM Archive Approved: $DATEEX') 
             WHERE b.id IN ($sel_ids)";

#    print "$sql<br><br>";
    $rows = $dbx->do("$sql") or warn $DBI::errstr;

    &notify_possible_recnos($sel_ids);
  }
  else {
    $sql = "UPDATE reconrxdb.incomingtb_review
                 SET status = 'DSUP',
                     ts_admin_status = CURRENT_TIMESTAMP
               WHERE id IN ($sel_ids)
                 AND status != 'DIT'";

#    print "$sql<br><br>";
    $rows = $dbx->do("$sql") or warn $DBI::errstr;

    ## Update Aging
    $sql = "UPDATE reconrxdb.incomingtb a
              JOIN reconrxdb.incomingtb_review b ON (a.IncomingtbID = b.IncomingtbID)
               SET a.dbCode = 'DSUP'
             WHERE b.id IN ($sel_ids)
               AND a.dbCode != 'DIT'";

#    print "$sql<br><br>";
    $rows = $dbx->do("$sql") or warn $DBI::errstr;
  }
}

#______________________________________________________________________________

sub notify_possible_recnos {
  my $sel_ids = shift @_;
  my $tbl_data = '';

  &read_emails();

  ## Update Aging
  $sql = "SELECT a.Pharmacy_ID, a.dbNCPDPNumber, a.dbBinNumber, c.DateAdded, count(*)
            FROM reconrxdb.incomingtb a
            JOIN reconrxdb.incomingtb_review b ON (a.IncomingtbID = b.IncomingtbID)
       LEFT JOIN reconrxdb.aging_exclusions_per_pid c ON (a.Pharmacy_ID = c.Pharmacy_ID AND a.dbBinNumber = c.BinNumber)
           WHERE b.id IN ($sel_ids)
             AND b.cscode = 'RNO'
             AND b.status = 'BR'
             AND c.DateAdded IS NULL
        GROUP BY a.Pharmacy_ID, a.dbNCPDPNumber, a.dbBinNumber, c.DateAdded";

#    print "$sql<br><br>";

  my $sthr = $dbx->prepare("$sql");
  my $numrows = $sthr->execute();
 
  if ( $numrows > 0 ) {
    while ( my ($ph_id, $ncpdp, $bin, $count) = $sthr->fetchrow_array() ) {
      $tbl_data .= "<tr><td class='bd'>$ncpdp</td><td class='bd'>$ncpdp</td><td class='bd'>$bin</td><td class='bd'>$count</td></tr>";
    }

    &generate_email($tbl_data);
  }

  $sthr->finish();
}

#______________________________________________________________________________

sub generate_email {
  my $tbl_data = shift @_;
  my $sig_img   = "D:\\RedeemRx\\CannedFiles\\TDS_Signature.png";

  $ram = 'Kanatzar, Jessie';
  $from = 'jkanatzar';

  my $message = "<style>p.MsoNormal, li.MsoNormal, div.MsoNormal {margin:0in; margin-bottom:.0001pt; font-size:11.0pt; font-family:'Calibri',sans-serif;} table.bd, td.bd, th.bd {
      border: 1px solid black; padding: 5px;}</style>";

  $message .= "<p>IT,</p><p>Please add the following BIN(s) to the Reconcile No table for given NCPDP(s).</p>";
  $message .= "<table class='bd' style='border-collapse: collapse;'><tr><th class='bd'>NCPDP</th><th class='bd'>Pharmacy ID</th><th class='bd'>BIN</th><th class='bd'>CLM COUNT</th></tr></thead><tbody>";

  $message .= $tbl_data;
  $message .= "</tbody></table>";

  $message .= &add_email_sig($ram, $from, 'Email');

  $to      = 'PAIT@tdsclinical.com';
#  $to      = 'jkanatzar@tdsclinical.com';

  $subject = "Request to Add BIN to Reconcile No Table";

  if (! &send_email($from, $to, $subject, $message, 1, $sig_img) ) {
     print "<span style='color: red'>Unable to send request $to</span>";
  }
}

#______________________________________________________________________________

sub add_email_sig {
  my $ram = shift @_;
  my $user = shift @_;
  my $display = shift @_;
  my $sig_img;

  if ( $display =~ /Web/i ) {
    $sig_img   = "../images/TDS_Signature.png";
  }
  else {
    $sig_img   = "cid:TDS_Signature.png";
  }

  @pcs = split(/\,\s/, $ram);
  $sig_name = "$pcs[1] $pcs[0]";
  $sig_email = $EMAILACCT{$user};
  $sig_title = $EMAIL_SIG_TITLE{$user};
  $sig_ext   = $EMAIL_SIG_EXT{$user};

  my $sig .= "<p>Thank You,</p><table>
                <tr>
                  <td style='background:white;padding:0in 6.0pt 0in 6.0pt'>
                    <b><span style='font-size:12.0pt;color:#002060;text-transform:uppercase'>$sig_name</span></b><br>
                    <span style='color:#002060;text-transform:uppercase'>$sig_title<br></span>
                  </td>
                <tr>
                  <td>
                    <img border=0 width=255 height=133 src='cid:TDS_Signature.png' align=left hspace=12>
                  </td>
                </tr>
                <tr>
                  <td style='background:white;padding:0in 1.0pt 0in 1.0pt'>
                    <span style='color:blue'><a href='mailto:$sig_email'>$sig_email</a></span></br>
                    <span style='color:#002060;text-transform:uppercase'>TEL: (888) 255-6526 ext. 118</span></br>
                    <a href='http://www.tdsclinical.com/'><span style='color:#767171;text-transform:uppercase'>TRANSACTION DATA SYSTEMS</span></a></br>
                    <p style='margin:0in'>
                      <a href='http://www.rx30.com/'><span style='color:#767171;text-transform:uppercase'>RX30</a> | </span>
                      <a href='http://www.computer-rx.com/'><span style='color:#767171;text-transform:uppercase'>COMPUTER-RX</a> | </span>
                      <a href='https://kloudscript.com/'><span style='color:#767171;text-transform:uppercase'>KLOUDSCRIPT</a> | </span>
                      <a href='https://www.pharmassess.com/'><span style='color:#767171;text-transform:uppercase'>PHARM ASSESS</a> | </span>
                      <a href='https://www.enhancedmedicationservices.com/'><span style='color:#767171;text-transform:uppercase'>EMS</span></a>
                    </p>
                    <p class=MsoNormal style='mso-margin-top-alt:auto;line-height:105%'>
                      <span style='font-size:9.0pt;line-height:105%;color:#767171'>
                        The information contained in this transmission may contain privileged and confidential information, including patient information protected by federal and state privacy laws. It is intended only for the use of the person(s) named above. If you are not the intended recipient, you are hereby notified that any review, dissemination, distribution, or duplication of this communication is strictly prohibited. If you are not the intended recipient, please contact the sender by reply email and destroy all copies of the original message.
                      </span>
                    </p>
                  </td>
                </tr>
              </table>";

  return $sig;
}


