
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
$nbsp = "&nbsp;";

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
<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
<script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
<script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>
<!-- <script src="/includes/validate_req.js" type="text/javascript"></script> -->

<script>
\$(function() {
  \$('.phone').mask('(999) 999-9999');
  \$(".datepicker").mask("99/99/9999");
});

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
		var person = prompt("Please enter your full name", "");

		if (person == null || person == "") {
			alert("Your Name is required to proceed");
	                return false;
		} else {
			document.getElementById("submitter").value = person;
                }
	}
}

function q1show(){
  document.getElementById('q1diva').style.display ='block';
  document.getElementById('offyesno').required = true;
}
function q1hide(){
  document.getElementById('q1diva').style.display = 'none';
  document.getElementById('offyesno').required = false;
}
function q2show(){
  document.getElementById('q2diva').style.display ='block';
  document.getElementById('Entity').required = true;
}
function q2hide(){
  document.getElementById('q2diva').style.display = 'none';
  document.getElementById('Entity').required = false;
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


  if ( $in{'Submit'} =~ /Save Changes/i ) {
    &process_input();
    &email_owner();
    &remove_action();
    &update_eofy();
	&update_offer();
    print qq#<h2 style="color: green">Thank You for updating your information!</h2>\n#;
    exit;
  }




$ntitle = "Verify Contacts";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

print qq#<h2>Please update your contact information. Note: Payment Confirmation Contact and Claim Research Contact Information Required</h2>\n#;

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  my @pcs = split('-', $Pharmacy_EOY_Report_Dates{$PH_ID});
  my $eofy = "$pcs[1]/$pcs[2]/$pcs[0]";

  print qq#<!-- displayWebPage -->\n#;

  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return checkRequiredFields(this)\;">\n#;
  print qq#<INPUT TYPE="hidden" NAME="submitter" ID="submitter" "VALUE="">\n#;

  $sql = "SELECT a.id AS pc_id, b.id AS contact_ctl_id, c.name AS ct_name, a.name, a.cellphone, a.phone, a.phone_ext, a.email, a.fax
               FROM officedb.pharmacy_contacts a
               RIGHT JOIN officedb.contact_ctl b ON (a.contact_ctl_id = b.id
               AND a.pharmacy_id = $PH_ID)
               LEFT JOIN officedb.contact_types c ON b.contact_type = c.id	
                WHERE b.contact_owner IN ('ReconRx')
                AND c.display = 1        
           ORDER BY b.contact_owner, c.order";

   ($sqlout = $sql) =~ s/\n/<br>\n/g;

   $sth = $dbx->prepare($sql);
   $sth->execute();

   while ( my ( $contact_id, $ctl_id, $ct_name, $name, $cell, $phone, $phone_ext, $email, $fax ) = $sth->fetchrow_array()) {
     $contact_id = 0 if (! $contact_id );

     if ( $ctl_id =~ /11/ ) {
       $readonly = 'READONLY';
       $warning = "<tr><th colspan=5 style='text-align: center; font-size: 14px; color: red;'>Please notify your ReconRx Account Manager directly if the owner information has changed.</th></tr>";
     }
     else {
       $readonly = '';
       $warning = '';
     }

     if ( $ctl_id =~ /39|40/ ) {
       $required = 'required';
     }
     else {
       $required = '';
     }

     print "<div style='display: block'>
              <table>
                <tr>
                  <th colspan=5 style='text-align: center; font-size: 22px; border-bottom: 2px solid #5FC8ED;'>$ct_name Contact Information</th>
                </tr>
                $warning
                <tr>
                  <th>Name</th>
                  <th><INPUT class='input-text-form $required' TYPE='text' NAME='${ctl_id}_${contact_id}_name' SIZE=30 MAXLENGTH=100 VALUE='$name' $readonly></th>
                  <th>Email Address</th>
                  <th><INPUT class='input-text-form $required' TYPE='email' NAME='${ctl_id}_${contact_id}_email' SIZE=30 MAXLENGTH=100 VALUE='$email' $readonly></th>
                </tr>
                <tr>
                  <th>Phone Number</th>
                  <th><INPUT class='input-text-form phone $required' TYPE='text' NAME='${ctl_id}_${contact_id}_phone' SIZE=15 MAXLENGTH=15 VALUE='$phone' $readonly></th>
                  <th>Ext</th>
                  <th><INPUT class='input-text-form' TYPE='text' NAME='${ctl_id}_${contact_id}_phone_ext' SIZE=8 MAXLENGTH=10 VALUE='$phone_ext' $readonly></th>
                </tr>
                <tr>
                  <th>Fax Number</th>
                  <th><INPUT class='input-text-form phone' TYPE='text' NAME='${ctl_id}_${contact_id}_fax' SIZE=15 MAXLENGTH=15 VALUE='$fax' $readonly></th>
                  <th>Cell Number</th>
                  <th><INPUT class='input-text-form phone' TYPE='text' NAME='${ctl_id}_${contact_id}_cellphone' SIZE=15 MAXLENGTH=15 VALUE='$cell' $readonly></th>
                </tr>
              </table>
            </div><br>";
   }

   $sth->finish;

   print "<div style='display: block'>
            <table>
              <tr>
                <th colspan=5 style='text-align: center; font-size: 22px; border-bottom: 2px solid #5FC8ED;'>End of your current Fiscal Year</th>
              </tr>
              <tr>
                <th><INPUT class='input-text-form datepicker required' TYPE='text' NAME='eofy' ID='EOY' VALUE='<?php echo $eofy; ?>' maxlength='10'></th>
              </tr>
              <tr>
                <th><span style='font-size: 10px; padding-left: 10px'>e.g. MM/DD/YYYY</span></th>
              </tr>
            </table>
			</div>";			
			
   print qq#<div class="q1div" id="q1div" style='display: block'>
       <h1>Do you have an LTC NCPDP that is not in ReconRx? 
	   <input type="radio" id="ltcyesno" name="ltcyesno" value="Yes" onclick="q1show();" required="required"><label for="Yes">Yes</label>
	   <input type="radio" id="ltcyesno" name="ltcyesno" value="No" onclick="q1hide();" ><label for="No">No</label>
	   </h1>       
   </div>#;
   
   print qq#<div class="q1diva" id="q1diva" style='display: none'>
       <h1>ReconRx is currently offering 2 months free for the enrollment of any LTC NCPDP.<BR>Would you like to take advantage of this offer?
	   <input type="radio" id="offyesno" name="offyesno" value="Yes"><label for="Yes">Yes</label>
	   <input type="radio" id="offyesno" name="offyesno" value="No" ><label for="No">No</label>
	   </h1>       
   </div>#;
   
   print qq#<div class="q2div" id="q2div" style='display: block'>
       <h1>Does your pharmacy utilize a billing agency or clearing house to bill medical claims? 
	   <input type="radio" id="billyesno" name="billyesno" value="Yes" onclick="q2show();" required="required"><label for="Yes">Yes</label>
	   <input type="radio" id="billyesno" name="billyesno" value="No" onclick="q2hide();" required="required" ><label for="No">No</label>
	   </h1>       
   </div>#;
   
   print qq#<div class="q2diva" id="q2diva" style='display: none'>
       <h1>What entity does your pharmacy utilize to bill medical claims? 
	   <INPUT class='input-text-form' TYPE='text' NAME='Entity' id="Entity" SIZE=30 MAXLENGTH=100 placeholder="Enter Entity Name" $readonly>
	   </h1>       
   </div>#;

   print qq#<div id="errors"></div>\n#;

   print qq#<INPUT id="submit" style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Save Changes">\n#;
   print "</FORM>";
}

#______________________________________________________________________________

sub process_input {
  my $ctl_id_sav = '';
  my $ct_id_sav = '';
  my $set = '';
  my $rec_data = 0;
  my ($ctl_id, $ct_id, $field);

  foreach $key (sort keys %in) {
    next if ( $key !~ /_/i );

    ($ctl_id, $ct_id, $field)  = split('_', $key, 3);
	
    if ( $ctl_id != $ctl_id_sav && $set ne '') {
       &update_contact($ctl_id_sav, $ct_id_sav, $set) if ( $rec_data );
       $set = '';
       $rec_data = 0;
     }

     if (! $in{$key} ) {
       $in{$key} = 'NULL';
     }
     else {
       $in{$key} = &StripJunk($in{$key});

       $in{$key} = "'$in{$key}'";
       $rec_data++;
     }

    $set .= "$field = $in{$key}, ";
	
	#print "set: $set\n";

     $ctl_id_sav = $ctl_id;
     $ct_id_sav = $ct_id;
  }

  &update_contact($ctl_id_sav, $ct_id_sav, $set) if ( $rec_data );
}

#______________________________________________________________________________

sub update_contact {
  my $ctl_id = shift @_;
  my $ct_id = shift @_;
  my $set = shift @_;

  $set .= "Pharmacy_ID = $PH_ID, contact_ctl_id = $ctl_id";


  if ( $ct_id ) {
    $action = 'UPDATE';
    $where = "WHERE id = $ct_id";
  }
  else {
    $action = 'REPLACE INTO';
    $where = '';
  }

  $sql = "$action officedb.pharmacy_contacts 
              SET $set
           $where";

#  print "$sql<br><br>";

  $rows = $dbx->do("$sql") or warn $DBI::errstr;
}

#______________________________________________________________________________

sub email_owner {
  my $owner_email = '';

  &readCSRs();
  &read_emails();

  $sql = "SELECT a.id AS pc_id, b.id AS contact_ctl_id, c.name AS ct_name, a.name, a.cellphone, a.phone, a.phone_ext, a.email, a.fax
               FROM officedb.pharmacy_contacts a
               RIGHT JOIN officedb.contact_ctl b ON (a.contact_ctl_id = b.id
               AND a.pharmacy_id = $PH_ID)
               LEFT JOIN officedb.contact_types c ON b.contact_type = c.id	
                WHERE b.contact_owner IN ('ReconRx')
                AND c.display = 1        
           ORDER BY b.contact_owner, c.order";

  $sth = $dbx->prepare($sql);
  $sth->execute();

  while ( my ( $contact_id, $ctl_id, $ct_name, $name, $cell, $phone, $phone_ext, $email, $fax ) = $sth->fetchrow_array()) {
    $owner_email = $email if ( $ctl_id == 11 );

    $tbl_data .= "<tr><td class='bd'>$ct_name</td><td class='bd'>$name</td><td class='bd'>$email</td><td class='bd'>$phone</td><td class='bd'>$phone_ext</td><td class='bd'>$fax</td><td class='bd'>$cell</td></tr>";
  }

#  if ( $owner_email ) {
    &generate_email($owner_email, $tbl_data);
#  }

  $sth->finish();
}

#______________________________________________________________________________

sub generate_email {
  my $owner_email = shift @_;
  my $tbl_data    = shift @_;
  my $sig_img     = "D:\\RedeemRx\\CannedFiles\\TDS_Signature.png";
  my $ram         = $Pharmacy_ReconRx_Account_Managers{$PH_ID};

  my @attach = ($sig_img);

  @pcs = split(/@/, $CSR_Emails{$ram});
  $user_email = $pcs[0];
  $from = $user_email;

  my $message = "<style>p.MsoNormal, li.MsoNormal, div.MsoNormal {margin:0in; margin-bottom:.0001pt; font-size:11.0pt; font-family:'Calibri',sans-serif;} table.bd, td.bd, th.bd {
      border: 1px solid black; padding: 5px;}</style>";

  $message .= "<p>Attention,</p><p>Your pharmacy contact information was change by $in{'submitter'}.  Please Review.</p>";
  $message .= "<table class='bd' style='border-collapse: collapse;'><tr><th class='bd'>Contact</th><th class='bd'>Name</th><th class='bd'>Email</th><th class='bd'>Phone</th><th class='bd'>Ext</th><th class='bd'>Fax</th><th class='bd'>cell</th></tr></thead><tbody>";

  $message .= $tbl_data;
  $message .= "</tbody></table>";

  $message .= &add_email_sig($ram, $user_email, 'Email');

  $to = $owner_email;

#  print "TO: $owner_email<br>";

#  $to      = 'bprowell@tdsclinical.com';
#  $to      = 'jkanatzar@tdsclinical.com';
  $to      .= ',bprowell@tdsclinical.com';

  $subject = "Contact Information Changed";

  if (! &send_email($from, $to, $subject, $message, 1, $sig_img) ) {
#     print "<span style='color: red'>Unable to send request $to</span>";
  }
#   else {
#     print "<span style='color: green'>Contacts Updated</span>";
#   }
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
                  <td>
                    <img border=0 width=290 height=131 style='width:3.0208in;height:1.3645in' src='$sig_img' align=left hspace=12>
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

sub remove_action {
  $sql = "DELETE FROM officedb.pharmacy_action_req
           WHERE Pharmacy_ID = $PH_ID
             AND action = 'Contact Verification'";

#  print "$sql<br><br>";

  $rows = $dbx->do("$sql") or warn $DBI::errstr;
}

#______________________________________________________________________________

sub update_eofy {
  my @pcs = split('/', $in{'eofy'});
  my $eofy = $pcs[2] . "-" . $pcs[0] . "-" . $pcs[1];

  $sql = "UPDATE officedb.pharmacy
             SET EOY_Report_Date = '$eofy'
           WHERE Pharmacy_ID = $PH_ID";

#  print "$sql<br><br>";

  $rows = $dbx->do("$sql") or warn $DBI::errstr;
}

sub update_offer {
	$q1a = $in{'offyesno'};
	$q2a = $in{'Entity'};
	
	#print "PH_ID: $PH_ID  q1a: $q1a  q2a: $q2a\n";
	
	$sql = "REPLACE INTO testing.contact_answers
	        VALUES ($PH_ID, '$q1a', '$q2a')";
				
    $rows = $dbx->do("$sql") or warn $DBI::errstr;
}
