#______________________________________________________________________________
#
# Steve Downing 
# Date: 12/12/2017
# Upload835.cgi
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
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

sub DisplayForm {


print <<"HTML";
<html>
<script type="text/javascript" language="javascript" src="/js/upload835.js"></script>

<script>

function alertFileType(payer) {
  if ( payer == 'AlignRx' ) {
    document.getElementById("alert").innerHTML = '*Only TXT And ZIP File Formats Accepted*';
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

  document.uploaddoc.action= "file_upload835.cgi?remit_type=" + document.getElementById("remit_type").value;
  return true;
}
</script>
<head>
<title>Remittance Upload</title>
<body>
<h2>Remittance Upload</h2>
<hr>
<br>

<form method="post" name="uploaddoc" action="file_upload835.cgi"  enctype="multipart/form-data" target="hidden_frame">


Payer: 

<SELECT NAME="remit_type" ID="remit_type" onChange="alertFileType(this.value)">
<OPTION VALUE="">Select a Payer</OPTION>
<OPTION VALUE="AlignRx">AlignRx</OPTION>
<OPTION VALUE="NYMedicaid">NY Medicaid</OPTION>
<OPTION VALUE="CardinalHealth">Cardinal Health</OPTION>
</SELECT><br><br>

<div id="alert" style="font-weight:bold;"></div>

<p>Enter a file to upload: <input type="file" id='file' name="multi_files" multiple  style="border: solid .25px" onclick="clear_msg()"/></p>
<input type="submit" name="Submit" value="Upload File" onClick="return checkInput()">&nbsp
<span id="msg"></span>
</form><br>
<iframe name='hidden_frame' id="hidden_frame" style='display:none'></iframe>

HTML
}
