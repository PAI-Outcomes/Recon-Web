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

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

#Start page operations
  
if ( $in{submit} =~ /Send/i ) {
  &que_emails();
}

&displayOptions;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
sub displayOptions {
  my $ram_and = '';

  print "<hr>\n";

  print qq#<style> \n#;
  print qq#td { border-top: none; }\n#;
  print qq#</style> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq# function clearSearch(frm) { \n#;
  print qq#     \$("\#ph_id option:selected").removeAttr("selected"); \n#;
  print qq#     \$("\#bin option:selected").removeAttr("selected"); \n#;
  print qq# } \n#;
  print qq# function setFormTarget(target) { \n#;
  print qq#     document.getElementById('selectForm').target = target; \n#;
  print qq# } \n#;
  print qq#</script> \n#;

  print qq#<form id="selectForm" action="$PROG" method="post" >#;
  print "<table>\n";

  print qq#<tr><td><label for="PH_ID">Pharmacy:</label></td>#;
  print qq#<td><label for="TPP_ID">Third Party Payer:</label></td></tr>#;
  print qq#<tr><td><select name="PH_ID" id="ph_id" size="20" multiple style="width:450px;">\n#;

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  &readCSRs();
  $ram = $CSR_Reverse_ID_Lookup{$USER};
  $ram_and = "&& ReconRx_Account_Manager = '$ram'" if($USER != 66);

  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
               FROM officedb.pharmacy 
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
                 $ram_and
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM officedb.pharmacy_coo
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
                 $ram_and
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($PH_ID, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    print qq#<option value="$PH_ID">$NCPDP - $Pharmacy_Name</option>\n#;
  }

  $sthx->finish;
  print qq# </select></td>#;

#  print "SQL: $sql<br>";

  print qq#<td><select name="TPP_ID" id="bin" size="20" multiple style="width:450px;">\n#;

  my $DBNAME = "reconrxdb";
  my $TABLE  = "835auth_frms";

  $sql = "SELECT id, tpp_id, name
            FROM $DBNAME.$TABLE 
           WHERE active = 1
             AND auto = 1
        ORDER BY name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($ID, $TPP_ID, $TPP_NAME) = $sthx->fetchrow_array() ) {
    print qq#<option value="$TPP_ID">$TPP_ID - $TPP_NAME</option>\n#;
  }

  $sthx->finish;
  print qq# </select></td></tr>#;

  print qq#<td><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Preview" onclick="setFormTarget('_blank')"><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Send" onclick="setFormTarget('_self')"><INPUT style="padding:5px; margin:5px" TYPE="button" NAME="Clear" VALUE="Clear" onclick="clearSearch(this.form);"></td><td>$nbsp</td></tr>\n#;

  print qq#</table>\n#;

  print qq#</form>\n#;

  print qq#<br /><hr />\n#;
}

#______________________________________________________________________________

sub que_emails {
  &readCSRs();
  &read_emails();

  my @pharmacies = split(/\0/, $in{'PH_ID'});
  my @tpps = split(/\0/, $in{'TPP_ID'});

  my $TABLE  = '835_request';
  my $email_count = 0;

  foreach $tpp_id (@tpps) {
    $email .= "<tbody><tr>
                 <td colspan=2 class='bd'><p>Attention $ThirdPartyPayer_Names{$tpp_id},</p>
                   <p>Please link the below pharmacy(s) to ReconRx so we may begin receiving 835 files on their behalf.</p>
                   <table><thead><tr><th>Pharmacy Name</th><th>NCPDP</th><th>NPI</th></tr></thead><tbody>";

    foreach $Pharmacy_ID (@pharmacies) {
      $email .= "<tr><td>$Pharmacy_Names{$Pharmacy_ID}</td><td>$Pharmacy_NCPDPs{$Pharmacy_ID}</td><td>$Pharmacy_NPIs{$Pharmacy_ID}</td></tr>";

      $sql = "REPLACE INTO $DBNAME.$TABLE (user, pharmacy_id, tpp_id, request_type) 
              VALUES ($USER, $Pharmacy_ID, '$tpp_id', 'A')";
#      print "SQL: $sql<br>";

      $dbx->do($sql) or warn $DBI::errstr;
    }
    $email_count++;
  }

  print "<br>($email_count) Emails Queued<br>";
}

#______________________________________________________________________________

sub displayPreview {
  print "Content-type: text/html\n\n";

  my $email = qq#<!doctype html> 
                 <html lang="en">
                   <head>
                     <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

                     <TITLE>Preview</TITLE>
   
                   </head>

                   <body leftmargin="0" topmargin="0" marginwidth="0" marginheight="0"> #;

  my $email .= '<h3><strong>Disclaimer: Representation of email only.  Styling may vary from actual email sent.</strong></h3>';

  my $single_ncpdp = '';

  &readPharmacies();
  &readThirdPartyPayers();
  &readCSRs();
  &read_emails();

  my $ram = $CSR_Reverse_ID_Lookup{$USER};
  @pcs = split(/\,\s/, $ram);
  $fl_name = "$pcs[1] $pcs[0]";
  @pcs = split(/@/, $CSR_Emails{$ram});
  $user_email = $pcs[0];

  $sig_name  = $fl_name;
  $sig_email = $EMAILACCT{$user_email};
  $sig_title = $EMAIL_SIG_TITLE{$user_email};
  $sig_ext   = $EMAIL_SIG_EXT{$user_email};
  $sig_img   = "../images/TDS_Signature.png";

  my @pharmacies = split(/\0/, $in{'PH_ID'});
  my @tpps = split(/\0/, $in{'TPP_ID'});

  if ( scalar @pharmacies == 1 ) {
    $single_ncpdp = $Pharmacy_NCPDPs{$pharmacies[0]};
  }

  $email .= "<style>p.MsoNormal, li.MsoNormal, div.MsoNormal {margin:0in; margin-bottom:.0001pt; font-size:11.0pt; font-family:'Calibri',sans-serif;} table.bd {
  border: 1px solid black; margin: 5px; padding: 0px;} td.bd {border-top: 1px solid black;} td.nb {border: 0px solid white;}</style>";

  foreach $tpp_id (@tpps) {
    if ( $TPP_RemittancePrimary_Contact_Emails{$tpp_id} ) {
      $tpp_email = $TPP_RemittancePrimary_Contact_Emails{$tpp_id};
    }
    else {
      $tpp_email = "<div style='color:red'>Remittance Primary Contact Email Not Set</div>";
    }  

    $email .= "<table class='bd'><thead><tr><th align=left>From:</th><th align=left>$sig_email</th></tr>";
    $email .= "<tr><th align=left>To:</th><th align=left>$tpp_email</th></tr>";
    $email .= "<tr><th align=left>Subject:</th><th align=left>ReconRx Action Required: Initial 835 Setup Request $single_ncpdp</th></tr></thead>";

    $email .= "<tbody><tr>
                 <td colspan=2 class='bd'><p>Attention $ThirdPartyPayer_Names{$tpp_id},</p>
                   <p>Please link the below pharmacy(s) to ReconRx so we may begin receiving 835 files on their behalf.</p>
                   <table><thead><tr><th>Pharmacy Name</th><th>NCPDP</th><th>NPI</th></tr></thead><tbody>";

    foreach $Pharmacy_ID (@pharmacies) {
      $email .= "<tr><td class='nb'>$Pharmacy_Names{$Pharmacy_ID}</td><td class='nb'>$Pharmacy_NCPDPs{$Pharmacy_ID}</td><td class='nb'>$Pharmacy_NPIs{$Pharmacy_ID}</td></tr>";
    }

    $email .= "</tbody></table>";

    #### Add Signature
    $email .= "<p>Thank You,</p><table>
                 <tr>
                   <td class='nb'>
                     <img width=232 height=131 style='width:2.4166in;height:1.3645in' src='$sig_img' align=left hspace=12>
                   </td>
                   <td class='nb' width=354 style='width:265.6pt;background:white;padding:0in 6.0pt 0in 6.0pt;height:98.25pt'>
                     <p class=MsoNormal><b><span style='font-size:12.0pt;color:#005E86;text-transform:uppercase'><o:p>&nbsp;</o:p></span></b></p>
                     <p class=MsoNormal><b><span style='font-size:12.0pt;color:#005E86;text-transform:uppercase'>$sig_name</span></b><b><span style='color:#2F5597;text-transform:uppercase'><br></span></b>
                     <b><span style='color:#022234;text-transform:uppercase'>$sig_title<br></span></b>
                     <span style='color:black'><a href='mailto:$sig_email'>$sig_email</a></span><u><span style='color:#005E86'><br>
                     </span></u><b><span style='color:#022234;text-transform:uppercase'>TEL: (888) 255-6526 ext. $sig_ext&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <o:p></o:p></span></b></p>
                     <p class=MsoNormal><b><span style='color:#022234;text-transform:uppercase'>TRANSACTION DATA SYSTEMS<br></span></b><span style='color:black'>
                     <a href='rx30.com'><span style='color:#022234'>RX30</span></a></span><span style='color:#022234;text-transform:uppercase'> | </span><span style='color:#022234'><a href='computer-rx.com'><span style='color:#022234'>COMPUTER-RX</span></a><span style='text-transform:uppercase'> | </span><a href='Enhancedmedicationservices.com'><span style='color:#022234'>EMS</span></a> I <u><a href='http://www.pharmassess.com/'><span style='color:#022234'>PHARM ASSESS</span></a></u></span><b><span style='font-size:10.0pt;color:#022234;text-transform:uppercase'><o:p></o:p></span></b></p></td></tr></table><p class=MsoNormal><o:p>&nbsp;</o:p></p><p class=MsoNormal><o:p>&nbsp;</o:p></p>
                   </td>
                 </tr>
               </table>";

    $email .= "</td></tr></tbody>";
    $email .= "</table><br>";
  }

  print "$email";

  print qq#<INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="submit" VALUE="Close" onclick="self.close()">\n#;
  print "</body></html>";
  exit;
}

