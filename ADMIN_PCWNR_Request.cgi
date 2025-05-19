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

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

#______________________________________________________________________________

if ( $USER ) {
  &readCSRs();
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

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

#Start page operations
  
if ( $in{submit} =~ /Send/i ) {
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
                 #&& ReconRx_Account_Manager = '$ram'
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM officedb.pharmacy_coo
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
                 #&& ReconRx_Account_Manager = '$ram'
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
      $where .= "&& $field = '" . substr($in{$key},0,6) . "' ";
    }
  }

  print qq#<form name="frm2" id="frm2" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<INPUT TYPE="hidden" NAME="pcwnr_id" VALUE="">\n#;
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
  print qq#     for (var i = 0; i < form.elements.length; i++ ) { \n#;
  print qq#       if (form.elements[i].type == 'checkbox' && form.elements[i].name == 'ids') { \n#;
  print qq#           if (form.elements[i].checked == true) { \n#;
  print qq#               ids += form.elements[i].value + ','; \n#;
  print qq#           } \n#;
  print qq#       } \n#;
  print qq#     } \n#;
  print qq#     ids = ids.substring(0, ids.length - 1); \n#;
  print qq#     if (ids == '') { \n#;
  print qq#       alert('No Records Selected'); \n#;
  print qq#       return false; \n#;
  print qq#     } \n#;
  print qq#     form.pcwnr_id.value = ids\n#;
  print qq#     document.getElementById('frm2').target = target; \n#;
  print qq# } \n#;

  print qq#</script> \n#;

  print qq#<table id="tablef">\n#;
  print "<thead>\n";
  print "<tr><th><INPUT name=\"selectall\" type=\"checkbox\" onchange=\"checkAll(this)\" name=\"ids[]\" /></th><th>NCPDP</th><th>BIN</th><th>Payer Name</th><th>Pmt Type</th><th>Check Num</th><th>Check Amt</th><th>Check Date</th></tr>\n";
  print "</thead>\n";
  print "<tbody>\n";

  my $DBNAME = "reconrxdb";

  my $sql = "SELECT id, NCPDP, BIN, ThirdParty, PaymentType, CheckNumber, CheckAmount, CheckDate, RequestSent
               FROM $DBNAME.paymentnoremit
              WHERE Pharmacy_ID IN (SELECT Pharmacy_ID FROM officedb.pharmacy WHERE ReconRx_Account_Manager = '$ram')
              #WHERE Pharmacy_ID IN (SELECT Pharmacy_ID FROM officedb.pharmacy WHERE 1=1)
             $where";

#  print "$sql<br>";
 
  my $sthr  = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($id, $ncpdp, $bin, $payer, $pmt_type, $chk_num, $chk_amt, $chk_dte, $req_sent) = $sthr->fetchrow_array() ) {
    if ( $req_sent ) {
      $req_sent = '<span style="color: green">Requested</span>';
    }
    else {
      $req_sent = "<input type='checkbox' name='ids' value=$id>";
    }
    print "<tr><td>$req_sent</td><td>$ncpdp</td><td>$bin</td><td>$payer</td><td>$pmt_type</td><td>$chk_num</td><td>$chk_amt</td><td>$chk_dte</td></tr>\n";
  }

  $sthr->finish;

  print "</tbody>";
  print "</table><br>\n";
  print qq#<td><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Preview" onclick="return setSelected(document.frm2, '_blank')"><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Send" onclick="return setSelected(document.frm2, '_self')"></td><td>$nbsp</td></tr>\n#;

  print "</form>\n";
}  

#______________________________________________________________________________

sub displayPreview {
  my $sel_ids = $in{'pcwnr_id'};
  print "Content-type: text/html\n\n";

  my $email = qq#<!doctype html> 
                 <html lang="en">
                   <head>
                     <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

                     <TITLE>Preview</TITLE>
   
                   </head>

                   <body leftmargin="0" topmargin="0" marginwidth="0" marginheight="0"> #;

  my $email .= '<h3><strong>Disclaimer: Representation of email only.  Styling may vary from actual email sent.</strong></h3>';

  &read_emails();

  @pcs = split(/\,\s/, $ram);
  @pcs = split(/@/, $CSR_Emails{$ram});
  $user_email = $pcs[0];
  $chk_dates = '';

  my $sql = "SELECT a.id, a.Pharmacy_ID, a.NCPDP, b.Third_Party_Payer_ID, a.ThirdParty, b.RemittancePrimary_Contact_Email, a.PaymentType, a.CheckNumber, a.CheckAmount, a.CheckDate
               FROM $DBNAME.paymentnoremit a
          LEFT JOIN officedb.third_party_payers b ON (a.BIN = b.BIN AND a.ThirdParty = b.Third_Party_Payer_Name AND b.Status = 'Active')
              WHERE a.id IN ($sel_ids)
           ORDER BY a.Pharmacy_ID, b.Third_Party_Payer_ID, a.CheckDate";

#  print "$sql<br>";
 
  my $sthr = $dbx->prepare("$sql");
  $sthr->execute;

  $first = 1;
  $tpp_id_sav = '';
  $ph_id_sav = '';

  while ( my ($id, $pharmacy_id, $ncpdp, $tpp_id, $payer, $payer_email, $pmt_type, $chk_num, $chk_amt, $chk_date) = $sthr->fetchrow_array() ) {
    if ( ($tpp_id != $tpp_id_sav || $pharmacy_id != $ph_id_sav) || $first ) {
      if (!$first) {
        $email .= "</tbody></table>";

        #### Add Signature
        $email .= &add_email_sig($ram, $user_email, 'Web');

        $email .= "</td></tr></tbody>";
        $email .= "</table><br>";
      }

      $email .= "<style>p.MsoNormal, li.MsoNormal, div.MsoNormal {margin:0in; margin-bottom:.0001pt; font-size:11.0pt; font-family:'Calibri',sans-serif;} table.bd {
                 border: 1px solid black; margin: 5px; padding: 0px;} td.bd {border-top: 1px solid black;} td.nb {border: 0px solid white;} table.bord { border: 1px solid black; border-collapse: collapse;}
                 th.bdd { border: 1px solid black; border-collapse: collapse; padding: 0px 5px 0px 5px;} td.bdd { border: 1px solid black; border-collapse: collapse; padding: 0px 5px 0px 5px;}</style>";

      if ( $payer_email !~ /^\s+$/) {
        $tpp_email = $payer_email;
      }
      else {
        $tpp_email = "<div style='color:red'>Remittance Primary Contact Email Not Set</div>";
      }  

      $email .= "<table class='bd'><thead><tr><th align=left>From:</th><th align=left>$EMAILACCT{$user_email}</th></tr>";
      $email .= "<tr><th align=left>To:</th><th align=left>$tpp_email</th></tr>";
      $email .= "<tr><th align=left>Subject:</th><th align=left>ReconRx Action Required: Missing 835 File(s) Request</th></tr></thead>";

      $email .= "<tbody><tr>
                   <td colspan=2 class='bd'><p>Attention $payer,</p>
                     <p>Please send ReconRx the 835 file(s) associated with the below payment(s), and provide confirmation once sent.</p>
                     <table class='bord'><thead><tr><th class='bdd'>NCPDP</th><th class='bdd'>TPP</th><th class='bdd'>TYPE</th><th class='bdd'>NUMBER</th><th class='bdd'>AMT</th><th class='bdd'>DATE</th></tr></thead><tbody>";
    }

    $chk_date = substr($chk_date,4,2) . '/' . substr($chk_date,6,2) . '/' . substr($chk_date,0,4);

    $email .= "<tr><td class='bdd'>$ncpdp</td><td class='bdd'>$payer</td><td class='bdd'>$pmt_type</td><td class='bdd'>$chk_num</td><td class='bdd'>\$$chk_amt</td><td class='bdd'>$chk_date</td></tr>";
    #$email .= "<tr><td>$ncpdp</td><td>$payer</td><td>$pmt_type</td><td>$chk_num</td><td>$chk_amt</td><td>$chk_date</td></tr>";

    $tpp_id_sav = $tpp_id;
    $ph_id_sav = $pharmacy_id;
    $first = 0;
  }

  $sthr->finish;

  $email .= "</tbody></table>";

  #### Add Signature
  $email .= &add_email_sig($ram, $user_email, 'Web');

  $email .= "</td></tr></tbody>";
  $email .= "</table><br>";

  print "$email";

  print qq#<INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Close" onclick="self.close()">\n#;
  print "</body></html>";
  exit;
}

#______________________________________________________________________________

sub process_request {
  my $sel_ids = $in{'pcwnr_id'};

  &readThirdPartyPayers();
  &read_emails();

  my $sql = "SELECT a.id, a.Pharmacy_ID, a.NCPDP, b.Third_Party_Payer_ID, a.ThirdParty, b.RemittancePrimary_Contact_Email, a.PaymentType, a.CheckNumber, a.CheckAmount, a.CheckDate
               FROM $DBNAME.paymentnoremit a
          LEFT JOIN officedb.third_party_payers b ON (a.BIN = b.BIN AND a.ThirdParty = b.Third_Party_Payer_Name AND b.Status = 'Active')
              WHERE a.id IN ($sel_ids)
           ORDER BY a.Pharmacy_ID, b.Third_Party_Payer_ID, a.CheckDate";

#  print "$sql<br>";
 
  my $sthr = $dbx->prepare("$sql");
  $sthr->execute;

  my $first = 1;
  my $tbl_data = '';
  my $tpp_id_sav = '';
  my $ph_id_sav = '';
  my $email_chk_dates = '';
  my $email_ids = '';

  while ( my ($id, $pharmacy_id, $ncpdp, $tpp_id, $payer, $payer_email, $pmt_type, $chk_num, $chk_amt, $chk_date) = $sthr->fetchrow_array() ) {
    if ( ($tpp_id != $tpp_id_sav || $pharmacy_id != $ph_id_sav) && !$first ) {
      &generate_email($tpp_id_sav, $tbl_data);

      &create_intervention($ph_id_sav, $ram, $tpp_id_sav, $email_chk_dates, $email_ids);

      $tbl_data = '';
      $email_chk_dates = '';
      $email_ids = '';
    }

    $chk_date = substr($chk_date,4,2) . '/' . substr($chk_date,6,2) . '/' . substr($chk_date,0,4);
    $email_chk_dates .= " $chk_date,";
    $email_ids .= "$id,";

    $tbl_data .= "<tr><td class='bd'>$ncpdp</td><td class='bd'>$payer</td><td class='bd'>$pmt_type</td><td class='bd'>$chk_num</td><td class='bd'>\$$chk_amt</td><td class='bd'>$chk_date</td></tr>";

    $tpp_id_sav = $tpp_id;
    $ph_id_sav = $pharmacy_id;
    $first = 0;
  }

  &generate_email($tpp_id_sav, $tbl_data);

  &create_intervention($ph_id_sav, $ram, $tpp_id_sav, $email_chk_dates, $email_ids);

  $sthr->finish();
}

#______________________________________________________________________________

sub generate_email {
  my $tpp_id = shift @_;
  my $tbl_data = shift @_;

  my @attach = ($sig_img);

  @pcs = split(/@/, $CSR_Emails{$ram});
  $user_email = $pcs[0];
  $from = $user_email;

  my $message = "<style>p.MsoNormal, li.MsoNormal, div.MsoNormal {margin:0in; margin-bottom:.0001pt; font-size:11.0pt; font-family:'Calibri',sans-serif;} table.bd, td.bd, th.bd {
      border: 1px solid black; padding: 5px;}</style>";

  $message .= "<p>Attention $ThirdPartyPayer_Names{$tpp_id},</p><p>Please send ReconRx the 835 file(s) associated with the below payments(s), and provide confirmation once sent.</p>";
  $message .= "<table class='bd' style='border-collapse: collapse;'><tr><th class='bd'>NCPDP</th><th class='bd'>TPP</th><th class='bd'>TYPE</th><th class='bd'>NUMBER</th><th class='bd'>AMT</th><th class='bd'>DATE</th></tr></thead><tbody>";

  $message .= $tbl_data;
  $message .= "</tbody></table>";

  $message .= &add_email_sig($ram, $user_email);

  if ( $tpp_id == 700165 ) {
    $to = "$TPP_RemittancePrimary_Contact_Emails{$tpp_id},$TPP_RemittanceMaintenance_Contact_Emails{$tpp_id},$TPP_RxPaymentInquiries_Contact_Emails{$tpp_id}";
  }
  else {
    $to = $TPP_RemittancePrimary_Contact_Emails{$tpp_id};
  }

#  $to      = 'jkanatzar@tdsclinical.com';

  $subject = "ReconRx Action Required: Missing 835 File(s) Request";
  #print "$from, $to, $subject, $message, 1, $sig_img\n";
  if (! &send_email($from, $to, $subject, $message, 1, $sig_img) ) {
     print "<span style='color: red'>Unable to send request $to</span>";
  }
}

#______________________________________________________________________________

sub add_email_sig_old {
  my $ram = shift @_;
  my $user = shift @_;
  my $display = shift @_;

  if ( $display =~ /Web/i ) {
    $sig_loc   = "../images/TDS_Signature.png";
  }
  else {
    $sig_loc   = "cid:TDS_Signature.png";
  }

  @pcs = split(/\,\s/, $ram);
  $sig_name = "$pcs[1] $pcs[0]";
  $sig_email = $EMAILACCT{$user};
  $sig_title = $EMAIL_SIG_TITLE{$user};
  $sig_ext   = $EMAIL_SIG_EXT{$user};

  my $sig .= "<p>Thank You,</p><table>
                <tr>
                  <td>
                    <img border=0 width=290 height=131 style='width:3.0208in;height:1.3645in' src='$sig_loc' align=left hspace=12>
                  </td>
                  <td width=354 style='width:265.6pt;background:white;padding:0in 6.0pt 0in 6.0pt;height:98.25pt'>
                    <p class=MsoNormal><b><span style='font-size:12.0pt;color:#005E86;text-transform:uppercase'><o:p>&nbsp;</o:p></span></b></p>
                    <p class=MsoNormal><b><span style='font-size:12.0pt;color:#005E86;text-transform:uppercase'>$sig_name</span></b><b><span style='color:#2F5597;text-transform:uppercase'><br></span></b>
                    <b><span style='color:#022234;text-transform:uppercase'>$sig_title<br></span></b>
                    <span style='color:black'><a href='mailto:$sig_email'>$sig_email</a></span><u><span style='color:#005E86'><br>
                    </span></u><b><span style='color:#022234;text-transform:uppercase'>TEL: (888) 255-6526 ext. 118&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <o:p></o:p></span></b></p>
                    <p class=MsoNormal><b><span style='color:#022234;text-transform:uppercase'>TRANSACTION DATA SYSTEMS<br></span></b><span style='color:black'>
                    <a href='rx30.com'><span style='color:#022234'>RX30</span></a></span><span style='color:#022234;text-transform:uppercase'> | </span><span style='color:#022234'><a href='computer-rx.com'><span style='color:#022234'>COMPUTER-RX</span></a><span style='text-transform:uppercase'> | </span><a href='Enhancedmedicationservices.com'><span style='color:#022234'>EMS</span></a> I <u><a href='http://www.pharmassess.com/'><span style='color:#022234'>PHARM ASSESS</span></a></u></span><b><span style='font-size:10.0pt;color:#022234;text-transform:uppercase'><o:p></o:p></span></b></p></td></tr></table><p class=MsoNormal><o:p>&nbsp;</o:p></p><p class=MsoNormal><o:p>&nbsp;</o:p></p>
                  </td>
                </tr>
              </table>";

  return $sig;
}

#______________________________________________________________________________

sub create_intervention {
  my $Pharmacy_ID = shift @_;
  my $acct_mgr    = shift @_;
  my $tpp_id      = shift @_;
  my $check_dates = shift @_;
  my $check_ids   = shift @_;

  chop($check_dates);
  chop($check_ids);

  my $open_date = &build_date();
  my $open_date_TS = &build_date_TS($open_date);
  my ($type_id, $cat, $type, $comments);

  $type     = 'ThirdPartyPayer';
  $type_id  = $tpp_id; 
  $cat      = 'ReconRx - Post Check With No Remit Request';
  $comments = 'ReconRx has requested the 835 file associated with the Post Check with no Remit entry entered on the following dates(s): ' . $check_dates;

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

  if ( $inserted == 1 ) {
     $dbx->do("UPDATE $DBNAME.paymentnoremit SET RequestSent = 1 WHERE id IN ($check_ids)") or die $DBI::errstr;
  }

  $sth->finish();
}
