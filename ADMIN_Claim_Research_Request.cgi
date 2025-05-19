use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Excel::Writer::XLSX;
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

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

#______________________________________________________________________________

if ( $USER ) {
  &readCSRs();
  &readPharmacies();
  &readThirdPartyPayers();
  &read_emails();

  $ram = $CSR_Reverse_ID_Lookup{$USER};

  if ( $in{submit} =~ /^Preview/i ) {
    &displayPreview();
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

#______________________________________________________________________________

&hasAccess($USER);

if ( $ReconRx_Admin_Dashboard_Aging_Tool !~ /^Yes/i ) {
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
$long_time  = sprintf("%04d%02d%02d%02d%02d", $year, $month, $day, $hour, $min);

my $SECRET = "ReconRx2021#";

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

#Start page operations
  
if ( $in{submit} =~ /Submit/i ) {
  &process_request();
}

&displayOptions;

&displayResults();

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

  print qq#<tr><td><label for="NCPDP">Pharmacy:</label></td>#;
  print qq#<td><input type="text" name="NCPDP" list="plist" id="NCPDP" value="$in{NCPDP}" style="width:300px;">\n#;
  print qq#<datalist id="plist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
               FROM officedb.pharmacy 
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
                 && ReconRx_Account_Manager = '$ram'
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM officedb.pharmacy_coo
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                 #&& NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
                 && ReconRx_Account_Manager = '$ram'
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($PH_ID, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    print qq#<option value="$NCPDP - $Pharmacy_Name"> </option>\n#;
  }

  $sthx->finish;
  print qq# </datalist></td></tr>#;


  print qq#<tr><td><label for="BIN">Third Party Payer:</label></td>#;
  print qq#<td><input type="text" name="BIN" list="blist" id="bin" value="$in{BIN}" style="width:300px;">\n#;
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

  print qq#<tr><td><label for="SendTo">Send To:</label></td>#;
  print qq#<td><select name="SendTo" id="sendto">\n#;
  print qq# <option value="0">-Select-</option>#;
  print qq# <option value="TPP">TPP</option>#;
  print qq# <option value="PSAO">PSAO</option>#;
  print qq# </select></td></tr>#;

  print qq#<td><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Filter"><INPUT style="padding:5px; margin:5px" TYPE="button" NAME="Clear" VALUE="Clear" onclick="clearSearch(this.form);"></td><td>$nbsp</td></tr>\n#;

  print qq#</table>\n#;

  print qq#</form>\n#;

  print qq#<br /><hr />\n#;
}

#______________________________________________________________________________

sub displayResults {
  my $where;

  foreach $key (sort keys %in) {
    next if ($key =~ /submit/);

    $field = $key;

    if ( $key =~ /NCPDP/i && $in{$key} ne '') {
      $where .= "&& $field = '" . substr($in{$key},0,7) . "' ";
    }
    elsif ( $key =~ /BIN/i && $in{$key} ne '') {
      $where .= "&& payer = '" . substr($in{$key},9) . "' ";
    }
  }

  print qq#<form name="frm2" id="frm2" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<INPUT TYPE="hidden" NAME="clmrvw_id" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="send_to" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="NCPDP" VALUE="$in{'NCPDP'}">\n#;

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
  print qq# function setSelected(form, target) { \n#;
  print qq#     var ids = ''; \n#;
  print qq#     if (document.getElementById("sendto").value != '0') { \n#;
  print qq#       for (var i = 0; i < form.elements.length; i++ ) { \n#;
  print qq#         if (form.elements[i].type == 'checkbox' && form.elements[i].name == 'ids') { \n#;
  print qq#             if (form.elements[i].checked == true) { \n#;
  print qq#                 ids += form.elements[i].value + ','; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#       } \n#;
  print qq#       ids = ids.substring(0, ids.length - 1); \n#;
  print qq#       if (ids == '') { \n#;
  print qq#         alert('No Records Selected'); \n#;
  print qq#         return false; \n#;
  print qq#       } \n#;
  print qq#       form.clmrvw_id.value = ids\n#;
  print qq#       form.send_to.value = document.getElementById("sendto").value\n#;
  print qq#       document.getElementById('frm2').target = target; \n#;
  print qq#     } else { \n#;
  print qq#       alert('Please select an option for "Send To"'); \n#;
  print qq#       return false; \n#;
  print qq#     } \n#;
  print qq# } \n#;

  print qq#</script> \n#;

  print qq#<table id="tablef">\n#;
  print "<thead>\n";
  print qq#<tr>
             <th><INPUT name=\"selectall\" type=\"checkbox\" onchange=\"checkAll(this)\" name=\"ids[]\" /></th>
             <th>NCPDP</th>
             <th>TPP</th>
             <th>BIN</th>
             <th>PCN</th>
             <th>Rx</th>
             <th>Filled Date</th>
             <th>Processed Date</th>
             <th>Amount Due</th>
             <th>Code</th>
             <th>Date Sent</th>\n#;
  print qq#</tr>\n#;

  print "</thead>\n";
  print "<tbody>\n";

  my $DBNAME = "reconrxdb";

  $sql = "SELECT cr.id, ph.NCPDP, cr.tpp_id, clm.dbBinNumber, clm.dbRxNumber, Date_Format(clm.dbDateOfService,'%m/%d/%Y'), Date_Format(SUBSTR(clm.dbDateTransmitted,1,8),'%m/%d/%Y'),
                 IFNULL(clm.dbTotalAmountPaid_Remaining,0), IFNULL(clm.dbTotalAmountPaid,0), clm.dbProcessorControlNumber, clm.dbCode, Date_Format(cr.date_sent_tpp,'%m/%d/%Y')
            FROM $DBNAME.incomingtb_review cr
            JOIN $DBNAME.incomingtb clm ON (cr.incomingtbID = clm.incomingtbID)
            JOIN officedb.pharmacy ph ON (cr.Pharmacy_ID = ph.Pharmacy_ID)
           WHERE cr.status = 'FRR'
             AND ph.ReconRx_Account_Manager = '$ram'
             AND clm.dbBinParentdbkey != '700006'
           $where
        ORDER BY cr.date_sent";

#  print "$sql<br>";
 
  my $sthr  = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($id, $ncpdp, $tpp_id, $bin, $rxnum, $dos, $dtrans, $amt_paid_rm, $amt_paid, $pcn, $code, $dte_sent) = $sthr->fetchrow_array() ) {
    $req_sent = $dte_sent;
    $tpp_name = $TPP_Names{$tpp_id};
    if ( $req_sent ) {
      $req_sent = '<span style="color: green">Sent</span>';
    }
    else {
      $req_sent = "<input type='checkbox' name='ids' value=$id>";
    }
    print "<tr><td>$req_sent</td><td>$ncpdp</td><td>$tpp_name</td><td>$bin</td><td>$pcn</td><td>$rxnum</td><td>$dos</td><td>$dtrans</td><td>$amt_paid_rm</td><td>$code</td><td>$dte_sent</td></tr>\n";
  }

  $sthr->finish;

  print "</tbody>";
  print "</table><br>\n";
  print qq#<td><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Submit" onclick="return setSelected(document.frm2, '_self')"></td><td>$nbsp</td></tr>\n#;

  print "</form>\n";
}  

#______________________________________________________________________________

sub process_request {
  my $sel_ids = $in{'clmrvw_id'};
  my $sendto = $in{'send_to'};

  my $sql = "SELECT cr.tpp_id, cr.Pharmacy_id, clm.dbBinNumber, clm.dbNCPDPNumber, clm.dbRxNumber, clm.dbDateOfService, clm.dbDateTransmitted, clm.dbTotalAmountPaid, clm.dbCode, clm.dbProcessorControlNumber, clm.dbGroupID,
                    clm.dbCardHolderID, clm.dbPatientFirstName, clm.dbPatientLastName, clm.dbDateOfBirth, clm.dbStatus, clm.dbPSS, clm.dbCFA, clm.dbIntervention_ID, clm.dbOtherPayerAmountRecognized
               FROM $DBNAME.incomingtb_review cr
               JOIN $DBNAME.incomingtb clm ON (cr.incomingtbID = clm.incomingtbID)
              WHERE cr.id IN ($sel_ids)
           ORDER BY clm.dbBinNumber, clm.dbNCPDPNumber, clm.dbDateTransmitted";

#  print "$sql<br>";

  my $key_sav = '';
  my $wrow = 1;
  my $dte_trans_sav = '';
 
  my $sthr = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my @row = $sthr->fetchrow_array() ) {
    my ($tpp_id, $Pharmacy_ID, $dbBinNumber, $dbNCPDPNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid, $dbCode, $dbProcessorControlNumber, $dbGroupID, $dbCardHolderID, $dbPatientFirstName, $dbPatientLastName, $dbDateOfBirth, $dbStatus, $dbPSS, $dbCFA, $dbIntervention_ID, $dbOtherPayerAmountRecognized ) = @row;
    my $key = "$tpp_id##$Pharmacy_ID";

    my $dbDateOfServiceDisplay = substr($dbDateOfService, 4, 2) . "/" . substr($dbDateOfService, 6, 2) . "/" . substr($dbDateOfService, 0, 4);
    my $dbDateTransmittedDisplay = substr($dbDateTransmitted, 4, 2) . "/" . substr($dbDateTransmitted, 6, 2) . "/" . substr($dbDateTransmitted, 0, 4);
    my $dbDateOfBirthDisplay = substr($dbDateOfBirth, 4, 2) . "/" . substr($dbDateOfBirth, 6, 2) . "/" . substr($dbDateOfBirth, 0, 4);
      
    if ( $key ne $key_sav ) {
      if ( $key_sav ne '' ) {
        #### Finish and Send Spreadsheet
        $workbook->close(); #End XLSX

        $cmd = qq#"C:/Program Files/7-Zip/7z.exe" a "$zip_location/$zfilename" "$zip_location/$filename" -p$SECRET#;
   
        ##print $cmd;
        `$cmd`;

        if ( &generate_email($key_sav, $save_location.$zfilename) ) {
          $clm_dates .= "-$dte_trans_sav";
          &create_intervention($key_sav, $ram, $clm_dates);
        }
      }

      $save_location = "D:\\Recon-Rx\\Reports\\";
      $zip_location = "D:/Recon-Rx/Reports/";
      $filename = "Claim_Research_${dbNCPDPNumber}_${long_time}.xlsx";
      $zfilename = $filename;
      $zfilename =~ s/.xlsx/.zip/;

      $wrow = 1;
      $clm_dates = $dbDateTransmittedDisplay;
      &setExcel($save_location.$filename);
    }

    $wrow++;
  
    $worksheet->write( "A$wrow", $dbBinNumber );  
    $worksheet->write( "B$wrow", $dbNCPDPNumber );  
    $worksheet->write( "C$wrow", $dbRxNumber );  
    $worksheet->write( "D$wrow", $dbDateOfServiceDisplay );  
    $worksheet->write( "E$wrow", $dbDateTransmittedDisplay );  
    $worksheet->write( "F$wrow", $dbTotalAmountPaid );  
    $worksheet->write( "G$wrow", $dbCode );  
    $worksheet->write( "H$wrow", $dbProcessorControlNumber );  
    $worksheet->write( "I$wrow", $dbGroupID );  
    $worksheet->write( "J$wrow", $dbCardHolderID, $format_left );  
    $worksheet->write( "K$wrow", $dbPatientFirstName );  
    $worksheet->write( "L$wrow", $dbPatientLastName );  
    $worksheet->write( "M$wrow", $dbDateOfBirthDisplay );  

    $key_sav = $key;
    $dte_trans_sav = $dbDateTransmittedDisplay;
  }

  $sthr->finish();

  $workbook->close(); #End XLSX

  $cmd = qq#"C:/Program Files/7-Zip/7z.exe" a "$zip_location/$zfilename" "$zip_location/$filename" -p$SECRET#;

##  print $cmd;
  
  `$cmd`;

  if ( &generate_email($key_sav, $save_location.$zfilename) ) {
    $dbx->do("UPDATE $DBNAME.incomingtb_review SET date_sent_tpp = '$adate' WHERE id IN ($sel_ids)") or die $DBI::errstr;

    $clm_dates .= "-$dte_trans_sav";
    &create_intervention($key_sav, $ram, $clm_dates);
  }

}

#______________________________________________________________________________

sub generate_email {
  my $param    = shift @_;
  my $filename = shift @_;

  my ($tpp_id, $Pharmacy_ID) = split(/##/, $param);

  my @attach = ($sig_img, $filename);

  $Pharmacy_Name  = $Pharmacy_Names{$Pharmacy_ID};
  $Pharmacy_NCPDP = $Pharmacy_NCPDPs{$Pharmacy_ID};

  @pcs = split(/@/, $CSR_Emails{$ram});
  $user_email = $pcs[0];
  $from = $user_email;

  if ( $in{'send_to'} =~ /PSAO/i ) {
    $Current_PSAO = $Pharmacy_Current_PSAOs{$Pharmacy_ID};
    $tpp_id = &get_tpp_id($Current_PSAO);
#    print "IS PSAO: $Current_PSAO - $tpp_id<br>";
  }

  my $message .= "<p>$ThirdPartyPayer_Names{$tpp_id},</p><p>The attached claims appear to be unpaid for $Pharmacy_Name ($Pharmacy_NCPDP). Please research these claims and provide the associated payment information (check/ACH number, date, and amount). If these claims have not been paid, please let me know when the pharmacy can expect payment.</p><p>Additionally, please send the 835 files associated with the attached claims to ReconRx and let me know when they have been sent.</p><p>Password to follow.</p>";

  $message .= &add_email_sig($ram, $user_email, 'Email');

  $to = $TPP_RemittancePrimary_Contact_Emails{$tpp_id};
#  print "TO: $to<br>";

#  $to      = 'bprowell@tdsclinical.com';
#  $to      = 'jkanatzar@tdsclinical.com';

  $subject = "ReconRx Action Required: Claim Research and 835 File Request- $Pharmacy_NCPDP";

  if (! &send_email($from, $to, $subject, $message, 1, @attach) ) {
     print "<span style='color: red'>Unable to send request $to</span>";
     return 0;
  }
  else {
     sleep(5);
     &send_email($from, $to, '', $SECRET);
     print "<span style='color: green'><p>Claim Research Successfully Sent to - $to</p></span>";
     return 1;
  }
}

#______________________________________________________________________________

sub add_email_sig_old {
  my $ram = shift @_;
  my $user = shift @_;
  my $display = shift @_;
  my $sig_img;

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
                    <img border=0 width=255 height=133 src='' align=left hspace=12>
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

#______________________________________________________________________________

sub create_intervention {
  my $param    = shift @_;
  my $acct_mgr = shift @_;
  my $dates    = shift @_;

  my ($tpp_id, $Pharmacy_ID) = split(/##/, $param);

  chop($checks);
  chop($check_ids);

  my $open_date = &build_date();
  my $open_date_TS = &build_date_TS($open_date);
  my ($type_id, $cat, $type, $comments);

  $type     = 'ThirdPartyPayer';
  $type_id  = $tpp_id; 
  $cat      = 'ReconRx - Claim Research Request';
  $comments = "Claims dated $dates are not associated with a pending remit and have been sent for research.";

  my $sql = "INSERT 
               INTO officedb.interventions 
                SET Pharmacy_ID = $Pharmacy_ID,
                    Type = '$type',
                    Type_ID = '$type_id',
                    Category = '$cat',
                    Program = 'ReconRx',
                    CSR_ID = $CSR_IDs{$acct_mgr},
                    CSR_Name = '$acct_mgr',
                    Status = 'Active',
                    Opened_Date_TS = '$open_date_TS',
                    Opened_Date = '$open_date',
                    Comments = '$comments'";

#  print "$sql<br>";

  my $sth = $dbx->prepare($sql);
  $sth->execute() or die $DBI::errstr;
  $inserted = $sth->rows;

  $sth->finish();
}

#______________________________________________________________________________

sub setExcel {
  my $SSName = shift @_;

  unlink "$SSName" if ( -e "$SSName" );

  $workbook = Excel::Writer::XLSX->new( $SSName );
  $worksheet = $workbook->add_worksheet();
  $worksheet->set_landscape();
  $worksheet->fit_to_pages( 1, 0 ); #Fit all columns on a single page
  $worksheet->hide_gridlines(0); #0 = Show gridlines
    
  $worksheet->freeze_panes( 1, 0 ); #Freeze first row
  $worksheet->repeat_rows( 0 );    #Print on each page
    
  $worksheet->set_header("&LReconRx");
    
  $format_bold = $workbook->add_format();
  $format_bold->set_bold();

  $wrow = 1;
  $worksheet->write( "A$wrow", 'BIN', $format_bold); #0 
  $worksheet->write( "B$wrow", 'NCPDP', $format_bold);  #1
  $worksheet->write( "C$wrow", 'Rx', $format_bold); #2
  $worksheet->write( "D$wrow", 'Date of Service', $format_bold); #3
    $worksheet->set_column( 3, 3, 18 );
  $worksheet->write( "E$wrow", 'Processed Date', $format_bold); #4
    $worksheet->set_column( 4, 4, 18 );
  $worksheet->write( "F$wrow", 'Amount Due', $format_bold); #5
    $worksheet->set_column( 5, 5, 16 );
  $worksheet->write( "G$wrow", 'Code', $format_bold); #6
  $worksheet->write( "H$wrow", 'PCN', $format_bold); #7
    $worksheet->set_column( 7, 7, 18 );
  $worksheet->write( "I$wrow", 'Group', $format_bold); #8 
  $worksheet->write( "J$wrow", 'Cardhold ID', $format_bold); #9
    $worksheet->set_column( 9, 9, 18 );
  $worksheet->write( "K$wrow", 'Patient First Name', $format_bold); #10
    $worksheet->set_column( 10, 10, 18 );
  $worksheet->write( "L$wrow", 'Patient Last Name', $format_bold); #11
    $worksheet->set_column( 11, 11, 18 );
  $worksheet->write( "M$wrow", 'Patient DOB', $format_bold); #12
    $worksheet->set_column( 12, 12, 18 );

  my $format_left = $workbook->add_format();
  $format_left->set_align( 'left' );
  my $format_center = $workbook->add_format();
  $format_center->set_align( 'center' );
  my $format_right = $workbook->add_format();
  $format_right->set_align( 'right' );
  my $format_number = $workbook->add_format();
  $format_number->set_num_format( '#,##0' );
  my $format_money = $workbook->add_format();
  $format_money->set_num_format( '$#,##0.00' );
  
  $worksheet->keep_leading_zeros();
}

#______________________________________________________________________________

sub get_tpp_id {
  my $psao_name = shift @_;
  my $tpp_id = 0;

  if ( $psao_name =~ /Arete/i ) {
    $tpp_id = 700470;
  }
  elsif ( $psao_name =~ /Cardinal/i ) {
    $tpp_id = 700640;
  }
  elsif ( $psao_name =~ /Elevate/i ) {
    $tpp_id = 700641;
  }
  elsif ( $psao_name =~ /Health Mart Atlas/i ) {
    $tpp_id = 700447;
  }
  elsif ( $psao_name =~ /GeriMed/i ) {
    $tpp_id = 700447;
  }

  return($tpp_id);
}
