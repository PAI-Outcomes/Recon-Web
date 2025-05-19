#______________________________________________________________________________
#
# Steve Downing 
# Date: 12/12/2017
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

&readsetCookies;

if ( $USER ) {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;
   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

&DisplayForm;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

##############################################
# Subroutines
##############################################

##<script type="text/javascript" language="javascript" src="/js/jquery-1.2.6.js"></script>
sub DisplayForm {


print <<"HTML";
<html>
<script type="text/javascript" language="javascript" src="/js/upload835.js"></script>

<script>
function alertFileType(payer) {
  if ( payer == 'CAMedicaid' ) {
    document.getElementById("alert").innerHTML = '*Only PDF File Format Accepted*';
  }
  else {
    document.getElementById("alert").innerHTML = '';
  }
}

function checkInput() {
  if ( document.getElementById("remit_type").value == '' ) {
    alert("Please Select the Payer");
    return false;
  }
  if ( document.getElementById("file").value == '' ) {
    alert("Please Select a File to Upload");
    return false;
  }

  document.uploaddoc.action= "EOB_upload.cgi?remit_type=" + document.getElementById("remit_type").value;
  return true;
}
</script>
<head>
<title>EOB Converter</title>
<body>
<h2>EOB Converter</h2>
<hr>
<br>

<form method="post" name="uploaddoc" action="EOB_upload.cgi" id='form1' enctype="multipart/form-data" target="hidden_frame">
<!-- <form method="post" action="EOB_upload.cgi" id='form1' enctype="multipart/form-data" target="_blank"> -->
Payer: 

<SELECT NAME="remit_type" ID="remit_type" onChange="alertFileType(this.value)">
<OPTION VALUE="">Select a Payer</OPTION>
<OPTION VALUE="CAMedicaid">California Medicaid</OPTION>
<OPTION VALUE="NYMedicaid">New York Medicaid</OPTION>
<OPTION VALUE="Omnysis">OmnySIS</OPTION>
</SELECT><br><br>

<div id="alert" style="font-weight:bold;"></div>

<p>Enter a file to upload: <input type="file" id='file' name="upfile" style="border: solid .25px" onclick="clear_msg()"/></p>
<input type="submit" name="Submit" value="Upload File" onClick="return checkInput()">&nbsp
<span id="msg"></span>
<iframe name='hidden_frame' id="hidden_frame" style='display:none'></iframe>
</form><br>
<p><i>Disclaimer: Please note that OmnySIS and NY Medicaid claims data will not appear in your ReconRx account. Therefore, ReconRx will not be performing reconciliation or research for these third party payers. However, a remittance detail report will be created for you to review claims listed on the 835 file and adjustments applied. This report can be found in the Reconciled Detail Remittance tab.</i></p>

HTML
}
