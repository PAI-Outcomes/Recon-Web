
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

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

$ntitle = "Loyalty Contract";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

print qq#<h2>Please click the button below to receive your new contact via email from DocuSign.</h2>\n#;

print <<"HTML";
<script type="text/javascript" language="javascript" src="/js/upload835.js"></script>
<script type="text/javascript" language="javascript" src="/js/jquery-1.2.6.js"></script>
<style>
/* Center the loader */
#loader {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 1;
  width: 120px;
  height: 120px;
  margin: -76px 0 0 -76px;
  border: 16px solid #f3f3f3;
  border-radius: 50%;
  border-top: 16px solid #3498db;
  -webkit-animation: spin 2s linear infinite;
  animation: spin 2s linear infinite;
}

@-webkit-keyframes spin {
  0% { -webkit-transform: rotate(0deg); }
  100% { -webkit-transform: rotate(360deg); }
}

\@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Add animation to "page content" */
.animate-bottom {
  position: relative;
  -webkit-animation-name: animatebottom;
  -webkit-animation-duration: 1s;
  animation-name: animatebottom;
  animation-duration: 1s
}

\@-webkit-keyframes animatebottom {
  from { bottom:-100px; opacity:0 } 
  to { bottom:0px; opacity:1 }
}

\@keyframes animatebottom { 
  from{ bottom:-100px; opacity:0 } 
  to{ bottom:0; opacity:1 }
}

#myDiv {
  display: none;
  text-align: center;
}
</style>

<script>

function showLoader() {
  document.getElementById("loader").style.display = "block";
}
</script>

HTML

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  if ( $Pharmacy_Arete{$PH_ID} =~ /E/i ) {
    $fee = '112';
    $percent = '10';
  }
  else {
    $fee = '90';
    $percent = '5';
  }

  print qq#<div id="loader" style="display:none;"></div>#;

  print qq#<form method="post" name="sender" action="../Send_Loyalty_Contract.php" id='form1' enctype="multipart/form-data" target="hidden_frame">\n#;
  print qq#<INPUT TYPE="hidden" NAME="PH_ID" ID="PH_ID" VALUE="$PH_ID">\n#;
  print qq#<INPUT id="submit" style="padding:5px; margin:5px; font-size: 14px;" TYPE="Submit" NAME="Submit" VALUE="Loyalty Contract" onClick="showLoader()">\n#;
  print qq#<span id="msg" style="font-weight: bold; font-size: 14px;"></span>\n#;
  print qq#<iframe name='hidden_frame' id="hidden_frame" style='display:none'></iframe>\n#;
  print "</FORM>";

  print "<p>ReconRx would like to express our gratitude for your continued participation in our reconciliation program. Furthermore, we would like to offer you an opportunity to become a <i>Loyalty</i> member and <strong>save ${percent}% on your monthly reconciliation service fee!</strong> As a <i>Loyalty</i> member, your ReconRx service fee will be reduced to only \$$fee per month.</p><p>To take advantage of this offer, simply sign our 2-year contract. All your current features will remain the same. <strong>Please note that this offer expires April 8th, 2022.</strong></p><p>If you do not wish to become a Loyalty member at this time, there will be no changes to your ReconRx account. Your current agreement will remain in place, you will still have access to the complimentary <i>Business Tools (Inventory Management Report, Med Sync Report, and Prescription Savings Program)</i> and you will continue to receive exemplary service.</p>";

  print qq#    </div>\n#;
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

    $ctl_id_sav = $ctl_id;
    $ct_id_sav = $ct_id;
  }

  &update_contact($ctl_id_sav, $ct_id_sav, $set) if ( $rec_data );
}

#______________________________________________________________________________

#______________________________________________________________________________

sub remove_action {
  $sql = "DELETE FROM officedb.pharmacy_action_req
           WHERE Pharmacy_ID = $PH_ID
             AND action = 'Contact Verification'";

#  print "$sql<br><br>";

  $rows = $dbx->do("$sql") or warn $DBI::errstr;
}

