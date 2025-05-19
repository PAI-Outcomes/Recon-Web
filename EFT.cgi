require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp\;";

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$SORT    = $in{'SORT'};

$inNPI   = $dispNPI   if ( $dispNPI && !$inNPI );
$inNCPDP = $dispNCPDP if ( $dispNCPDP && !$inNCPDP );

$dispNPI   = $inNPI   if ( $inNPI && !$dispNPI );
$dispNCPDP = $inNCPDP if ( $inNCPDP && !$dispNCPDP );

$dbin     = "TPDBNAME";
$db       = $dbin;
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBTPNDS{"$dbin"};
$FIELDS2  = $DBTPNDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

my $HASH   = $HASHNAMES{$dbin};

#______________________________________________________________________________

&readsetCookies;
&readPharmacies('', '', $inNCPDP);

#______________________________________________________________________________

if ( $USER ) {
  if($Pharmacy_Arete{$PH_ID} =~ /B|E/) { 
   &MyAreteRxHeader;
   &AreteRxHeaderBlock;
  }
  else {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
  }
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&readLogins;
&readContacts;

$FirstName = $LFirstNames{$USER};
$LastName  = $LLastNames{$USER};

$Pharmacy_Name = $Pharmacy_Names{$PH_ID};
$inNCPDP = $Pharmacy_NCPDPs{$PH_ID};

$ntitle = "Generate EFT Paperwork";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayEFT;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayEFT {

  print qq#<!-- displayEFT -->\n#;

  $eft_output = $inNCPDP . '_EFT_Packet.pdf';
  $pdfDownloadDir = "../downloads"; #no trailing slash

#  &eftForm($inNCPDP, $pdfSaveDir, $pdfDownloadDir);

  my $eft_pharmacy_name = $Pharmacy_Names{$inNCPDP} || $Clinic_Names{$inNCPDP};
  
  #Relies on &readPharmacies, &eftPDF
  #Template PDF located in D:/WWW/www.paidesktop.com/docs/EFT/EFT_Master_File.pdf
  
  my ($prog, $dir, $ext) = fileparse($0, '\..*');
  
#  if ($inNCPDP > 0 && $in{'inAuthName'} !~ /^\s*$/) {
  if ( $in{'submit_form'} =~ /Populate/i ) {
    my $sql = "REPLACE 
                  INTO reconrxdb.eft_info (pharmacy_id, auth_name, auth_title, auth_email, auth_phone, auth_fax,
                                           bank_name, bank_contact, bank_phone, bank_street, bank_city,
                                           bank_state, bank_zip, bank_acct_name, bank_rte, bank_acct,
                                           bank_acct_type, eft_type, include_info)
                VALUES ($PH_ID, '" . $in{'inAuthName'} . "', '" . $in{'inAuthTitle'} .  "', '" . $in{'inAuthEmail'} . "', '" . $in{'inAuthPhone'} . "', '" . $in{'inAuthFax'} .  "', '" .
                        $in{'inBankName'} .  "', '" . $in{'inBankContact'} .  "', '" . $in{'inBankPhone'} .  "', '" . $in{'inBankStreet'} .  "', '" . $in{'inBankCity'} .  "', '" .
                        $in{'inBankState'} .  "', '" . $in{'inBankZip'} .  "', '" . $in{'inAcctName'} .  "', '" . $in{'inAcctRouting'} .  "', '" . $in{'inAcctAccount'} .  "', '" .
                        $in{'inAcctType'} .  "', '" . $in{'inAcctEFT'} .  "', '" . $in{'inAcctIncluded'} .  "')";

#     print "SQL: $sql<br>\n";

     $retval = $dbx->do($sql) or die $DBI::errstr;     

     if ( $retval ) {
       # set the php program to run (prefaced with php, prog path and name in quotes)

       $cmd = qq#php D:\\WWW\\members.recon-rx.com\\all_eft_pdf.php PH_ID=$PH_ID#;
#       print "Execute command: $cmd<br>\n";

       system("$cmd");
     }

#    my ($builtPDF, $eft_output) = &eftPDF($pdfSaveDir);
#    if ($builtPDF > 0) {
      print qq#<p>Please follow the instructions in the cover pages of the PDF download in order to submit your form(s) directly to the third party payer(s).</p>\n#;
    
      print qq#<div class="lj_blue" style="margin: 10px 0 10px 0; padding: 10px; width: 350px; text-align: center;"><a href="${pdfDownloadDir}/${eft_output}" download target="_blank"><strong>Download EFT Packet (PDF) for ${eft_pharmacy_name}</strong></a></div>\n#;      
#    }
  } else {
  
    print qq#<p>Complete the following fields and click "Populate EFT Documents" at the bottom of the page. This will build a PDF file to download containing all EFT documents pre-populated with your information, as well as instructions with how to proceed.</p>\n
	#;

    my $Program = 'ReconRx';
    my $Type = 'Authorized';
	
    print qq#<FORM ACTION="${prog}.cgi" METHOD="POST" onSubmit="return checkRequiredFields(this);">\n#;
    
    if ($in{'inAuthName'} =~ /^\s*$/) {
      $in{'inAuthName'} = $Contacts{$PH_ID}{$Program}{$Type}{'Name'};
    }
    if ($in{'inAuthTitle'} =~ /^\s*$/) {
      $in{'inAuthTitle'} = $Contacts{$PH_ID}{$Program}{$Type}{'Title'};
    }
    if ($in{'inAuthEmail'} =~ /^\s*$/) {
      $in{'inAuthEmail'} = $Contacts{$PH_ID}{$Program}{$Type}{'Email'};
    }
    if ($in{'inAuthPhone'} =~ /^\s*$/) {
      $in{'inAuthPhone'} = $Contacts{$PH_ID}{$Program}{$Type}{'Phone'};
    }
    if ($in{'inAuthFax'} =~ /^\s*$/) {
      $in{'inAuthFax'} = $Contacts{$PH_ID}{$Program}{$Type}{'Fax'};
    }
    
    if ($inNCPDP =~ /1111111|2222222/) {
      $in{'inAuthTitle'}   = "Owner";
      
      $in{'inBankName'}    = "First National Bank";
      $in{'inBankPhone'}   = "(913) 555-5555";
      $in{'inBankStreet'}  = "123 N. 3rd St.";
      $in{'inBankCity'}    = "Louisburg";
      $in{'inBankState'}   = "KS";
      $in{'inBankZip'}     = "66053";
      
      $in{'inAcctName'}    = "MY LLC ACCT";
      $in{'inAcctRouting'} = "1234567890";
      $in{'inAcctAccount'} = "980085868";
    }

    print qq#<p><strong>EFT Setup Authorized Signer Information:</strong></p>\n#;
    print qq#<table>\n#;
    print qq#<tr><td>Auth. Signer Name:</td><td><input name="inAuthName"   value="$in{'inAuthName'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Auth. Signer Title:</td><td><input name="inAuthTitle" value="$in{'inAuthTitle'}" class="required" /></td></tr>\n#;
#    if ($in{'inAuthDepartment'} =~ /^\s*$/) { $in{'inAuthDepartment'} = "Accounts Receivables"; }
#    print qq#<tr><td>Department:</td><td><input name="inAuthDepartment" value="$in{'inAuthDepartment'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Email:</td><td><input name="inAuthEmail" value="$in{'inAuthEmail'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Phone:</td><td><input name="inAuthPhone" value="$in{'inAuthPhone'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Fax:</td><td><input name="inAuthFax" value="$in{'inAuthFax'}" class="required" /></td></tr>\n#;
    print qq#</table>\n#;
    print qq#<br /><hr /><br />\n#;

    print qq#<p><strong>Bank Information:</strong></p>\n#;
    print qq#<table>\n#;
    print qq#<tr><td>Bank Name:</td><td><input name="inBankName" value="$in{'inBankName'}" class="required" /></td></tr>\n#;
    if ($in{'inBankContact'} =~ /^\s*$/) { $in{'inBankContact'} = "EFT Setup"; }
    print qq#<tr><td>Bank Contact:</td><td><input name="inBankContact" value="$in{'inBankContact'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Bank Phone:</td><td><input name="inBankPhone" value="$in{'inBankPhone'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Bank Street:</td><td><input name="inBankStreet" value="$in{'inBankStreet'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Bank City:</td><td><input name="inBankCity" value="$in{'inBankCity'}" class="required" /></td></tr>\n#;
    
    print qq#
    <tr>
    <td>Bank State:</td>
    <td><!-- <input name="inBankState" value="$in{'inBankState'}" class="required" /> -->
      <select name="inBankState" size="1" class="required">
        <option value="$in{'inBankState'}">$in{'inBankState'}</option>
        <option value="AK">AK</option>
        <option value="AL">AL</option>
        <option value="AR">AR</option>
        <option value="AZ">AZ</option>
        <option value="CA">CA</option>
        <option value="CO">CO</option>
        <option value="CT">CT</option>
        <option value="DC">DC</option>
        <option value="DE">DE</option>
        <option value="FL">FL</option>
        <option value="GA">GA</option>
        <option value="HI">HI</option>
        <option value="IA">IA</option>
        <option value="ID">ID</option>
        <option value="IL">IL</option>
        <option value="IN">IN</option>
        <option value="KS">KS</option>
        <option value="KY">KY</option>
        <option value="LA">LA</option>
        <option value="MA">MA</option>
        <option value="MD">MD</option>
        <option value="ME">ME</option>
        <option value="MI">MI</option>
        <option value="MN">MN</option>
        <option value="MO">MO</option>
        <option value="MS">MS</option>
        <option value="MT">MT</option>
        <option value="NC">NC</option>
        <option value="ND">ND</option>
        <option value="NE">NE</option>
        <option value="NH">NH</option>
        <option value="NJ">NJ</option>
        <option value="NM">NM</option>
        <option value="NV">NV</option>
        <option value="NY">NY</option>
        <option value="OH">OH</option>
        <option value="OK">OK</option>
        <option value="OR">OR</option>
        <option value="PA">PA</option>
        <option value="PR">PR</option>
        <option value="RI">RI</option>
        <option value="SC">SC</option>
        <option value="SD">SD</option>
        <option value="TN">TN</option>
        <option value="TX">TX</option>
        <option value="UT">UT</option>
        <option value="VA">VA</option>
        <option value="VT">VT</option>
        <option value="WA">WA</option>
        <option value="WI">WI</option>
        <option value="WV">WV</option>
        <option value="WY">WY</option>
      </select>
    </td>
    </tr>
    \n#;
    
    print qq#<tr><td>Bank Zip:</td><td><input name="inBankZip" value="$in{'inBankZip'}" class="required" /></td></tr>\n#;
    print qq#</table>\n#;
    print qq#<br /><hr /><br />\n#;

    print qq#<p><strong>Account Information:</strong></p>\n#;
    print qq#<table>\n#;
    print qq#<tr><td>Name on Bank Account:</td><td><input name="inAcctName" value="$in{'inAcctName'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Routing\#:</td><td><input name="inAcctRouting" value="$in{'inAcctRouting'}" class="required" /></td></tr>\n#;
    print qq#<tr><td>Account\#:</td><td><input name="inAcctAccount" value="$in{'inAcctAccount'}" class="required" /></td></tr>\n#;

    $CHECKED_inAcctType_Checking = '';
    $CHECKED_inAcctType_Savings  = '';
    if ($in{'inAcctType'} =~ /savings/i) {
      $CHECKED_inAcctType_Savings  = 'CHECKED';
    } elsif ($in{'inAcctType'} =~ /checking/i) {
      $CHECKED_inAcctType_Checking = 'CHECKED';
    }
    print qq#<tr><td>Account Type:</td><td>
      <input type="radio" name="inAcctType" value="checking" class="required" $CHECKED_inAcctType_Checking /> Checking &nbsp; <i>or</i> &nbsp; 
      <input type="radio" name="inAcctType" value="savings" $CHECKED_inAcctType_Savings/> Savings 
    </td></tr>\n#;

    print qq#<input type="hidden" name="inAcctPharmType" value="independent" />#;

    $CHECKED_inAcctEFT_New = '';
    $CHECKED_inAcctEFT_Update  = '';
    if ($in{'inAcctEFT'} =~ /update/i) {
      $CHECKED_inAcctEFT_Update  = 'CHECKED';
    } elsif ($in{'inAcctEFT'} =~ /new/i) {
      $CHECKED_inAcctEFT_New = 'CHECKED';
    }
    print qq#<tr><td>EFT Type:</td><td>
      <input type="radio" name="inAcctEFT" value="eft_new" class="required" $CHECKED_inAcctEFT_New /> NEW EFT &nbsp; <i>or</i> &nbsp; 
      <input type="radio" name="inAcctEFT" value="eft_update" $CHECKED_inAcctEFT_Update /> UPDATE to Existing Account 
    </td></tr>\n#;

    $CHECKED_inAcctIncluded_Bank = '';
    $CHECKED_inAcctIncluded_Check  = '';
    if ($in{'inAcctIncluded'} =~ /bank/i) {
      $CHECKED_inAcctIncluded_Bank  = 'CHECKED';
    } elsif ($in{'inAcctIncluded'} =~ /check/i) {
      $CHECKED_inAcctIncluded_Check = 'CHECKED';
    }
    print qq#<tr><td>Included Info:</td><td>
      <input type="radio" name="inAcctIncluded" value="eft_check" class="required" $CHECKED_inAcctIncluded_Check /> Voided Check &nbsp; <i>or</i> &nbsp; 
      <input type="radio" name="inAcctIncluded" value="eft_bank" $CHECKED_inAcctIncluded_Bank /> Bank Letter 
    </td></tr>\n#;

    print qq#</table>\n#;
    print qq#<br /><hr />\n#;
    
    print qq#<p id="errors" style="color: \#F00;"></p>\n#;

    print qq#<br /><INPUT TYPE="Submit" NAME="submit_form" VALUE="Populate Documents" class="button-form">\n#;
    print qq#</FORM>\n#;
    
    print qq#
    <script>
    var checkRequiredFields = function(form) {
      
      var errors = '';
      var error_found = 0;
      
      var checkClass = /(^|\\s)required(\\s|\$)/;  // Field is required
      var checkValue = /^\\s*\$/;                 // Match all whitespace
      
      for(var i=0; i < form.length; i++) {
        
        error_found = 0;
        
        if ( checkClass.test(form[i].className) ) {
          // Required field has no value or only whitespace
          
          if (form[i].type === 'radio') {
            var radios = document.getElementsByName(form[i].name);
            var checked = 0;
            for (var j=0; j < radios.length; j++) {
              if (radios[j].checked) {
                checked += 1;
              }
            }
            if ( checked <= 0 ) {
              error_found = 1;
            }
          } else if (checkValue.test(form[i].value)) {
            error_found = 1;
          }
          
          if (error_found > 0) {
            var name = form[i].name;
            name = name.replace(/^in/g, '');
            name = name.replace(/_/g, ' ');
            name = name.split(/(?=[A-Z])/).join(" ");
            errors += '(' + name + ') \\n';
          }
        }
        
      }
      
      if (errors) {
        errors = 'Please fill out all required fields: \\n' + errors;
        var displayErrorsID = document.getElementById("errors");
        if (displayErrorsID === null) {
          alert(errors);
        } else {
          errors = errors.replace(new RegExp('\\r?\\n','g'), '<br />');
          displayErrorsID.innerHTML = errors;
        }
        return false;
      }
      
    }
    </script>
    #;
  
  }
}

#______________________________________________________________________________
