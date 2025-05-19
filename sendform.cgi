#!/usr/local/bin/perl

require "D:/RedeemRx/MyData/vars.pl";
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";

use CGI ':standard';
use File::Basename;
use File::Find;

print <<"HEAD";

<!doctype html> 
<html lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<meta name="description" content="ReconRx works for independent pharmacies to provide an efficient and cost effective way to ensure your pharmacy is receiving accurate compensation on all of your third party reimbursements."> 
	<TITLE>ReconRx</TITLE>
	<link type="text/css" rel="stylesheet" media="print" href="/css/print.css" />
	<link type="text/css" rel="stylesheet" media="screen" href="/css/reconrx_style.css" />

<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-37510200-1']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>

</head>

<BODY leftmargin="0" topmargin="0" marginwidth="0" marginheight="0">

<div id="wrapper_home"><!-- wrapper -->

<div id="header_home">
  <div id="recon_graphic" > 
    <img src="/images/header_1024.jpg"><!-- header image -->
  </div><!-- end reconheader -->
  
  <div id="recon_login">
     <FORM ACTION="/cgi-bin/MyReconRx.cgi" METHOD="POST">
        <INPUT TYPE="hidden" NAME="WHICHDB" VALUE="LIVE">
	<table class="main">
	<tr><th align=left class="no_border">User ID</th><td class="no_border"> <INPUT TYPE="text"     NAME="USER" VALUE=""></td></tr>
	<tr><th align=left class="no_border">Password</th><td class="no_border"><INPUT TYPE="PASSWORD" NAME="PASS" VALUE=""></td></tr>
	<tr><th class="no_border">&nbsp;</th><th align=right class="no_border_right"><INPUT TYPE="Submit" VALUE="Log In"></th></tr>
	</table>
     </FORM>
  </div>
</div>

  <!-- content -->
  
  <div id="nav_home">
    <ul>
      <li class="selected"><a href="/index.html">Home</a></li>
	  <li><a href="/reconrx_details.html">Program Details</a></li>
      <li><a href="/reconrx_faqs.html">FAQs</a></li>
      <li><a href="/reconrx_contact.html">Contact Us</a></li>

      <li style="float: right; padding-right: 0px;"><a href="http://www.recon-rx.com/join.html">---- Join a Web Conference! ----</a></li>
    </ul>
  </div><!--end nav-->
  
  <div id="content_container_home">
  
  <div id="mainbody_home">
  
  	<div id="details_home">
	
	<center><a href="http://www.recon-rx.com/WebShare/Docs/ReconRx%20Enrollment.pdf" target="_blank"><img src="/images/enroll_now.png"></a></center>
	
	</div>
HEAD

#for $i (param()) {
#    print "<br /><b>", $i, "</b>: ", param($i), "<br>\n";
#}

print "<br />Thank you for your interest in ReconRx!<br />";
print "<br />We will be in contact with you shortly.<br />";

my $reconinfo_name     = param('reconinfo_name');
my $reconinfo_pharmacy = param('reconinfo_pharmacy');
my $email              = param('email');
my $fax                = param('fax');
my $telephone          = param('telephone');

# $SENDTO  = "josh\@pharmassess.com, tpearson\@pharmassess.com";
  $SENDTO  = "josh\@pharmassess.com";
   
my $from = "NoReplyReconRx";
my $FROM = $EMAILACCT{"$from"};
my $PASS = $EMAILACCTPWD{"$from"};
my $to   = $SENDTO;
  
$subject = "ReconRx Interest from '$reconinfo_pharmacy'\n";

$msg = "ReconRx form filled out by '$reconinfo_name'\n\n";
$msg .= "Contact Name: $reconinfo_name\n\n";
$msg .= "Pharmacy Name: $reconinfo_pharmacy\n\n";
$msg .= "Email: $email\n\n";
$msg .= "Fax: $fax\n\n";
$msg .= "Phone: $telephone\n\n";
     
#print qq#\n<br />sendmessage($from, "$to", $subject, $msg)\n\n#;

print <<"FOOT";

  </div>
  
  </div>
  
  <div id="reconfooter_home"> <!-- start footer --> 

  <a href="mailto:jherder@pharmassess.com?subject=Recon-Rx Web Pages - Powered by textRx" target="_blank">Powered by textRx</a> |
  Click <a href="mailto:jherder@pharmassess.com?subject=Recon-Rx Web Pages - Technical Assistance" target="_blank">here</a> for technical assistance. |
  Copyright 2012. All Rights Reserved.
  
  </div><!-- end reconfooter -->
  
</div><!-- end wrapper -->

</body>
</html>
FOOT

#$debug++;
#$incdebug++;
#$verbose++;

&sendmessage($from, "$to", $subject, $msg);
